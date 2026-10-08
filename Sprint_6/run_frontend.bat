@echo off
title ChatBiz Frontend (Port 3000)
echo ===================================================
echo Starting ChatBiz Standalone Frontend on port 3000...
echo Dashboard: http://127.0.0.1:3000
echo ===================================================
python -m http.server 3000 --directory frontend
pause
