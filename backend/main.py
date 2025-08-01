import io
import sqlite3
import uuid

import uvicorn
from client_manager import update_server_config
from database import init_db
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from proxy_creator import create_proxy
from pydantic import BaseModel

app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend"), name="static")
templates = Jinja2Templates(directory="frontend")


class ProxyRequest(BaseModel):
    server_ip: str
    ssh_user: str
    ssh_password: str
    mask_domain: str


class ClientRequest(BaseModel):
    client_email: str


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
    cursor.execute("SELECT id, server_ip, mask_domain FROM servers")
    servers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return JSONResponse(content=servers)


@app.post("/api/proxy")
async def api_create_proxy(proxy_request: ProxyRequest):
    try:
        result = create_proxy(
            proxy_request.server_ip,
            proxy_request.ssh_user,
            proxy_request.ssh_password,
            proxy_request.mask_domain,
        )

        conn = sqlite3.connect("vless_daddy.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO servers (server_ip, ssh_user, ssh_password, mask_domain) VALUES (?, ?, ?, ?)",
            (
                proxy_request.server_ip,
                proxy_request.ssh_user,
                proxy_request.ssh_password,
                proxy_request.mask_domain,
            ),
        )
        server_id = cursor.lastrowid

        client_uuid = result["vless_link"].split("//")[1].split("@")[0]

        cursor.execute(
            "INSERT INTO clients (server_id, uuid, email) VALUES (?, ?, ?)",
            (server_id, client_uuid, "user1"),
        )
        conn.commit()
        conn.close()

        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/servers/{server_id}/clients")
async def get_clients(server_id: int):
    conn = sqlite3.connect("vless_daddy.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, uuid, email FROM clients WHERE server_id = ?", (server_id,)
    )
    clients = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return JSONResponse(content=clients)


@app.post("/api/servers/{server_id}/clients")
async def add_client(server_id: int, client_request: ClientRequest):
    conn = sqlite3.connect("vless_daddy.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    new_uuid = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO clients (server_id, uuid, email) VALUES (?, ?, ?)",
        (server_id, new_uuid, client_request.client_email),
    )
    conn.commit()

    cursor.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
    server = cursor.fetchone()

    cursor.execute("SELECT uuid, email FROM clients WHERE server_id = ?", (server_id,))
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

    cursor.execute("SELECT uuid, email FROM clients WHERE server_id = ?", (server_id,))
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
