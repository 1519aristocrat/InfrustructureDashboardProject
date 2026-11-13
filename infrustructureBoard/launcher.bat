
@echo off
title Infrastructure Monitor
cd /d "%~dp0"

echo Starting Infrastructure Monitor...

start "" "%~dp0index.html"

.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000

pause
