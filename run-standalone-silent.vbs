' Run No Homers Club standalone without showing a console window.
' Double-click this file instead of run-standalone.bat.
Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "cmd /c run-standalone.bat", 0, False
