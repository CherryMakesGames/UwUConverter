#define MyAppName "UwUConverter"
#define MyAppVersion "2.3"
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
Source: "dist\UwUConverter\*"; DestDir: "{app}"; Excludes: "UwUConverterUpdater.exe,UwUConverterBrowserHost.exe"; Flags: ignoreversion recursesubdirs createallsubdirs

; PyInstaller builds the updater as a standalone one-file executable here.
; Keeping this source explicit guarantees that UwUConverterUpdater.exe is
; actually embedded in the installer.
Source: "dist\UwUConverterUpdater.exe"; DestDir: "{app}"; DestName: "UwUConverterUpdater.exe"; Flags: ignoreversion

; Native messaging host used by the Firefox/Chromium browser extension.
; Keeping this explicit makes installer compilation fail if CI forgot to
; build the browser host.
Source: "dist-browser-host\UwUConverterBrowserHost.exe"; DestDir: "{app}"; DestName: "UwUConverterBrowserHost.exe"; Flags: ignoreversion



[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "UwUConverterUpdater"; ValueData: """{app}\UwUConverterUpdater.exe"" --auto"; Flags: uninsdeletevalue

[Run]
Filename: "{app}\UwUConverter.exe"; Parameters: ""; Flags: runhidden waituntilterminated postinstall skipifsilent


Filename: "{app}\UwUConverterUpdater.exe"; Parameters: "--auto"; Flags: runhidden nowait postinstall skipifsilent skipifdoesntexist

[UninstallRun]
Filename: "{app}\UwUConverter.exe"; Parameters: "--uninstall"; Flags: runhidden waituntilterminated

[Code]
var
  BrowserPage: TInputOptionWizardPage;
  ChromeIndex: Integer;
  ChromiumIndex: Integer;
  EdgeIndex: Integer;
  OperaIndex: Integer;
  OperaGXIndex: Integer;
  BraveIndex: Integer;
  VivaldiIndex: Integer;
  FirefoxIndex: Integer;
  BrowserQuestionsAlreadyShown: Boolean;

function FirstExistingFile(Candidate1, Candidate2, Candidate3, Candidate4: String): String;
begin
  Result := '';
  if (Candidate1 <> '') and FileExists(Candidate1) then begin Result := Candidate1; exit; end;
  if (Candidate2 <> '') and FileExists(Candidate2) then begin Result := Candidate2; exit; end;
  if (Candidate3 <> '') and FileExists(Candidate3) then begin Result := Candidate3; exit; end;
  if (Candidate4 <> '') and FileExists(Candidate4) then Result := Candidate4;
end;

function FindChrome(): String;
begin
  Result := FirstExistingFile(
    ExpandConstant('{autopf}\Google\Chrome\Application\chrome.exe'),
    ExpandConstant('{autopf32}\Google\Chrome\Application\chrome.exe'),
    ExpandConstant('{localappdata}\Google\Chrome\Application\chrome.exe'), '');
end;

function FindChromium(): String;
begin
  Result := FirstExistingFile(
    ExpandConstant('{autopf}\Chromium\Application\chrome.exe'),
    ExpandConstant('{autopf32}\Chromium\Application\chrome.exe'),
    ExpandConstant('{localappdata}\Chromium\Application\chrome.exe'), '');
end;

function FindEdge(): String;
begin
  Result := FirstExistingFile(
    ExpandConstant('{autopf}\Microsoft\Edge\Application\msedge.exe'),
    ExpandConstant('{autopf32}\Microsoft\Edge\Application\msedge.exe'),
    ExpandConstant('{localappdata}\Microsoft\Edge\Application\msedge.exe'), '');
end;

function FindOpera(): String;
begin
  Result := FirstExistingFile(
    ExpandConstant('{localappdata}\Programs\Opera\opera.exe'),
    ExpandConstant('{localappdata}\Programs\Opera\launcher.exe'),
    ExpandConstant('{autopf}\Opera\opera.exe'),
    ExpandConstant('{autopf32}\Opera\opera.exe'));
end;

function FindOperaGX(): String;
begin
  Result := FirstExistingFile(
    ExpandConstant('{localappdata}\Programs\Opera GX\opera.exe'),
    ExpandConstant('{localappdata}\Programs\Opera GX\launcher.exe'),
    ExpandConstant('{autopf}\Opera GX\opera.exe'),
    ExpandConstant('{autopf32}\Opera GX\opera.exe'));
end;

function FindBrave(): String;
begin
  Result := FirstExistingFile(
    ExpandConstant('{autopf}\BraveSoftware\Brave-Browser\Application\brave.exe'),
    ExpandConstant('{autopf32}\BraveSoftware\Brave-Browser\Application\brave.exe'),
    ExpandConstant('{localappdata}\BraveSoftware\Brave-Browser\Application\brave.exe'), '');
end;

function FindVivaldi(): String;
begin
  Result := FirstExistingFile(
    ExpandConstant('{localappdata}\Vivaldi\Application\vivaldi.exe'),
    ExpandConstant('{autopf}\Vivaldi\Application\vivaldi.exe'),
    ExpandConstant('{autopf32}\Vivaldi\Application\vivaldi.exe'), '');
end;

function FindFirefox(): String;
begin
  Result := FirstExistingFile(
    ExpandConstant('{autopf}\Mozilla Firefox\firefox.exe'),
    ExpandConstant('{autopf32}\Mozilla Firefox\firefox.exe'),
    ExpandConstant('{localappdata}\Mozilla Firefox\firefox.exe'), '');
end;

procedure AddDetectedBrowser(BrowserName, ExecutablePath: String; var BrowserIndex: Integer);
begin
  BrowserIndex := -1;
  if ExecutablePath <> '' then
  begin
    BrowserIndex := BrowserPage.CheckListBox.Items.Count;
    BrowserPage.Add(BrowserName);
    BrowserPage.Values[BrowserIndex] := True;
  end;
end;

procedure InitializeWizard();
var
  BrowserSetupValue: Cardinal;
begin
  ChromeIndex := -1;
  ChromiumIndex := -1;
  EdgeIndex := -1;
  OperaIndex := -1;
  OperaGXIndex := -1;
  BraveIndex := -1;
  VivaldiIndex := -1;
  FirefoxIndex := -1;
  BrowserQuestionsAlreadyShown := False;

  if RegQueryDWordValue(
    HKEY_CURRENT_USER,
    'Software\Pink Sakura Studios\UwUConverter',
    'BrowserQuestionsShown',
    BrowserSetupValue
  ) then
    BrowserQuestionsAlreadyShown := BrowserSetupValue <> 0;

  BrowserPage := CreateInputOptionPage(
    wpSelectTasks,
    'Browser integration',
    'Install the UwUConverter browser extension',
    'Select the browsers where you want UwUConverter available. After installation, '
    + 'Setup opens the selected extension pages and the bundled extension folder. '
    + 'Until store publishing, use Load unpacked, or Load Temporary Add-on in Firefox.',
    False,
    False
  );

  AddDetectedBrowser('Google Chrome', FindChrome(), ChromeIndex);
  AddDetectedBrowser('Chromium', FindChromium(), ChromiumIndex);
  AddDetectedBrowser('Microsoft Edge', FindEdge(), EdgeIndex);
  AddDetectedBrowser('Opera', FindOpera(), OperaIndex);
  AddDetectedBrowser('Opera GX', FindOperaGX(), OperaGXIndex);
  AddDetectedBrowser('Brave', FindBrave(), BraveIndex);
  AddDetectedBrowser('Vivaldi', FindVivaldi(), VivaldiIndex);
  AddDetectedBrowser('Firefox', FindFirefox(), FirefoxIndex);
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  if PageID = BrowserPage.ID then
    Result := BrowserQuestionsAlreadyShown or (BrowserPage.CheckListBox.Items.Count = 0);
end;

function BrowserSelected(BrowserIndex: Integer): Boolean;
begin
  Result := (BrowserIndex >= 0) and BrowserPage.Values[BrowserIndex];
end;

procedure LaunchBrowser(ExecutablePath, TargetUrl: String);
var
  ResultCode: Integer;
begin
  if ExecutablePath = '' then exit;
  if not ShellExec('', ExecutablePath, '"' + TargetUrl + '"', '', SW_SHOWNORMAL, ewNoWait, ResultCode) then
    Log('Could not open browser extension page: ' + ExecutablePath);
end;

procedure OpenFolder(FolderPath: String);
var
  ResultCode: Integer;
begin
  if not DirExists(FolderPath) then exit;
  ShellExec('', FolderPath, '', '', SW_SHOWNORMAL, ewNoWait, ResultCode);
end;

procedure LaunchSelectedBrowserExtensions();
var
  ChromiumFolderOpened: Boolean;
begin
  if BrowserQuestionsAlreadyShown then exit;
  ChromiumFolderOpened := False;

  if BrowserSelected(ChromeIndex) then begin
    LaunchBrowser(FindChrome(), 'chrome://extensions');
    if not ChromiumFolderOpened then begin OpenFolder(ExpandConstant('{app}\browser-extension\chromium')); ChromiumFolderOpened := True; end;
  end;

  if BrowserSelected(ChromiumIndex) then begin
    LaunchBrowser(FindChromium(), 'chrome://extensions');
    if not ChromiumFolderOpened then begin OpenFolder(ExpandConstant('{app}\browser-extension\chromium')); ChromiumFolderOpened := True; end;
  end;

  if BrowserSelected(EdgeIndex) then begin
    LaunchBrowser(FindEdge(), 'edge://extensions');
    if not ChromiumFolderOpened then begin OpenFolder(ExpandConstant('{app}\browser-extension\chromium')); ChromiumFolderOpened := True; end;
  end;

  if BrowserSelected(OperaIndex) then begin
    LaunchBrowser(FindOpera(), 'opera://extensions');
    if not ChromiumFolderOpened then begin OpenFolder(ExpandConstant('{app}\browser-extension\chromium')); ChromiumFolderOpened := True; end;
  end;

  if BrowserSelected(OperaGXIndex) then begin
    LaunchBrowser(FindOperaGX(), 'opera://extensions');
    if not ChromiumFolderOpened then begin OpenFolder(ExpandConstant('{app}\browser-extension\chromium')); ChromiumFolderOpened := True; end;
  end;

  if BrowserSelected(BraveIndex) then begin
    LaunchBrowser(FindBrave(), 'brave://extensions');
    if not ChromiumFolderOpened then begin OpenFolder(ExpandConstant('{app}\browser-extension\chromium')); ChromiumFolderOpened := True; end;
  end;

  if BrowserSelected(VivaldiIndex) then begin
    LaunchBrowser(FindVivaldi(), 'vivaldi://extensions');
    if not ChromiumFolderOpened then begin OpenFolder(ExpandConstant('{app}\browser-extension\chromium')); ChromiumFolderOpened := True; end;
  end;

  if BrowserSelected(FirefoxIndex) then begin
    LaunchBrowser(FindFirefox(), 'about:debugging#/runtime/this-firefox');
    OpenFolder(ExpandConstant('{app}\browser-extension\firefox'));
  end;

  RegWriteDWordValue(
    HKEY_CURRENT_USER,
    'Software\Pink Sakura Studios\UwUConverter',
    'BrowserQuestionsShown',
    1
  );
end;

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


function IsWindows11OrLater(): Boolean;
var
  Version: TWindowsVersion;
begin
  GetWindowsVersionEx(Version);
  Result :=
    (Version.Major > 10) or
    ((Version.Major = 10) and (Version.Build >= 22000));
end;

procedure RegisterModernShell();
var
  PowerShellPath: String;
  ScriptPath: String;
  LogPath: String;
  Parameters: String;
  ResultCode: Integer;
begin
  if not IsWindows11OrLater() then
    exit;

  ScriptPath := ExpandConstant(
    '{app}\modern-shell\register_shell.ps1'
  );

  if not FileExists(ScriptPath) then
  begin
    Log('Modern shell registration script was not installed.');
    exit;
  end;

  LogPath := ExpandConstant(
    '{app}\modern-shell\registration.log'
  );

  SaveStringToFile(
    LogPath,
    'UwUConverter modern shell registration started by Setup.' + #13#10,
    False
  );

  PowerShellPath := ExpandConstant(
    '{sys}\WindowsPowerShell\v1.0\powershell.exe'
  );

  Parameters :=
    '-NoLogo -NoProfile -NonInteractive -WindowStyle Hidden '
    + '-ExecutionPolicy Bypass -File "' + ScriptPath + '" '
    + '-InstallDir "' + ExpandConstant('{app}') + '"';

  if (not Exec(
    PowerShellPath,
    Parameters,
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  )) or (ResultCode <> 0) then
  begin
    Log(
      'Windows 11 modern context-menu registration failed with exit code '
      + IntToStr(ResultCode)
    );

    MsgBox(
      'UwUConverter was installed, but the Windows 11 modern context menu '
      + 'could not be registered.' + #13#10 + #13#10
      + 'PowerShell exit code: ' + IntToStr(ResultCode)
      + #13#10 + #13#10
      + 'Registration details were saved to:' + #13#10
      + LogPath
      + #13#10 + #13#10
      + 'The classic Show more options menu will still work.',
      mbInformation,
      MB_OK
    );
  end;
end;

procedure UnregisterModernShell();
var
  PowerShellPath: String;
  ScriptPath: String;
  Parameters: String;
  ResultCode: Integer;
begin
  if not IsWindows11OrLater() then
    exit;

  ScriptPath := ExpandConstant(
    '{app}\modern-shell\unregister_shell.ps1'
  );

  if not FileExists(ScriptPath) then
    exit;

  PowerShellPath := ExpandConstant(
    '{sys}\WindowsPowerShell\v1.0\powershell.exe'
  );

  Parameters :=
    '-NoLogo -NoProfile -NonInteractive -WindowStyle Hidden '
    + '-ExecutionPolicy Bypass -File "' + ScriptPath + '" '
    + '-InstallDir "' + ExpandConstant('{app}') + '"';

  if (not Exec(
    PowerShellPath,
    Parameters,
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  )) or (ResultCode <> 0) then
    Log(
      'Windows 11 modern context-menu unregistration returned exit code '
      + IntToStr(ResultCode)
    );
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    AddCliToPath();
    EnsureSevenZipInstalled();
    RegisterModernShell();
    LaunchSelectedBrowserExtensions();
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    UnregisterModernShell();
    RemoveCliFromPath();
  end;
end;
