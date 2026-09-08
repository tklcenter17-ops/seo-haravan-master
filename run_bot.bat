@echo off
chcp 65001 > nul
title LamQuetVault Telegram Bot
cd /d "%~dp0"
echo ========================================================
echo   KHỞI ĐỘNG TRỢ LÝ QUẸT TELEGRAM (@LamQuetVault_bot)
echo ========================================================
echo.

:: Vòng lặp tự động phục hồi nếu có sự cố rớt mạng
:loop
python bot.py
echo.
echo [CẢNH BÁO] Bot vừa dừng. Đang tự động khởi động lại sau 5 giây...
timeout /t 5 /nobreak > nul
goto loop
