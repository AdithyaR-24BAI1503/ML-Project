# ChatBiz — Sprint 5
## Automated Reminders + Voice Input + Recurring Invoices

Implements the documented Sprint 5 deliverables:
- Automated payment reminders
- Voice command transcription
- Recurring invoice support

WhatsApp sending and WhatsApp media permissions are mocked.
Reminder jobs write to a delivery log instead of calling Meta.

## Run
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

For Whisper, install/configure it if you want real local transcription.
The demo also accepts a text transcript so the workflow can be demonstrated without external credentials.
