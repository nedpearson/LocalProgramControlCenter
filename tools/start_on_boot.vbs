' Local Nexus Controller - Windows Startup Script
' This script runs silently in the background on Windows startup

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
projectDir = fso.GetParentFolderName(scriptDir)

' Change to project directory and run npm run dev
' The /K keeps the window open, /C would close it after execution
' We use /MIN to minimize the window
WshShell.Run "cmd /C cd /d """ & projectDir & """ && npm run dev", 7, False

' Window style: 0 = Hidden, 1 = Normal, 7 = Minimized
