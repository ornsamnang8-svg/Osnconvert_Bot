Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\85596\.antigravity-ide\Link2Media"
WshShell.Run "cmd /c set PYTHONPATH=. && .venv\Scripts\python.exe -m link2media.main", 0, False
