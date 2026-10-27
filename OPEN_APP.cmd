@echo off
setlocal
cd /d "%~dp0"
title Bridge - Local App Server
if not exist "frontend\dist\index.html" (
  echo Frontend build is missing. Run start.ps1 for setup.
  pause
  exit /b 1
)
set "BRIDGE_PYTHON=C:\Program Files\Python313\python.exe"
if exist ".venv\Scripts\python.exe" set "BRIDGE_PYTHON=%CD%\.venv\Scripts\python.exe"
if not exist "%BRIDGE_PYTHON%" (
  echo Python was not found. Run start.ps1 for setup.
  pause
  exit /b 1
)
echo Keep this window open while using Bridge.
echo Wait for "Application startup complete", then open:
echo http://127.0.0.1:8000/
echo Startup may take a few minutes while live job sources refresh.
"%BRIDGE_PYTHON%" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
 echo.
echo The server stopped. Any error is shown above.
pause
