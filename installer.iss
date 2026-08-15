#define MyAppName "UwUConverter"
#define MyAppVersion "2.1"
#define MyAppPublisher "Pink Sakura Studios"
#define SevenZipVersion "26.02"
#define SevenZipInstaller "7z2602-x64.exe"
#define SevenZipUrl "https://github.com/ip7z/7zip/releases/download/26.02/7z2602-x64.exe"

[Setup]
AppId={{8D811A80-60D1-49B5-A9D5-1E9E3A54D84A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\UwUConverter
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer-output
OutputBaseFilename=UwUConverter-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ChangesEnvironment=yes
UninstallDisplayIcon={app}\UwUConverter.exe

[Files]
; Main GUI bundle. The updater is excluded here and added explicitly below.
; That makes Inno Setup fail at COMPILE TIME if the updater was not built,
; instead of producing an installer that fails after installation.
Source: "dist\UwUConverter\*"; DestDir: "{app}"; Excludes: "UwUConverterUpdater.exe"; Flags: ignoreversion recursesubdirs createallsubdirs

; PyInstaller builds the updater as a standalone one-file executable here.
; Keeping this source explicit guarantees that UwUConverterUpdater.exe is
; actually embedded in the installer.
Source: "dist\UwUConverterUpdater.exe"; DestDir: "{app}"; DestName: "UwUConverterUpdater.exe"; Flags: ignoreversion


[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "UwUConverterUpdater"; ValueData: """{app}\UwUConverterUpdater.exe"" --auto"; Flags: uninsdeletevalue

[Run]
Filename: "{app}\UwUConverter.exe"; Parameters: ""; Flags: runhidden waituntilterminated postinstall skipifsilent

Filename: "{app}\UwUConverterUpdater.exe"; Parameters: "--auto"; Flags: runhidden nowait postinstall skipifsilent skipifdoesntexist

[UninstallRun]
Filename: "{app}\UwUConverter.exe"; Parameters: "--uninstall"; Flags: runhidden waituntilterminated

[Code]
procedure AddCliToPath();
var
  P, C: String;
begin
  C := ExpandConstant('{app}\cli');
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', P) then
    P := '';

  if Pos(';' + Uppercase(C) + ';', ';' + Uppercase(P) + ';') = 0 then
  begin
    if (P <> '') and (P[Length(P)] <> ';') then
      P := P + ';';
    P := P + C;
    RegWriteExpandStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', P);
  end;
end;

procedure RemoveCliFromPath();
var
  P, C, N, Part, Rest: String;
  SeparatorPos: Integer;
begin
  C := ExpandConstant('{app}\cli');

  if not RegQueryStringValue(
    HKEY_CURRENT_USER,
    'Environment',
    'Path',
    P
  ) then
    exit;

  N := '';
  Rest := P;

  while Rest <> '' do
  begin
    SeparatorPos := Pos(';', Rest);

    if SeparatorPos = 0 then
    begin
      Part := Rest;
      Rest := '';
    end
    else
    begin
      Part := Copy(
        Rest,
        1,
        SeparatorPos - 1
      );

      Delete(
        Rest,
        1,
        SeparatorPos
      );
    end;

    if (Part <> '') and
       (CompareText(Part, C) <> 0) then
    begin
      if N <> '' then
        N := N + ';';

      N := N + Part;
    end;
  end;

  RegWriteExpandStringValue(
    HKEY_CURRENT_USER,
    'Environment',
    'Path',
    N
  );
end;

function SevenZipInstalled(): Boolean;
begin
  Result :=
    FileExists(
      ExpandConstant('{autopf}\7-Zip\7z.exe')
    ) or
    FileExists(
      ExpandConstant('{autopf32}\7-Zip\7z.exe')
    );
end;

procedure EnsureSevenZipInstalled();
var
  InstallerPath: String;
  ResultCode: Integer;
begin
  if SevenZipInstalled() then
  begin
    Log('7-Zip already installed; skipping download.');
    exit;
  end;

  try
    Log('7-Zip not found. Downloading 7-Zip ' + '{#SevenZipVersion}' + '...');

    DownloadTemporaryFile(
      '{#SevenZipUrl}',
      '{#SevenZipInstaller}',
      '',
      nil
    );

    InstallerPath :=
      ExpandConstant('{tmp}\{#SevenZipInstaller}');

    if not FileExists(InstallerPath) then
    begin
      Log('Downloaded 7-Zip installer was not found.');
      MsgBox(
        'UwUConverter was installed, but the downloaded 7-Zip installer could not be found.'
        + #13#10
        + 'Archive commands will not work until 7-Zip is installed.',
        mbInformation,
        MB_OK
      );
      exit;
    end;

    Log('Launching 7-Zip installer.');

    if not ShellExec(
      'runas',
      InstallerPath,
      '/S',
      '',
      SW_SHOWNORMAL,
      ewWaitUntilTerminated,
      ResultCode
    ) then
    begin
      Log('Could not launch 7-Zip installer.');
      exit;
    end;

    if ResultCode <> 0 then
      Log(
        '7-Zip installer returned exit code '
        + IntToStr(ResultCode)
      )
    else
      Log('7-Zip installation completed.');

  except
    Log(
      '7-Zip automatic installation failed: '
      + GetExceptionMessage
    );

    MsgBox(
      'UwUConverter was installed, but 7-Zip could not be installed automatically.'
      + #13#10
      + 'Archive commands will not work until 7-Zip is installed.',
      mbInformation,
      MB_OK
    );
  end;
end;


procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    AddCliToPath();
    EnsureSevenZipInstalled();
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
    RemoveCliFromPath();
end;
