from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from .database import init_db
from .nlp import parse_command
from . import client_service

app = FastAPI(title="ChatBiz — Sprint 2", version="2.0")

class Message(BaseModel):
    text: str

@app.on_event("startup")
def startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(open("app/static/index.html", encoding="utf-8").read())

@app.get("/api/clients")
def clients():
    return client_service.list_clients()

@app.post("/api/messages")
def message(body: Message):
    intent = parse_command(body.text)

    if intent.name == "ADD_CLIENT":
        try:
            client = client_service.add_client(intent.name_arg, intent.phone, intent.email)
            return {"intent": intent.name, "message": f"Client {client['name']} added.", "data": client}
        except ValueError as e:
            return {"intent": intent.name, "message": str(e)}

    if intent.name == "LIST_CLIENTS":
        return {"intent": intent.name, "message": "Client list retrieved.", "data": client_service.list_clients()}

    if intent.name == "FIND_CLIENT":
        client = client_service.find_client(intent.name_arg)
        return {"intent": intent.name, "message": "Client found." if client else "Client not found.", "data": client}

    if intent.name == "UPDATE_CLIENT":
        client = client_service.update_client(intent.name_arg, intent.field, intent.value)
        return {"intent": intent.name, "message": "Client updated." if client else "Client not found.", "data": client}

    if intent.name == "DELETE_CLIENT":
        ok = client_service.delete_client(intent.name_arg)
        return {"intent": intent.name, "message": "Client deleted." if ok else "Client not found."}

    return {"intent": "UNKNOWN", "message": "Command not understood."}
