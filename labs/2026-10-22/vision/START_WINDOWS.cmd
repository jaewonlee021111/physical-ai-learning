@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto dependencies
where py >nul 2>nul
if errorlevel 1 (
  python -m venv .venv
) else (
  py -3 -m venv .venv
)
if errorlevel 1 goto failed
:dependencies
.venv\Scripts\python.exe -m pip install -r requirements-yolo.txt platformio
if errorlevel 1 goto failed
echo Camera must be free in Zoom before you continue.
.venv\Scripts\python.exe pc_check.py --camera 0 --yolo
if errorlevel 1 goto failed
echo Opening the local dashboard at http://127.0.0.1:5050
start "" http://127.0.0.1:5050
.venv\Scripts\python.exe step8_pipeline_dashboard.py --source camera
goto end
:failed
echo Setup or hardware check failed. Keep this message for diagnosis.
:end
pause
