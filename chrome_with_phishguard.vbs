Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "chrome_with_phishguard.bat" & chr(34), 0
Set WshShell = Nothing
