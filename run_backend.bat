@echo off
echo Starting ChatBiz Unified Backend on http://127.0.0.1:8000 ...
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
if %ERRORLEVEL% NEQ 0 (
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
)
pause
