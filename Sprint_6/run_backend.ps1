Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Starting ChatBiz FastAPI Backend on port 8000..." -ForegroundColor Green
Write-Host "API Swagger Docs: http://127.0.0.1:8000/docs" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan

$host.UI.RawUI.WindowTitle = "ChatBiz Backend (Port 8000)"
python -m uvicorn app.main:app --port 8000 --reload
