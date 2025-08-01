import base64
import io
import json
import sqlite3
import uuid

import paramiko
import pyqrcode
from proxy_verifier import verify_proxy


def execute_command(ssh_client, command):
    stdin, stdout, stderr = ssh_client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        error_message = stderr.read().decode("utf-8")
        raise Exception(
            f"Command '{command}' failed with exit status {exit_status}: {error_message}"
        )
    return stdout.read().decode("utf-8")


def create_proxy_stream(server_ip, ssh_user, ssh_password, mask_domain, proxy_name):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        yield "status:connect:inprogress"
        ssh_client.connect(hostname=server_ip, username=ssh_user, password=ssh_password)
        yield "status:connect:done"

        yield "status:install:inprogress"
        check_curl_command = "command -v curl >/dev/null 2>&1 || (apt-get update && apt-get install -y curl)"
        execute_command(ssh_client, check_curl_command)
        install_command = 'bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install'
        execute_command(ssh_client, install_command)
        yield "status:install:done"

        yield "status:keys:inprogress"
        generated_uuid = str(uuid.uuid4())
        private_key_output = execute_command(ssh_client, "/usr/local/bin/xray x25519")

        private_key = ""
        public_key = ""
        for line in private_key_output.splitlines():
            if "Private key:" in line:
                private_key = line.split("Private key:")[1].strip()
            if "Public key:" in line:
                public_key = line.split("Public key:")[1].strip()

        if not private_key or not public_key:
            raise Exception("Failed to generate keys")
        yield "status:keys:done"

        yield "status:config:inprogress"
        config = {
            "log": {"loglevel": "info"},
            "inbounds": [
                {
                    "listen": "0.0.0.0",
                    "port": 443,
                    "protocol": "vless",
                    "tag": "reality-in",
                    "settings": {
                        "clients": [
                            {
                                "id": generated_uuid,
                                "email": "user1",
                                "flow": "xtls-rprx-vision",
                            }
                        ],
                        "decryption": "none",
                    },
                    "streamSettings": {
                        "network": "tcp",
                        "security": "reality",
                        "realitySettings": {
                            "show": False,
                            "dest": f"{mask_domain}:443",
                            "xver": 0,
                            "serverNames": [mask_domain],
                            "privateKey": private_key,
                            "minClientVer": "",
                            "maxClientVer": "",
                            "maxTimeDiff": 0,
                            "shortIds": [""],
                        },
                    },
                    "sniffing": {
                        "enabled": True,
                        "destOverride": ["http", "tls", "quic"],
                    },
                }
            ],
            "outbounds": [
                {"protocol": "freedom", "tag": "direct"},
                {"protocol": "blackhole", "tag": "block"},
            ],
            "routing": {
                "rules": [
                    {"type": "field", "protocol": "bittorrent", "outboundTag": "block"}
                ],
                "domainStrategy": "IPIfNonMatch",
            },
        }
        config_str = json.dumps(config, indent=2)

        sftp = ssh_client.open_sftp()
        with sftp.file("/usr/local/etc/xray/config.json", "w") as remote_file:
            remote_file.write(config_str)
        sftp.close()

        execute_command(ssh_client, "systemctl restart xray")
        execute_command(ssh_client, "systemctl status xray")
        yield "status:config:done"

        yield "status:verify:inprogress"
        verified = verify_proxy(server_ip, mask_domain)
        if not verified:
            raise Exception(
                "Proxy verification failed. The server may not be reachable or is misconfigured."
            )
        yield "status:verify:done"

        yield "status:done:inprogress"
        conn = sqlite3.connect("vless_daddy.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO servers (server_ip, ssh_user, ssh_password, mask_domain, public_key, proxy_name) VALUES (?, ?, ?, ?, ?, ?)",
            (server_ip, ssh_user, ssh_password, mask_domain, public_key, proxy_name),
        )
        server_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO clients (server_id, uuid, email) VALUES (?, ?, ?)",
            (server_id, generated_uuid, "user1"),
        )
        conn.commit()
        conn.close()
        yield "status:done:done"

        vless_link = f"vless://{generated_uuid}@{server_ip}:443/?encryption=none&type=tcp&sni={mask_domain}&fp=chrome&security=reality&alpn=h2&flow=xtls-rprx-vision&pbk={public_key}&packetEncoding=xudp#{proxy_name}"

        qr = pyqrcode.create(vless_link)
        buffer = io.BytesIO()
        qr.png(buffer, scale=5)
        qr_code_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        result = {"vless_link": vless_link, "qr_code": qr_code_b64}
        yield f"result:{json.dumps(result)}"

    except Exception as e:
        yield f"error:{str(e)}"
    finally:
        ssh_client.close()
