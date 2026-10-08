@echo off
title ChatBiz Backend (Port 8000)
echo ===================================================
echo Starting ChatBiz FastAPI Backend on port 8000...
echo API docs available at: http://127.0.0.1:8000/docs
echo ===================================================
python -m uvicorn app.main:app --port 8000 --reload
pause
