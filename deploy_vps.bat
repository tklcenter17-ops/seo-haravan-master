@echo off
chcp 65001 > nul
echo ======================================================
echo    ĐẨY BOT LÊN CLOUD VPS (KHÔNG CẦN BẬT TRÌNH DUYỆT)
echo    VPS IP: 103.166.185.85 - PM2 Process: lamquet-bot
echo ======================================================
echo.

node deploy_to_vps.js

echo.
pause
