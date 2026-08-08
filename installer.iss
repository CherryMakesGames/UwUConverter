#define MyAppName "UwUConverter"
#define MyAppVersion "0.11"
#define MyAppPublisher "Pink Sakura Studios"

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
Source: "dist\UwUConverter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Run]
Filename: "{app}\UwUConverter.exe"; Parameters: ""; Flags: runhidden waituntilterminated postinstall skipifsilent

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

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    AddCliToPath();
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
    RemoveCliFromPath();
end;
