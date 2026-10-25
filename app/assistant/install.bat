@echo off
cd /d "%~dp0"
echo === Step 1 of 4: Python ===
set PY=
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PY="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if defined PY goto havepy
py -3.11 --version >nul 2>nul
if not errorlevel 1 set PY=py -3.11
if defined PY goto havepy
echo Python not found. Installing automatically, please wait...
winget install -e --id Python.Python.3.11 --scope user --accept-package-agreements --accept-source-agreements
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PY="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if defined PY goto havepy
goto nopython

:havepy
echo === Step 2 of 4: libraries, 5-15 minutes ===
%PY% -m venv venv
if errorlevel 1 goto fail
venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\pip install -r requirements.txt
if errorlevel 1 goto fail
echo === Step 3 of 4: Ollama ===
where ollama >nul 2>nul
if errorlevel 1 if not exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" winget install -e --id Ollama.Ollama --accept-package-agreements --accept-source-agreements
echo === Step 4 of 4: Tesseract OCR, reads the screen ===
if not exist "C:\Program Files\Tesseract-OCR\tesseract.exe" winget install -e --id UB-Mannheim.TesseractOCR --accept-package-agreements --accept-source-agreements
echo.
echo DONE. Now run run.bat
pause
exit /b 0

:nopython
echo.
echo Could not install Python automatically.
echo Close this window and run install.bat once more.
echo If it fails again, take a photo of this window and send it to Claude.
pause
exit /b 1

:fail
echo.
echo Installation error. Take a photo of this window and send it to Claude.
pause
exit /b 1
