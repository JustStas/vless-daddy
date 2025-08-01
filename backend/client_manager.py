import json
import uuid

import paramiko


def update_server_config(server_ip, ssh_user, ssh_password, clients):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=server_ip, username=ssh_user, password=ssh_password)
        sftp = ssh_client.open_sftp()

        # Read existing config
        with sftp.file("/usr/local/etc/xray/config.json", "r") as remote_file:
            config = json.load(remote_file)

        # Update clients
        config["inbounds"][0]["settings"]["clients"] = [
            {
                "id": client["uuid"],
                "username": client["username"],
                "flow": "xtls-rprx-vision",
            }
            for client in clients
        ]

        # Write new config
        config_str = json.dumps(config, indent=2)
        with sftp.file("/usr/local/etc/xray/config.json", "w") as remote_file:
            remote_file.write(config_str)

        sftp.close()

        # Restart Xray
        stdin, stdout, stderr = ssh_client.exec_command("systemctl restart xray")
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            raise Exception(f"Failed to restart Xray: {stderr.read().decode('utf-8')}")

    finally:
        ssh_client.close()
