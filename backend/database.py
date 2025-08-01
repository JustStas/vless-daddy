import sqlite3


def init_db():
    conn = sqlite3.connect("vless_daddy.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY,
            server_ip TEXT NOT NULL,
            ssh_user TEXT NOT NULL,
            ssh_password TEXT NOT NULL,
            mask_domain TEXT NOT NULL,
            public_key TEXT NOT NULL,
            proxy_name TEXT NOT NULL
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY,
            server_id INTEGER NOT NULL,
            uuid TEXT NOT NULL,
            username TEXT NOT NULL,
            FOREIGN KEY (server_id) REFERENCES servers (id)
        )
    """
    )
    conn.commit()
    conn.close()
