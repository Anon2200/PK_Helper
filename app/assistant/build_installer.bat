@echo off
cd /d "%~dp0"
if not exist dist\Assistant\Assistant.exe goto nobuild
set ISCC=
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if defined ISCC goto build
echo Installing Inno Setup...
winget install -e --id JRSoftware.InnoSetup --accept-package-agreements --accept-source-agreements
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not defined ISCC goto fail
:build
%ISCC% installer.iss
if errorlevel 1 goto fail
echo.
echo DONE. Installer: installer\VoiceAssistant_Setup.exe
pause
exit /b 0
:nobuild
echo Run build.bat first.
pause
exit /b 1
:fail
echo Could not create installer. Take a photo of this window and send it to Claude.
pause
exit /b 1
