@echo off
title CyberShield AI public link

curl -s -o nul http://127.0.0.1:8080/api/stats
if errorlevel 1 (
    echo CyberShield AI is not running. Run START-CYBERSHIELD.bat first, then run this file again.
    pause
    exit /b 1
)

echo Creating a public link. Look for the address ending in trycloudflare.com below.
echo Keep this window open. Closing it turns the link off.
"C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:8080
pause
