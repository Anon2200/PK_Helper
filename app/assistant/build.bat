@echo off
cd /d "%~dp0"
echo === Building Assistant.exe, 10-20 minutes. Do not close this window ===
if not exist venv\Scripts\python.exe goto noinstall
venv\Scripts\pip install pyinstaller
if errorlevel 1 goto fail
venv\Scripts\pyinstaller --noconfirm --clean --windowed --name Assistant --icon assets\icon.ico --collect-all faster_whisper --collect-all ctranslate2 --collect-all sounddevice --collect-all onnxruntime --collect-all playwright --collect-submodules pywinauto --hidden-import pyttsx3.drivers --hidden-import pyttsx3.drivers.sapi5 --hidden-import win32com --hidden-import win32crypt --hidden-import comtypes --hidden-import pyscreeze --hidden-import pytweening --hidden-import pymsgbox --hidden-import pytesseract --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtWebEngineWidgets --exclude-module PySide6.QtPdf --exclude-module PySide6.Qt3DCore main.py
if errorlevel 1 goto fail
if exist data xcopy /E /I /Y data dist\Assistant\data >nul
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Assistant.lnk'); $s.TargetPath='%~dp0dist\Assistant\Assistant.exe'; $s.WorkingDirectory='%~dp0dist\Assistant'; $s.Save()"
echo.
echo DONE. Shortcut Assistant is on your Desktop.
echo The program is in folder dist\Assistant  - do not move Assistant.exe out of it.
echo Optional: run build_installer.bat to make a Setup.exe installer.
pause
exit /b 0
:noinstall
echo Run install.bat first.
pause
exit /b 1
:fail
echo.
echo Build error. Take a photo of this window and send it to Claude.
pause
exit /b 1
