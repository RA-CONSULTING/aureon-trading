@echo off
setlocal

set "REPO_ROOT=%~dp0..\.."
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"
set "PYTHON_EXE=%REPO_ROOT%\.venv\Scripts\python.exe"
set "SCRIPT_PATH=%REPO_ROOT%\scripts\python\smoke_test_unified.py"

if not exist "%PYTHON_EXE%" (
  echo Python venv not found: "%PYTHON_EXE%"
  exit /b 1
)

if not exist "%SCRIPT_PATH%" (
  echo Smoke test script not found: "%SCRIPT_PATH%"
  exit /b 1
)

set "PYTHONUNBUFFERED=1"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONPATH=%REPO_ROOT%;%REPO_ROOT%\aureon\core;%REPO_ROOT%\aureon\exchanges;%REPO_ROOT%\aureon\data_feeds;%REPO_ROOT%\aureon\monitors;%PYTHONPATH%"

echo Repo root: "%REPO_ROOT%"
echo Python: "%PYTHON_EXE%"

"%PYTHON_EXE%" "%SCRIPT_PATH%" %*

