# ChatBiz — Sprint 2
## NLP Command Parsing + Client Management

Implements the Sprint 2 deliverables:
- Natural-language command parsing
- Add/list/find/update/delete clients
- SQLite database
- FastAPI REST API
- Simple demo web UI

WhatsApp Business permissions are intentionally not required.
`POST /api/messages` simulates incoming WhatsApp text.

### Example commands
- `add client Rahul, 9876543210, rahul@gmail.com`
- `list clients`
- `find client Rahul`
- `update client Rahul phone 9999999999`
- `delete client Rahul`

### Run
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 or http://127.0.0.1:8000/docs
