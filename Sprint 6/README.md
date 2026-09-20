# ChatBiz — Sprint 6
## Analytics + Dashboard + Testing + Deployment

Implements the documented Sprint 6 deliverables:
- Analytics engine
- Web dashboard
- CSV export
- Automated API tests
- Docker deployment files

WhatsApp remains mocked; external API permissions are not required.

## Run locally
pip install -r requirements.txt
uvicorn app.main:app --reload

Open http://127.0.0.1:8000

## Docker
docker build -t chatbiz-sprint6 .
docker run -p 8000:8000 chatbiz-sprint6

## Test
pytest -q
