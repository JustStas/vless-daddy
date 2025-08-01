import base64
import io
import sqlite3
import uuid
from typing import Optional

import pyqrcode
import uvicorn
from client_manager import update_server_config
from database import init_db
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from proxy_creator import create_proxy_stream
from pydantic import BaseModel, Field

app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend"), name="static")
templates = Jinja2Templates(directory="frontend")


class ProxyRequest(BaseModel):
    server_ip: str
    ssh_user: str
    ssh_password: str
    mask_domain: str
    proxy_name: str
    overwrite: Optional[bool] = Field(default=False)


class ClientRequest(BaseModel):
    client_username: str


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/management", response_class=HTMLResponse)
async def read_management(request: Request):
    return templates.TemplateResponse("management.html", {"request": request})


@app.get("/clients", response_class=HTMLResponse)
async def read_clients(request: Request):
    return templates.TemplateResponse("clients.html", {"request": request})


@app.get("/api/servers")
async def get_servers():
    conn = sqlite3.connect("vless_daddy.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, server_ip, mask_domain, proxy_name FROM servers")
    servers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return JSONResponse(content=servers)


@app.post("/api/proxy")
async def api_create_proxy(proxy_request: ProxyRequest):
    return StreamingResponse(
        create_proxy_stream(
            proxy_request.server_ip,
            proxy_request.ssh_user,
            proxy_request.ssh_password,
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

    new_uuid = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO clients (server_id, uuid, username) VALUES (?, ?, ?)",
        (server_id, new_uuid, client_request.client_username),
    )
    conn.commit()

    cursor.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
    server = cursor.fetchone()

    cursor.execute(
        "SELECT uuid, username FROM clients WHERE server_id = ?", (server_id,)
    )
    clients = cursor.fetchall()

    conn.close()

    update_server_config(
        server["server_ip"],
        server["ssh_user"],
        server["ssh_password"],
        [dict(client) for client in clients],
    )

    return {"message": "Client added successfully"}


@app.delete("/api/servers/{server_id}/clients/{client_id}")
async def delete_client(server_id: int, client_id: int):
    conn = sqlite3.connect("vless_daddy.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM clients WHERE id = ? AND server_id = ?", (client_id, server_id)
    )
    conn.commit()

    cursor.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
    server = cursor.fetchone()

    cursor.execute(
        "SELECT uuid, username FROM clients WHERE server_id = ?", (server_id,)
    )
    clients = cursor.fetchall()

    conn.close()

    if server:
        update_server_config(
            server["server_ip"],
            server["ssh_user"],
            server["ssh_password"],
            [dict(client) for client in clients],
        )

    return {"message": "Client deleted successfully"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
