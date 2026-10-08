Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Starting ChatBiz Standalone Frontend on port 3000..." -ForegroundColor Green
Write-Host "Dashboard URL: http://127.0.0.1:3000" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan

$host.UI.RawUI.WindowTitle = "ChatBiz Frontend (Port 3000)"
python -m http.server 3000 --directory frontend
