@echo off

python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in system PATH.
    exit /b 1
)

python "%~dp0CGen.py" %*
