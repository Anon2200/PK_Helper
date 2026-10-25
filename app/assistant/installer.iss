; Установщик (Inno Setup). Собирается командой build_installer.bat
[Setup]
AppName=Voice Assistant
AppVersion=1.0
DefaultDirName={autopf}\VoiceAssistant
DefaultGroupName=Voice Assistant
OutputDir=installer
OutputBaseFilename=VoiceAssistant_Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
SetupIconFile=assets\icon.ico
[Files]
Source: "dist\Assistant\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs
[Icons]
Name: "{group}\Voice Assistant"; Filename: "{app}\Assistant.exe"
Name: "{autodesktop}\Voice Assistant"; Filename: "{app}\Assistant.exe"
[Run]
Filename: "{app}\Assistant.exe"; Description: "Запустить"; Flags: nowait postinstall skipifsilent
