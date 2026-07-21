@echo off
REM Start backend server (Windows batch). Run from project root.
SET SCRIPT_DIR=%~dp0
SET VENV_PYTHON=%SCRIPT_DIR%backend\.venv\Scripts\python.exe

REM Use venv python if available, otherwise use system python
IF EXIST "%VENV_PYTHON%" (
    SET PYTHON_CMD="%VENV_PYTHON%"
) ELSE (
    SET PYTHON_CMD=python
)

REM Check if port 9000 is in use, fallback to 9001
%PYTHON_CMD% -c "import socket; s=socket.socket(); s.settimeout(3); r=s.connect_ex(('127.0.0.1', 9000)); s.close(); exit(r)" 2>nul
IF %ERRORLEVEL% EQU 0 (
    echo Port 9000 is in use. Starting on port 9001 instead.
    set PORT=9001
) ELSE (
    set PORT=9000
)

REM Run uvicorn from project root so `backend` package imports work
%PYTHON_CMD% -m uvicorn backend.main:app --host 0.0.0.0 --port %PORT% --reload

