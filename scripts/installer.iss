#ifndef PayloadRoot
  #define PayloadRoot "dist\\inno_payload"
#endif

#ifndef OutputDir
  #define OutputDir "dist\\inno_output"
#endif

#ifndef AppVersion
  #define AppVersion "dev"
#endif

#ifndef OutputBaseFilename
  #define OutputBaseFilename "EDMCModernOverlay-setup"
#endif

#ifndef InstallVenvMode
  #define InstallVenvMode "embedded"
#endif

[Setup]
AppId=EDMCModernOverlay
AppName=EDMC Modern Overlay
AppVersion={#AppVersion}
AppPublisher=EDMC Modern Overlay
DefaultDirName={code:GetDefaultPluginDir}
DisableDirPage=no
UsePreviousAppDir=yes
DisableReadyMemo=yes
DisableProgramGroupPage=yes
DirExistsWarning=no
OutputDir={#OutputDir}
OutputBaseFilename={#OutputBaseFilename}
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=no
Uninstallable=no

[Tasks]
Name: "font"; Description: "Install Eurocaps font (you confirm you have a license to use this font)"; Flags: unchecked

[Files]
; Plugin payload
Source: "{#PayloadRoot}\EDMCModernOverlay\*"; DestDir: "{app}\EDMCModernOverlay"; Flags: ignoreversion recursesubdirs
; Preserve user settings and fonts if they already exist
Source: "{#PayloadRoot}\EDMCModernOverlay\overlay_groupings.user.json"; DestDir: "{app}\EDMCModernOverlay"; Flags: ignoreversion external skipifsourcedoesntexist
Source: "{#PayloadRoot}\EDMCModernOverlay\overlay_settings.json"; DestDir: "{app}\EDMCModernOverlay"; Flags: ignoreversion external skipifsourcedoesntexist
Source: "{#PayloadRoot}\EDMCModernOverlay\overlay_client\fonts\*"; DestDir: "{app}\EDMCModernOverlay\overlay_client\fonts"; Flags: ignoreversion recursesubdirs external skipifsourcedoesntexist
; Bundled assets staged to temp
Source: "{#PayloadRoot}\tools\generate_checksums.py"; DestDir: "{tmp}\tools"; Flags: ignoreversion deleteafterinstall
Source: "{#PayloadRoot}\tools\release_excludes.json"; DestDir: "{tmp}\tools"; Flags: ignoreversion deleteafterinstall
Source: "{#PayloadRoot}\checksums_payload.txt"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall
Source: "{#PayloadRoot}\extras\EUROCAPS.ttf"; DestDir: "{app}\EDMCModernOverlay\overlay_client\fonts"; DestName: "Eurocaps.ttf"; Flags: ignoreversion; Tasks: font

[Code]
const
  ChecksumScript = '\tools\generate_checksums.py';
  ExcludesFile = '\tools\release_excludes.json';
  InstallVenvMode = '{#InstallVenvMode}';
  PythonManualUrl = 'https://www.python.org/downloads/windows/';
  PythonMinMajor = 3;
  PythonMinMinor = 10;

procedure PerformPostInstallTasks; forward;

function BoolToStr(const Value: Boolean; const UseBoolStrs: Boolean): string;
begin
  if Value then
    Result := 'True'
  else
    Result := 'False';
end;

function GetDefaultPluginDir(Param: string): string;
begin
  if DirExists(ExpandConstant('{localappdata}\EDMarketConnector\plugins')) then
    Result := ExpandConstant('{localappdata}\EDMarketConnector\plugins')
  else
    Result := ExpandConstant('{userprofile}\AppData\Local\EDMarketConnector\plugins');
end;

function IsProcessRunning(const Name: string): Boolean;
var
  WbemLocator, WbemServices, WbemObjectSet: Variant;
begin
  Result := False;
  try
    WbemLocator := CreateOleObject('WbemScripting.SWbemLocator');
    WbemServices := WbemLocator.ConnectServer('.', 'root\cimv2');
    WbemObjectSet := WbemServices.ExecQuery(Format('Select * from Win32_Process where Name="%s"', [Name]));
    Result := (WbemObjectSet.Count > 0);
  except
    Result := False;
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): string;
var
  response: Integer;
begin
  while IsProcessRunning('EDMarketConnector.exe') do
  begin
    response := MsgBox(
      'Please close EDMarketConnector before installing the overlay.' + #13#10#13#10 +
      'Click Retry after closing it, or Cancel to exit the installer.',
      mbError, MB_RETRYCANCEL or MB_DEFBUTTON2);
    if response <> IDRETRY then
    begin
      Result := 'Setup was cancelled because EDMarketConnector was running.';
      exit;
    end;
  end;
  Result := '';
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  pluginTarget: string;
  response: Integer;
begin
  Result := True;
  if CurPageID = wpSelectDir then
  begin
    pluginTarget := ExpandConstant('{app}') + '\EDMCModernOverlay';
    if DirExists(pluginTarget) then
    begin
      response := MsgBox(
        'An existing EDMCModernOverlay installation was found at:' + #13#10 +
        pluginTarget + #13#10#13#10 +
        'The installer will perform an upgrade. User settings and fonts will be preserved.' + #13#10 +
        'Continue?',
        mbConfirmation, MB_YESNO or MB_DEFBUTTON2);
      if response <> IDYES then
        Result := False;
    end;
  end;
end;

function DisableDirIfExists(const DirPath: string): Boolean;
var
  target: string;
  idx: Integer;
  renamed: Boolean;
begin
  Result := True;
  if DirExists(DirPath) then
  begin
    target := DirPath + '.disabled';
    idx := 1;
    while DirExists(target) do
    begin
      target := DirPath + '.' + IntToStr(idx) + '.disabled';
      idx := idx + 1;
    end;
    renamed := RenameFile(DirPath, target);
    if renamed then
      MsgBox(Format('Legacy plugin folder "%s" was renamed to "%s" to avoid conflicts.', [DirPath, target]), mbInformation, MB_OK)
    else
    begin
      Result := False;
      MsgBox(Format('Failed to rename "%s". Please close any programs using it.', [DirPath]), mbError, MB_OK);
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  pluginRoot, legacy1, legacy2: string;
begin
  if CurStep = ssInstall then
  begin
    pluginRoot := ExpandConstant('{app}');
    legacy1 := pluginRoot + '\EDMC-ModernOverlay';
    legacy2 := pluginRoot + '\EDMCOverlay';
    if not DisableDirIfExists(legacy1) then
      WizardForm.Close;
    if not DisableDirIfExists(legacy2) then
      WizardForm.Close;
  end
  else if CurStep = ssPostInstall then
  begin
    PerformPostInstallTasks;
  end;
end;

function RunAndCheck(const FileName, Params, WorkDir, Friendly: string): Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec(FileName, Params, WorkDir, SW_HIDE, ewWaitUntilTerminated, ResultCode);
  if (not Result) or (ResultCode <> 0) then
  begin
    MsgBox(Format('%s failed (code %d).', [Friendly, ResultCode]), mbError, MB_OK);
    Result := False;
  end;
end;

function GetChecksumScriptPath(): string;
begin
  Result := ExpandConstant('{tmp}') + ChecksumScript;
end;

function GetExcludesPath(): string;
begin
  Result := ExpandConstant('{tmp}') + ExcludesFile;
end;

function GetPayloadManifestPath(): string;
begin
  Result := ExpandConstant('{tmp}') + '\checksums_payload.txt';
end;

function GetVenvPython(): string;
begin
  Result := ExpandConstant('{app}') + '\EDMCModernOverlay\overlay_client\.venv\Scripts\python.exe';
end;

function IsEmbeddedMode(): Boolean;
begin
  Result := CompareText(InstallVenvMode, 'embedded') = 0;
end;

function IsBuildMode(): Boolean;
begin
  Result := CompareText(InstallVenvMode, 'build') = 0;
end;

function PosExLocal(const SubStr, S: string; Offset: Integer): Integer;
var
  i, maxI: Integer;
begin
  Result := 0;
  if (Offset < 1) or (SubStr = '') then
    exit;
  maxI := Length(S) - Length(SubStr) + 1;
  for i := Offset to maxI do
  begin
    if Copy(S, i, Length(SubStr)) = SubStr then
    begin
      Result := i;
      exit;
    end;
  end;
end;

function ReadNextLine(const Text: string; var Index: Integer): string;
var
  startPos: Integer;
begin
  startPos := Index;
  while (Index <= Length(Text)) and (Text[Index] <> #10) do
    Index := Index + 1;
  Result := Copy(Text, startPos, Index - startPos);
  if (Index <= Length(Text)) and (Text[Index] = #10) then
    Index := Index + 1;
  StringChangeEx(Result, #13, '', True);
  Result := Trim(Result);
end;

function SplitVersionString(const Version: string; var Major, Minor, Patch: Integer): Boolean;
var
  p1, p2: Integer;
  sMajor, sMinor, sPatch: string;
begin
  Result := False;
  Major := -1;
  Minor := -1;
  Patch := -1;
  p1 := Pos('.', Version);
  if p1 = 0 then exit;
  p2 := PosExLocal('.', Version, p1 + 1);
  if p2 = 0 then exit;
  sMajor := Copy(Version, 1, p1 - 1);
  sMinor := Copy(Version, p1 + 1, p2 - p1 - 1);
  sPatch := Copy(Version, p2 + 1, MaxInt);
  Major := StrToIntDef(sMajor, -1);
  Minor := StrToIntDef(sMinor, -1);
  Patch := StrToIntDef(sPatch, -1);
  Result := (Major >= 0) and (Minor >= 0) and (Patch >= 0);
end;

function CompareVersions(const Left, Right: string): Integer;
var
  lMajor, lMinor, lPatch: Integer;
  rMajor, rMinor, rPatch: Integer;
begin
  if (not SplitVersionString(Left, lMajor, lMinor, lPatch)) or
     (not SplitVersionString(Right, rMajor, rMinor, rPatch)) then
  begin
    Result := 0;
    exit;
  end;
  if lMajor <> rMajor then Result := lMajor - rMajor
  else if lMinor <> rMinor then Result := lMinor - rMinor
  else Result := lPatch - rPatch;
end;

function IsPythonVersionAtLeast(const Version: string; MinMajor, MinMinor: Integer): Boolean;
var
  major, minor, patch: Integer;
begin
  Result := False;
  if not SplitVersionString(Version, major, minor, patch) then
    exit;
  if major > MinMajor then
    Result := True
  else if (major = MinMajor) and (minor >= MinMinor) then
    Result := True;
end;

function GetPyprojectPath(): string;
begin
  Result := ExpandConstant('{app}') + '\EDMCModernOverlay\pyproject.toml';
end;

function ParseWindowsPythonMetadata(var Version, Url, Sha, TargetTemplate, ExeTemplate: string): Boolean;
var
  contentAnsi: AnsiString;
  content, line, key, value: string;
  idx: Integer;
  inSection: Boolean;
  eqPos: Integer;
begin
  Result := False;
  Version := '';
  Url := '';
  Sha := '';
  TargetTemplate := '';
  ExeTemplate := '';

  if not LoadStringFromFile(GetPyprojectPath(), contentAnsi) then
  begin
    Log('Failed to read pyproject.toml for Windows Python metadata.');
    exit;
  end;

  content := contentAnsi;
  StringChangeEx(content, #13#10, #10, True);
  idx := 1;
  inSection := False;
  while idx <= Length(content) do
  begin
    line := ReadNextLine(content, idx);
    if line = '' then
      continue;
    if (line[1] = '#') or (line[1] = ';') then
      continue;
    if (line[1] = '[') and (line[Length(line)] = ']') then
    begin
      if inSection then
        break;
      inSection := CompareText(line, '[tool.windows_python_install]') = 0;
      continue;
    end;
    if not inSection then
      continue;
    eqPos := Pos('=', line);
    if eqPos = 0 then
      continue;
    key := Trim(Copy(line, 1, eqPos - 1));
    value := Trim(Copy(line, eqPos + 1, MaxInt));
    if (Length(value) >= 2) and (value[1] = '"') and (value[Length(value)] = '"') then
      value := Copy(value, 2, Length(value) - 2);
    if CompareText(key, 'version') = 0 then
      Version := value
    else if CompareText(key, 'url') = 0 then
      Url := value
    else if CompareText(key, 'sha256') = 0 then
      Sha := value
    else if CompareText(key, 'target_dir_template') = 0 then
      TargetTemplate := value
    else if CompareText(key, 'python_exe_template') = 0 then
      ExeTemplate := value;
  end;

  Result := (Version <> '') and (Url <> '') and (Sha <> '') and (TargetTemplate <> '') and (ExeTemplate <> '');
  if not Result then
    Log('Incomplete Windows Python metadata found in pyproject.toml.');
end;

function ExpandPythonTemplate(const Template, Version: string): string;
var
  major, minor, patch: Integer;
  majorStr, minorStr: string;
begin
  Result := Template;
  if SplitVersionString(Version, major, minor, patch) then
  begin
    majorStr := IntToStr(major);
    minorStr := IntToStr(minor);
    StringChangeEx(Result, '{MAJOR}', majorStr, True);
    StringChangeEx(Result, '{MINOR}', minorStr, True);
  end;
  StringChangeEx(Result, '%LOCALAPPDATA%', ExpandConstant('{localappdata}'), True);
end;

function ExtractUrlFilename(const Url: string): string;
var
  idx: Integer;
begin
  Result := '';
  for idx := Length(Url) downto 1 do
  begin
    if Url[idx] = '/' then
    begin
      Result := Copy(Url, idx + 1, MaxInt);
      exit;
    end;
  end;
end;

function GetPythonInfo(const PythonCommand: string; var ExePath, Version: string): Boolean;
var
  tmpFile: string;
  params: string;
  resultCode: Integer;
  outputAnsi: AnsiString;
  output, line1, line2: string;
  idx: Integer;
begin
  Result := False;
  tmpFile := ExpandConstant('{tmp}') + '\python_info.txt';
  DeleteFile(tmpFile);
  params := Format('/c ""%s" -c "import sys; print(sys.executable); print(''{}.{}.{}''.format(*sys.version_info[:3]))" > "%s""', [PythonCommand, tmpFile]);
  if not Exec(ExpandConstant('{cmd}'), params, '', SW_HIDE, ewWaitUntilTerminated, resultCode) then
    exit;
  if resultCode <> 0 then
    exit;
  if not LoadStringFromFile(tmpFile, outputAnsi) then
    exit;
  output := Trim(outputAnsi);
  if output = '' then
    exit;
  idx := 1;
  line1 := ReadNextLine(output, idx);
  line2 := ReadNextLine(output, idx);
  ExePath := Trim(line1);
  Version := Trim(line2);
  if ExePath = '' then
    ExePath := PythonCommand;
  Result := Version <> '';
end;

function FindPython(var PythonExe, PythonVersion: string; const DeterministicPath: string; var FoundViaPath: Boolean): Boolean;
var
  exePath, version: string;
begin
  Result := False;
  FoundViaPath := False;

  if GetPythonInfo('python', exePath, version) then
  begin
    if IsPythonVersionAtLeast(version, PythonMinMajor, PythonMinMinor) then
    begin
      PythonExe := exePath;
      PythonVersion := version;
      FoundViaPath := True;
      Result := True;
      exit;
    end
    else
      Log(Format('Python on PATH is %s (below required %d.%d).', [version, PythonMinMajor, PythonMinMinor]));
  end;

  if (DeterministicPath <> '') and FileExists(DeterministicPath) then
  begin
    if GetPythonInfo(DeterministicPath, exePath, version) then
    begin
      if IsPythonVersionAtLeast(version, PythonMinMajor, PythonMinMinor) then
      begin
        PythonExe := exePath;
        PythonVersion := version;
        Result := True;
        exit;
      end
      else
        Log(Format('Python at %s is %s (below required %d.%d).', [DeterministicPath, version, PythonMinMajor, PythonMinMinor]));
    end;
  end;
end;

function DownloadFileWithPowerShell(const Url, Dest: string): Boolean;
var
  params: string;
  resultCode: Integer;
begin
  params := Format('-NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -Uri ''%s'' -OutFile ''%s'' -UseBasicParsing -ErrorAction Stop } catch { exit 1 }"', [Url, Dest]);
  Result := Exec('powershell', params, '', SW_HIDE, ewWaitUntilTerminated, resultCode);
  if (not Result) or (resultCode <> 0) then
    Result := False;
end;

function VerifySha256(const FilePath, Expected: string): Boolean;
var
  actual: string;
begin
  actual := Lowercase(GetSHA256OfFile(FilePath));
  Result := actual = Lowercase(Expected);
  if not Result then
    Log(Format('SHA-256 mismatch: expected %s, got %s', [Expected, actual]));
end;

function InstallPythonInstaller(const InstallerPath, TargetDir: string): Boolean;
var
  params: string;
  resultCode: Integer;
begin
  params := Format('/quiet InstallAllUsers=0 PrependPath=0 Include_launcher=0 Include_pip=1 TargetDir="%s"', [TargetDir]);
  Result := Exec(InstallerPath, params, '', SW_HIDE, ewWaitUntilTerminated, resultCode);
  if (not Result) or (resultCode <> 0) then
    Result := False;
end;

function VenvMeetsRequirements(const PythonExe: string): Boolean;
var
  checkScript, logPath, scriptContent, logContent: string;
  logContentAnsi: AnsiString;
  resultCode: Integer;
begin
  checkScript := ExpandConstant('{tmp}') + '\venv_check.py';
  logPath := ExpandConstant('{tmp}') + '\venv_check_output.txt';
  scriptContent :=
    'import sys, traceback' + #13#10 +
    'from importlib import metadata' + #13#10 +
    'log_path = sys.argv[1]' + #13#10 +
    'lines = []' + #13#10 +
    'lines.append("sys_executable=" + sys.executable)' + #13#10 +
    'lines.append("sys_version=" + sys.version.replace("\\n", " "))' + #13#10 +
    'ok = sys.version_info >= (3, 10)' + #13#10 +
    'try:' + #13#10 +
    '    ver = metadata.version("PyQt6")' + #13#10 +
    '    lines.append("pyqt6_version=" + ver)' + #13#10 +
    '    try:' + #13#10 +
    '        ver_t = tuple(int(x) for x in ver.split(".")[0:2])' + #13#10 +
    '    except Exception:' + #13#10 +
    '        ver_t = (0, 0)' + #13#10 +
    '    ok = ok and ver_t >= (6, 5)' + #13#10 +
    'except Exception:' + #13#10 +
    '    ok = False' + #13#10 +
    '    lines.append("pyqt6_import_error=" + traceback.format_exc())' + #13#10 +
    'with open(log_path, "w", encoding="utf-8") as fh:' + #13#10 +
    '    fh.write("\\n".join(lines))' + #13#10 +
    'sys.exit(0 if ok else 1)';

  if not SaveStringToFile(checkScript, scriptContent, False) then
  begin
    MsgBox('Failed to write venv check script.', mbError, MB_OK);
    Result := False;
    exit;
  end;

  DeleteFile(logPath);
  Log(Format('Checking existing venv using: %s %s %s', [PythonExe, checkScript, logPath]));

  if not Exec(PythonExe, Format('"%s" "%s"', [checkScript, logPath]), '', SW_HIDE, ewWaitUntilTerminated, resultCode) then
  begin
    Log('Exec failed launching venv check script.');
    MsgBox('Existing venv Python/deps check could not be launched (see log).', mbError, MB_OK);
    Result := False;
    exit;
  end;

  if LoadStringFromFile(logPath, logContentAnsi) then
  begin
    logContent := logContentAnsi;
    Log('Existing venv check details:'#13#10 + logContent)
  end
  else
    Log('Existing venv check produced no log output.');

  Result := (resultCode = 0);
  if not Result then
    MsgBox(Format('Existing venv Python/deps check failed (code %d). See log for details.', [resultCode]), mbError, MB_OK);
end;

function GetChecksumManifest(): string;
begin
  Result := ExpandConstant('{app}') + '\EDMCModernOverlay\checksums.txt';
end;

procedure PerformPostInstallTasks;
var
  checksumScriptPath, manifest, appRoot, venvPython: string;
  excludesPath, payloadManifest: string;
  pythonCheckCmd, includeArg, pythonForChecks, systemPython: string;
  hasExistingVenv, skipRebuild, needsRebuild, venvMatches: Boolean;
  response: Integer;
  metaVersion, metaUrl, metaSha, metaTargetTemplate, metaExeTemplate: string;
  pythonExe, pythonVersion, deterministicExe, deterministicTargetDir: string;
  pythonFound, foundViaPath, forceInstall: Boolean;
  installerPath: string;
  pathSource: string;
begin
  checksumScriptPath := GetChecksumScriptPath();
  excludesPath := GetExcludesPath();
  payloadManifest := GetPayloadManifestPath();
  manifest := GetChecksumManifest();
  appRoot := ExpandConstant('{app}');
  venvPython := GetVenvPython();
  includeArg := '';
  pythonForChecks := 'python';
  hasExistingVenv := FileExists(venvPython);
  skipRebuild := False;
  needsRebuild := False;

  if IsEmbeddedMode() then
  begin
    includeArg := ' --include-venv';
    if not hasExistingVenv then
    begin
      MsgBox('Bundled virtual environment was not found. Cannot continue in embedded mode.', mbError, MB_OK);
      exit;
    end;

    venvMatches := VenvMeetsRequirements(venvPython);
    if venvMatches then
    begin
      response := MsgBox(
        'An existing virtual environment was found and appears to meet requirements.' + #13#10 +
        'Skip rebuilding it and reuse as-is?',
        mbConfirmation, MB_YESNO or MB_DEFBUTTON2);
      if response = IDYES then
        skipRebuild := True;
    end
    else
    begin
      response := MsgBox(
        'The bundled virtual environment appears outdated or missing dependencies.' + #13#10 +
        'Rebuild it now using the bundled environment?',
        mbConfirmation, MB_YESNO or MB_DEFBUTTON1);
      if response <> IDYES then
      begin
        MsgBox('Installation cannot continue without a valid virtual environment.', mbError, MB_OK);
        exit;
      end;
    end;

    pythonForChecks := venvPython;
    pythonCheckCmd := '-c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"';
    if not RunAndCheck(venvPython, pythonCheckCmd, '', 'Bundled Python 3.10+ check') then
      exit;
  end
  else if IsBuildMode() then
  begin
    Log(Format('Build mode selected. Existing venv: %s (exists=%s)', [venvPython, BoolToStr(hasExistingVenv, True)]));
    forceInstall := CmdLineParamExists('ForcePythonInstall');

    if not ParseWindowsPythonMetadata(metaVersion, metaUrl, metaSha, metaTargetTemplate, metaExeTemplate) then
    begin
      MsgBox('Python installer metadata could not be read from pyproject.toml. Cannot continue.', mbError, MB_OK);
      exit;
    end;

    deterministicTargetDir := ExpandPythonTemplate(metaTargetTemplate, metaVersion);
    deterministicExe := ExpandPythonTemplate(metaExeTemplate, metaVersion);

    pythonFound := FindPython(pythonExe, pythonVersion, deterministicExe, foundViaPath);
    if pythonFound then
    begin
      if foundViaPath then
        pathSource := 'PATH'
      else
        pathSource := 'deterministic path';
      Log(Format('Detected Python %s at %s (via %s).', [pythonVersion, pythonExe, pathSource]));
      if CompareVersions(pythonVersion, metaVersion) < 0 then
        Log(Format('Detected Python %s is older than pinned %s; continuing without upgrade.', [pythonVersion, metaVersion]));
    end
    else
      Log('No Python 3.10+ detected on PATH or deterministic path.');

    if forceInstall or (not pythonFound) then
    begin
      response := MsgBox(
        'Python 3.10+ is required to set up the overlay client.' + #13#10 +
        'Download and install Python now?' + #13#10#13#10 +
        'Manual download: ' + PythonManualUrl,
        mbConfirmation, MB_YESNO or MB_DEFBUTTON1);
      if response <> IDYES then
      begin
        if pythonFound then
          Log('User declined Python download; continuing with existing Python.')
        else
        begin
          MsgBox('Python 3.10+ is required. Please install it from ' + PythonManualUrl + ' and re-run the installer.', mbError, MB_OK);
          exit;
        end;
      end
      else
      begin
        installerPath := ExtractUrlFilename(metaUrl);
        if installerPath = '' then
          installerPath := 'python-installer.exe';
        installerPath := ExpandConstant('{tmp}') + '\' + installerPath;
        if FileExists(installerPath) then
          DeleteFile(installerPath);

        Log(Format('Downloading Python installer from %s to %s', [metaUrl, installerPath]));
        if not DownloadFileWithPowerShell(metaUrl, installerPath) then
        begin
          MsgBox('Failed to download the Python installer. Please install Python manually from ' + PythonManualUrl + '.', mbError, MB_OK);
          exit;
        end;

        Log('Verifying Python installer checksum...');
        if not VerifySha256(installerPath, metaSha) then
        begin
          MsgBox('Python installer checksum verification failed. Please install Python manually from ' + PythonManualUrl + '.', mbError, MB_OK);
          exit;
        end;

        Log(Format('Installing Python to %s', [deterministicTargetDir]));
        if not InstallPythonInstaller(installerPath, deterministicTargetDir) then
        begin
          MsgBox('Python installer failed. Please install Python manually from ' + PythonManualUrl + '.', mbError, MB_OK);
          exit;
        end;

        if FileExists(installerPath) then
          DeleteFile(installerPath);

        if not GetPythonInfo(deterministicExe, pythonExe, pythonVersion) then
        begin
          MsgBox('Python installation did not complete successfully (python.exe not found).', mbError, MB_OK);
          exit;
        end;

        if not IsPythonVersionAtLeast(pythonVersion, PythonMinMajor, PythonMinMinor) then
        begin
          MsgBox('Installed Python does not meet the 3.10+ requirement.', mbError, MB_OK);
          exit;
        end;

        Log(Format('Installed Python %s at %s.', [pythonVersion, pythonExe]));
        pythonFound := True;
      end;
    end;

    if hasExistingVenv then
    begin
      Log('Checking existing venv for reuse...');
      venvMatches := VenvMeetsRequirements(venvPython);
      if venvMatches then
      begin
        response := MsgBox(
          'An existing virtual environment was found and appears to meet requirements.' + #13#10 +
          'Skip rebuilding it and reuse as-is?',
          mbConfirmation, MB_YESNO or MB_DEFBUTTON2);
        if response = IDYES then
        begin
          skipRebuild := True;
          pythonForChecks := venvPython;
        end;
        Log(Format('Existing venv check passed; user chose reuse=%s', [BoolToStr(skipRebuild, True)]));
      end;

      if (not venvMatches) or (not skipRebuild) then
      begin
        Log('Existing venv check failed or user chose rebuild; scheduling rebuild.');
        needsRebuild := True;
      end;
    end
    else
    begin
      Log('No existing venv found; scheduling rebuild.');
      needsRebuild := True;
    end;

    if needsRebuild then
    begin
      if not pythonFound then
      begin
        MsgBox('Python 3.10+ is required to rebuild the virtual environment.', mbError, MB_OK);
        exit;
      end;
      systemPython := pythonExe;
      Log('Starting venv rebuild using system Python (requires 3.10+)...');
      pythonCheckCmd := '-c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"';
      if not RunAndCheck(systemPython, pythonCheckCmd, '', 'System Python 3.10+ check') then
        exit;

      WizardForm.StatusLabel.Caption := 'Creating virtual environment...';
      WizardForm.ProgressGauge.Max := 3;
      WizardForm.ProgressGauge.Position := 1;
      WizardForm.ProgressGauge.Update;

      if not RunAndCheck(systemPython, Format('-m venv "%s"', [appRoot + '\EDMCModernOverlay\overlay_client\.venv']), '', 'Virtual environment creation (system Python)') then
        exit;

      if not FileExists(venvPython) then
      begin
        MsgBox('Virtual environment python.exe not found after creation.', mbError, MB_OK);
        exit;
      end;

      pythonForChecks := venvPython;

      WizardForm.StatusLabel.Caption := 'Installing dependencies (online)...';
      WizardForm.ProgressGauge.Position := 2;
      WizardForm.ProgressGauge.Update;

      Log('Upgrading pip in rebuilt venv...');
      if not RunAndCheck(venvPython, '-m pip install --upgrade pip', '', 'Dependency installation (online)') then
        exit;

      Log('Installing PyQt6>=6.5 in rebuilt venv...');
      if not RunAndCheck(venvPython, '-m pip install PyQt6>=6.5', '', 'Dependency installation (online)') then
        exit;

      Log('Venv rebuild completed.');
    end
    else
      pythonForChecks := venvPython;
  end
  else
  begin
    MsgBox(Format('Unknown InstallVenvMode: %s', [InstallVenvMode]), mbError, MB_OK);
    exit;
  end;

  if FileExists(payloadManifest) then
  begin
    if not RunAndCheck(pythonForChecks, Format('"%s" --verify --root "%s" --manifest "%s" --excludes "%s" --skip "EDMCModernOverlay"', [checksumScriptPath, ExpandConstant('{tmp}'), payloadManifest, excludesPath]), '', 'Payload checksum validation') then
      exit;
  end;

  if not RunAndCheck(pythonForChecks, Format('"%s" --verify --root "%s" --manifest "%s" --excludes "%s"%s', [checksumScriptPath, appRoot, manifest, excludesPath, includeArg]), '', 'Checksum validation') then
    exit;
end;
