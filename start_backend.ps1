#!/usr/bin/env pwsh
# Start backend server (PowerShell). Run this from the project root.
$venvPython = Join-Path -Path $PSScriptRoot -ChildPath 'backend\.venv\Scripts\python.exe'

# Use venv python if available, otherwise use system python
if (Test-Path $venvPython) {
    $pythonCmd = $venvPython
} else {
    $pythonCmd = 'python'
}

# Check if port 9000 is in use, fallback to 9001
$port = 9000
$check = & $pythonCmd -c "import socket; s=socket.socket(); s.settimeout(3); r=s.connect_ex(('127.0.0.1', 9000)); s.close(); exit(r)" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Port 9000 is in use. Starting on port 9001 instead."
    $port = 9001
}

# Run uvicorn from project root so `backend` package imports work
Write-Host "Starting server on http://localhost:$port ..."
& $pythonCmd -m uvicorn backend.main:app --host 0.0.0.0 --port $port --reload