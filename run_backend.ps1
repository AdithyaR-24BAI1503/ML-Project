Write-Host "Starting ChatBiz Unified Backend on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
if (Get-Command py -ErrorAction SilentlyContinue) {
    py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
} else {
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
}
