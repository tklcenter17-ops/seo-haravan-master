' Khởi động Bot chạy ngầm hoàn toàn (Không hiện cửa sổ CMD)
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
ScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

WshShell.CurrentDirectory = ScriptDir
' 0 = Ẩn cửa sổ hoàn toàn, False = Không chờ tiến trình kết thúc
WshShell.Run "pythonw bot.py", 0, False
