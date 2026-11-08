@echo off
cd /d "%~dp0"
if not exist .venv (py -m venv .venv)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if "%ADMIN_PASSWORD%"=="" set /p ADMIN_PASSWORD=Enter admin password (not shown in site): 
if "%SECRET_KEY%"=="" set SECRET_KEY=local-coursework-secret-change-for-real-deployment
python server.py
pause
