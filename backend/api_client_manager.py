import json
import uuid

import paramiko


def add_user_via_api(server_ip, ssh_user, ssh_password, ssh_port, username):
    """
    Add a user to the Xray server using the API instead of config file modification.
    Returns the generated UUID.
    """
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Generate new UUID
        new_uuid = str(uuid.uuid4())

        # Connect to server
        ssh_client.connect(
            hostname=server_ip, username=ssh_user, password=ssh_password, port=ssh_port
        )

        # Create user JSON for the API (format based on GitHub PR #4943)
        # The adu command expects full inbound configuration structure
        user_config = {
            "inbounds": [
                {
                    "tag": "reality-in",
                    "protocol": "vless",
                    "listen": "0.0.0.0",
                    "port": 443,
                    "settings": {
                        "decryption": "none",
                        "clients": [
                            {
                                "id": new_uuid,
                                "email": username,
                                "flow": "xtls-rprx-vision",
                            }
                        ],
                    },
                }
            ]
        }

        # Create temporary file with user config on the server
        remote_temp_path = f"/tmp/user_{new_uuid}.json"
        config_json = json.dumps(user_config, indent=2)

        # Write config to remote file
        sftp = ssh_client.open_sftp()
        with sftp.file(remote_temp_path, "w") as remote_file:
            remote_file.write(config_json)
        sftp.close()

        try:
            # Add user via Xray API
            cmd = f"/usr/local/bin/xray api adu --server=127.0.0.1:8081 {remote_temp_path}"
            stdin, stdout, stderr = ssh_client.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()

            if exit_status != 0:
                stdout_content = stdout.read().decode("utf-8")
                stderr_content = stderr.read().decode("utf-8")
                raise Exception(
                    f"Xray API command failed (exit code {exit_status}): {stderr_content}"
                )

            return new_uuid

        finally:
            # Clean up remote temp file
            ssh_client.exec_command(f"rm {remote_temp_path}")

    except Exception as e:
        print(f"ERROR in add_user_via_api for user '{username}': {str(e)}")
        raise
    finally:
        ssh_client.close()


def remove_user_via_api(server_ip, ssh_user, ssh_password, ssh_port, username):
    """
    Remove a user from the Xray server using the API.
    """
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to server
        ssh_client.connect(
            hostname=server_ip, username=ssh_user, password=ssh_password, port=ssh_port
        )

        # Remove user via Xray API
        cmd = f"/usr/local/bin/xray api rmu --server=127.0.0.1:8081 -tag=reality-in {username}"
        stdin, stdout, stderr = ssh_client.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()

        if exit_status != 0:
            error_msg = stderr.read().decode("utf-8")
            raise Exception(f"Failed to remove user via API: {error_msg}")

    finally:
        ssh_client.close()


def list_users_via_api(server_ip, ssh_user, ssh_password, ssh_port):
    """
    List all users from the Xray server using the API.
    Returns a list of user info dictionaries.
    """
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to server
        ssh_client.connect(
            hostname=server_ip, username=ssh_user, password=ssh_password, port=ssh_port
        )

        # Get all users via Xray API
        cmd = f"/usr/local/bin/xray api inbounduser --server=127.0.0.1:8081 -tag=reality-in"
        stdin, stdout, stderr = ssh_client.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()

        if exit_status != 0:
            error_msg = stderr.read().decode("utf-8")
            raise Exception(f"Failed to list users via API: {error_msg}")

        output = stdout.read().decode("utf-8").strip()

        # Parse the output (format may vary, we'll need to test this)
        users = []
        if output:
            try:
                # Try to parse as JSON first
                users_data = json.loads(output)
                if isinstance(users_data, list):
                    users = users_data
                elif isinstance(users_data, dict) and "users" in users_data:
                    users = users_data["users"]
            except json.JSONDecodeError:
                # If not JSON, try to parse line by line
                # This will need adjustment based on actual API output format
                pass

        return users

    finally:
        ssh_client.close()


def get_user_info_via_api(server_ip, ssh_user, ssh_password, ssh_port, username):
    """
    Get specific user info from the Xray server using the API.
    Returns user info dictionary or None if not found.
    """
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to server
        ssh_client.connect(
            hostname=server_ip, username=ssh_user, password=ssh_password, port=ssh_port
        )

        # Get specific user via Xray API
        cmd = f"/usr/local/bin/xray api inbounduser --server=127.0.0.1:8081 -tag=reality-in -email={username}"
        stdin, stdout, stderr = ssh_client.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()

        if exit_status != 0:
            error_msg = stderr.read().decode("utf-8")
            # User not found is not necessarily an error
            if "not found" in error_msg.lower():
                return None
            raise Exception(f"Failed to get user info via API: {error_msg}")

        output = stdout.read().decode("utf-8").strip()

        if output:
            try:
                user_info = json.loads(output)
                return user_info
            except json.JSONDecodeError:
                # Handle non-JSON output format if needed
                pass

        return None

    finally:
        ssh_client.close()
