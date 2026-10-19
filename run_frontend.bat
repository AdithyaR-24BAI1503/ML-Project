@echo off
echo Starting ChatBiz Minimal Frontend on http://127.0.0.1:3000 ...
py -m http.server 3000 --directory frontend
if %ERRORLEVEL% NEQ 0 (
    python -m http.server 3000 --directory frontend
)
pause
