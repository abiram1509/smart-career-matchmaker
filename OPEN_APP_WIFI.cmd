@echo off
setlocal
cd /d "%~dp0"
title Bridge - Wi-Fi App Server
set "BRIDGE_PYTHON=C:\Program Files\Python313\python.exe"
if exist ".venv\Scripts\python.exe" set "BRIDGE_PYTHON=%CD%\.venv\Scripts\python.exe"
echo Keep this window open. Wait for Application startup complete.
echo Other devices: use this computer's current Wi-Fi IPv4 address with :8000.
echo Do not also run OPEN_APP.cmd while this server is running.
"%BRIDGE_PYTHON%" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
pause
