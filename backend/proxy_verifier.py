import socket
import ssl
import time


def verify_proxy(server_ip, mask_domain):
    """
    Verifies that the proxy is responding by attempting a TLS handshake.
    This simulates a client connecting and ensures the XTLS-Reality setup is working.
    """
    try:
        # A short delay to allow the xray service to fully restart.
        time.sleep(3)

        context = ssl.create_default_context()
        # We don't need to validate the certificate itself, just that the handshake completes.
        # Xray will be using a self-signed cert for the REALITY protocol.
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Attempt to connect to the server on the standard HTTPS port.
        # The 'server_hostname' argument sets the SNI, which is critical for XTLS-Reality.
        with socket.create_connection((server_ip, 443), timeout=15) as sock:
            with context.wrap_socket(sock, server_hostname=mask_domain) as ssock:
                # If the handshake completes without an error, the test is successful.
                print(
                    f"Proxy verification successful. Connected to {server_ip} with SNI '{mask_domain}'."
                )
                return True
    except (ssl.SSLError, socket.timeout, ConnectionRefusedError, OSError) as e:
        print(f"Proxy verification failed: {e}")
        return False
    return False
