@echo off
chcp 65001 > nul
title LamQuet Radar Telegram Bot (@LamQuet_Radar_bot)
cd /d "%~dp0"
echo ========================================================
echo   TRỢ LÝ QUẸT TELEGRAM (@LamQuet_Radar_bot)
echo ========================================================
echo.
echo [CHÚ Ý] Bot đã được thiết lập chạy 24/7 trên VPS 103.166.185.85.
echo Nếu bạn chạy thêm trên máy tính này, Telegram sẽ báo lỗi xung đột kép (Conflict)
echo và chặn phản hồi tin nhắn.
echo.
echo Nhấn Ctrl+C để hủy nếu bot đang chạy trên VPS.
echo Hoặc nhấn phím bất kỳ nếu bạn chắc chắn muốn chạy local:
pause > nul
echo.

:: Vòng lặp tự động phục hồi nếu có sự cố rớt mạng
:loop
python bot.py
echo.
echo [CẢNH BÁO] Bot vừa dừng. Đang tự động khởi động lại sau 5 giây...
timeout /t 5 /nobreak > nul
goto loop
