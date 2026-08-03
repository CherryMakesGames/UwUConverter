#define MyAppName "UwUConverter"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Cherry Leper"
#define MyAppExeName "UwUConverter.exe"

[Setup]
AppId={{7B6F193A-8D9C-42E1-81E8-E9E85C796940}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={localappdata}\Programs\UwUConverter
DefaultGroupName={#MyAppName}

PrivilegesRequired=lowest
OutputDir=installer-output
OutputBaseFilename=UwUConverter-Setup

SetupIconFile=UwUConverter.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "dist\UwUConverter.exe"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Icons]
Name: "{group}\UwUConverter"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\UwUConverter"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Install UwUConverter context menus"; Flags: runhidden waituntilterminated

[UninstallRun]
Filename: "{app}\{#MyAppExeName}"; \
    Parameters: "--uninstall"; \
    Flags: waituntilterminated runhidden skipifdoesntexist; \
    RunOnceId: "RemoveUwUConverterMenus"