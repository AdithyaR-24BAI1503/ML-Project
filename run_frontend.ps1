Write-Host "Starting ChatBiz Minimal Frontend on http://127.0.0.1:3000 ..." -ForegroundColor Cyan
if (Get-Command py -ErrorAction SilentlyContinue) {
    py -m http.server 3000 --directory frontend
} else {
    python -m http.server 3000 --directory frontend
}
