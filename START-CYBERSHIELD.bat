@echo off
title CyberShield AI
cd /d "%~dp0"

echo Starting CyberShield AI...

for /d %%i in ("C:\Program Files\Eclipse Adoptium\jdk-21*") do set "JAVA=%%i\bin\java.exe"

if not exist "%JAVA%" (
    echo Java 21 was not found. Install it, then run this file again.
    pause
    exit /b 1
)

sc query postgresql-17 | find "RUNNING" >nul
if errorlevel 1 (
    echo PostgreSQL is not running. Start the postgresql-17 service, then run this file again.
    pause
    exit /b 1
)

start "CyberShield ML service - keep open" /d "%~dp0ml-service" cmd /k ".venv\Scripts\python.exe app.py"
start "CyberShield server - keep open" /d "%~dp0backend" cmd /k ""%JAVA%" "-Djdk.net.unixdomain.tmpdir=%PUBLIC%" -jar target\backend-1.0.0.jar"

echo Waiting for the server to start...
set /a tries=0

:wait
ping -n 3 127.0.0.1 >nul
curl -s -o nul http://127.0.0.1:8080/api/stats
if not errorlevel 1 goto ready

set /a tries+=1
if %tries% lss 45 goto wait

echo The server did not start. Check the two other windows for an error message.
pause
exit /b 1

:ready
start "" http://127.0.0.1:8080
echo CyberShield AI is running at http://127.0.0.1:8080
echo Keep the two other windows open. Close them to stop the project.
pause
