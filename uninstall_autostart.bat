@echo off
chcp 65001 > nul
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\LamQuetBot.lnk"

if exist "%SHORTCUT%" (
    del "%SHORTCUT%"
    echo [ĐÃ HỦY] Đã xóa bot khỏi danh sách tự khởi động cùng Windows.
) else (
    echo Bot chưa được cài đặt tự khởi động.
)

pause
