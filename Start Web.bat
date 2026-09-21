@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
echo.
echo Opening Historical Dialectics Studio in your browser...
echo Keep this window open while you use the app.
echo.
start "" http://127.0.0.1:7860
".venv\Scripts\python.exe" -m dialectics_studio.web
pause
