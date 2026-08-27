' Silent one-click launcher: no terminal window, only a Windows notification for real updates.
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
folder = files.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = folder
command = """" & folder & "\.venv\Scripts\python.exe"" """ & folder & "\main.py"" --toast"
shell.Run command, 0, False
