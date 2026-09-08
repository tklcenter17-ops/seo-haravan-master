@echo off
chcp 65001 > nul
echo ========================================================
echo   CÀI ĐẶT TỰ ĐỘNG CHẠY BOT CÙNG WINDOWS (AUTO-START)
echo ========================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "TARGET=%SCRIPT_DIR%start_bot_silent.vbs"
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\LamQuetBot.lnk"

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = 'wscript.exe'; $s.Arguments = '\"%TARGET%\"'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.Save()"

if exist "%SHORTCUT%" (
    echo [THÀNH CÔNG] Đã đăng ký bot tự động chạy ngầm cùng Windows!
    echo Mỗi khi anh bật máy tính, bot sẽ tự động chạy ngầm mà không cần mở bất kỳ cửa sổ nào.
    echo.
) else (
    echo [THẤT BẠI] Không thể tạo shortcut khởi động.
)

pause
