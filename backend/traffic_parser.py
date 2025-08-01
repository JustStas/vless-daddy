import json
import sqlite3
from collections import defaultdict

import paramiko

DB_PATH = "vless_daddy.db"
API_SERVER = "127.0.0.1:8081"
XRAY_BIN = "/usr/local/bin/xray"


def _run_stat(ssh_client: paramiko.SSHClient, name: str, reset: bool = False) -> int:
    """Run `xray api stats` for a single counter name and return the integer value.

    If the counter isn't found Xray returns an error on stderr – treat that as 0.
    """
    reset_flag = "-reset=true" if reset else "-reset=false"
    # Wrap the name in single quotes so shell passes it literally.
    cmd = f"{XRAY_BIN} api stats --server={API_SERVER} -name '{name}' {reset_flag}"
    stdin, stdout, stderr = ssh_client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()

    if exit_status != 0:
        # Counter not found or other error ⇒ 0 bytes.
        error_msg = stderr.read().decode("utf-8").strip()
        print(f"Counter '{name}' error: {error_msg}")
        return 0

    # Successful call returns JSON:  {"stat": {"name": "...", "value": 123}}
    try:
        output = stdout.read().decode("utf-8").strip()
        print(f"Counter '{name}' output: '{output}'")

        data = json.loads(output)
        return int(data["stat"]["value"])
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        print(f"Failed to parse counter '{name}' output: '{output}', error: {e}")
        return 0


def _get_usernames_for_server(server_ip: str) -> list[str]:
    """Return list of client usernames for the given server_ip from the local DB."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM servers WHERE server_ip = ?", (server_ip,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return []
    server_id = row[0]
    cursor.execute("SELECT username FROM clients WHERE server_id = ?", (server_id,))
    usernames = [r[0] for r in cursor.fetchall()]
    conn.close()
    return usernames


def get_traffic_usage(server_ip: str, ssh_user: str, ssh_password: str) -> dict:
    """Return a dict { username: { 'up': int, 'down': int } } for the given server."""
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    traffic_data = defaultdict(lambda: {"up": 0, "down": 0})
    usernames = _get_usernames_for_server(server_ip)
    if not usernames:
        return {}

    try:
        ssh_client.connect(hostname=server_ip, username=ssh_user, password=ssh_password)

        for username in usernames:
            for direction in ("uplink", "downlink"):
                counter = f"user>>>{username}>>>traffic>>>{direction}"
                value = _run_stat(ssh_client, counter, reset=False)
                if direction == "uplink":
                    traffic_data[username]["up"] += value
                else:
                    traffic_data[username]["down"] += value

        return traffic_data
    finally:
        ssh_client.close()


def reset_traffic_usage(server_ip: str, ssh_user: str, ssh_password: str) -> bool:
    """Reset all user traffic counters to zero. Returns True on success."""
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    usernames = _get_usernames_for_server(server_ip)
    if not usernames:
        return False

    try:
        ssh_client.connect(hostname=server_ip, username=ssh_user, password=ssh_password)
        success = True
        for username in usernames:
            for direction in ("uplink", "downlink"):
                counter = f"user>>>{username}>>>traffic>>>{direction}"
                _ = _run_stat(ssh_client, counter, reset=True)
        return success
    finally:
        ssh_client.close()
