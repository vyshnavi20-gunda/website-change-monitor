' Used by Task Scheduler. It keeps the project folder as the working directory
' so the scheduled run writes to this project's data\monitor.db.
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
folder = files.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = folder
command = """" & folder & "\.venv\Scripts\python.exe"" """ & folder & "\main.py"" --toast"
shell.Run command, 0, False
