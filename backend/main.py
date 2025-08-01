import base64
import io
import sqlite3
import uuid
from typing import Optional

import paramiko
import pyqrcode
import uvicorn
from api_client_manager import add_user_via_api, remove_user_via_api
from database import init_db
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from proxy_creator import create_proxy_stream
from pydantic import BaseModel, Field
from traffic_parser import get_traffic_usage

app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")
templates = Jinja2Templates(directory="frontend/build")


class ProxyRequest(BaseModel):
    server_ip: str
    ssh_user: str
    ssh_password: str
    ssh_port: int = 22
    mask_domain: str
    proxy_name: str
    overwrite: Optional[bool] = Field(default=False)


class ClientRequest(BaseModel):
    client_username: str


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/api/servers")
async def get_servers():
    conn = sqlite3.connect("vless_daddy.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, server_ip, mask_domain, proxy_name FROM servers")
    servers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return JSONResponse(content=servers)


@app.get("/api/servers/{server_id}")
async def get_server_details(server_id: int):
    conn = sqlite3.connect("vless_daddy.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, proxy_name FROM servers WHERE id = ?",
        (server_id,),
    )
    server = cursor.fetchone()
    conn.close()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return JSONResponse(content=dict(server))


@app.delete("/api/servers/{server_id}")
async def delete_server(server_id: int, cleanup: bool = False):
    conn = sqlite3.connect("vless_daddy.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if cleanup:
        cursor.execute(
            "SELECT server_ip, ssh_user, ssh_password FROM servers WHERE id = ?",
            (server_id,),
        )
        server = cursor.fetchone()
        if server:
            try:
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(
                    hostname=server["server_ip"],
                    username=server["ssh_user"],
                    password=server["ssh_password"],
                )
                cleanup_command = "systemctl stop xray; rm -f /usr/local/etc/xray/config.json; rm -rf /var/log/xray"
                stdin, stdout, stderr = ssh_client.exec_command(cleanup_command)
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    # Log error but proceed with DB deletion
                    print(
                        f"Server cleanup failed for {server['server_ip']}: {stderr.read().decode('utf-8')}"
                    )
                ssh_client.close()
            except Exception as e:
                print(
                    f"SSH connection failed during cleanup for {server['server_ip']}: {e}"
                )

    # Delete from database
    cursor.execute("DELETE FROM clients WHERE server_id = ?", (server_id,))
    cursor.execute("DELETE FROM servers WHERE id = ?", (server_id,))
    conn.commit()
    conn.close()
    return {"message": "Server deleted successfully"}


@app.post("/api/proxy")
async def api_create_proxy(proxy_request: ProxyRequest):
    return StreamingResponse(
        create_proxy_stream(
            proxy_request.server_ip,
            proxy_request.ssh_user,
            proxy_request.ssh_password,
            proxy_request.ssh_port,
            proxy_request.mask_domain,
            proxy_request.proxy_name,
            proxy_request.overwrite,
        ),
        media_type="text/event-stream",
    )


@app.get("/api/servers/{server_id}/clients")
async def get_clients(server_id: int):
    conn = sqlite3.connect("vless_daddy.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, uuid, username FROM clients WHERE server_id = ?", (server_id,)
    )
    clients = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return JSONResponse(content=clients)


@app.get("/api/clients/{client_id}")
async def get_client_details(client_id: int):
    conn = sqlite3.connect("vless_daddy.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT c.uuid, s.server_ip, s.mask_domain, s.public_key, s.proxy_name
        FROM clients c
        JOIN servers s ON c.server_id = s.id
        WHERE c.id = ?
    """,
        (client_id,),
    )
    data = cursor.fetchone()
    conn.close()

    if not data:
        raise HTTPException(status_code=404, detail="Client not found")

    vless_link = f"vless://{data['uuid']}@{data['server_ip']}:443/?encryption=none&type=tcp&sni={data['mask_domain']}&fp=chrome&security=reality&alpn=h2&flow=xtls-rprx-vision&pbk={data['public_key']}&packetEncoding=xudp#{data['proxy_name']}"

    qr = pyqrcode.create(vless_link)
    buffer = io.BytesIO()
    qr.png(buffer, scale=5)
    qr_code_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return JSONResponse(
        content={"uuid": data["uuid"], "vless_link": vless_link, "qr_code": qr_code_b64}
    )


@app.post("/api/servers/{server_id}/clients")
async def add_client(server_id: int, client_request: ClientRequest):
    conn = sqlite3.connect("vless_daddy.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get server details
    cursor.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
    server = cursor.fetchone()

    if not server:
        conn.close()
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        # Add user via Xray API and get the generated UUID
        new_uuid = add_user_via_api(
            server["server_ip"],
            server["ssh_user"],
            server["ssh_password"],
            server["ssh_port"],
            client_request.client_username,
        )

        # Store in local database
        cursor.execute(
            "INSERT INTO clients (server_id, uuid, username) VALUES (?, ?, ?)",
            (server_id, new_uuid, client_request.client_username),
        )
        conn.commit()
        conn.close()

        return {"message": "Client added successfully", "uuid": new_uuid}

    except Exception as e:
        print(
            f"ERROR: Failed to add client '{client_request.client_username}': {str(e)}"
        )
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to add client: {str(e)}")


@app.delete("/api/servers/{server_id}/clients/{client_id}")
async def delete_client(server_id: int, client_id: int):
    conn = sqlite3.connect("vless_daddy.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get client details before deletion
    cursor.execute(
        "SELECT username FROM clients WHERE id = ? AND server_id = ?",
        (client_id, server_id),
    )
    client = cursor.fetchone()

    if not client:
        conn.close()
        raise HTTPException(status_code=404, detail="Client not found")

    # Get server details
    cursor.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
    server = cursor.fetchone()

    if not server:
        conn.close()
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        # Remove user via Xray API
        remove_user_via_api(
            server["server_ip"],
            server["ssh_user"],
            server["ssh_password"],
            server["ssh_port"],
            client["username"],
        )

        # Remove from local database
        cursor.execute(
            "DELETE FROM clients WHERE id = ? AND server_id = ?", (client_id, server_id)
        )
        conn.commit()
        conn.close()

        return {"message": "Client deleted successfully"}

    except Exception as e:
        conn.close()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete client: {str(e)}"
        )


@app.get("/api/servers/{server_id}/traffic")
async def get_server_traffic(server_id: int):
    conn = sqlite3.connect("vless_daddy.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT server_ip, ssh_user, ssh_password, ssh_port FROM servers WHERE id = ?",
        (server_id,),
    )
    server = cursor.fetchone()
    conn.close()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    traffic_data = get_traffic_usage(
        server["server_ip"],
        server["ssh_user"],
        server["ssh_password"],
        server["ssh_port"],
    )
    return JSONResponse(content=traffic_data)


@app.get("/api/servers/{server_id}/debug_traffic")
async def get_debug_traffic(server_id: int):
    conn = sqlite3.connect("vless_daddy.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT server_ip, ssh_user, ssh_password, ssh_port FROM servers WHERE id = ?",
        (server_id,),
    )
    server = cursor.fetchone()
    conn.close()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    traffic_data = get_traffic_usage(
        server["server_ip"],
        server["ssh_user"],
        server["ssh_password"],
        server["ssh_port"],
    )
    return JSONResponse(content=traffic_data)


# Serve React App
@app.get("/{full_path:path}")
async def serve_react_app(request: Request, full_path: str):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
