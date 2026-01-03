# Collect EDMC Modern Overlay diagnostics for support.

$ScriptName = "collect_overlay_debug_windows.ps1"

function Fail {
    param([string]$Message)
    [Console]::Error.WriteLine("${ScriptName}: $Message")
    exit 1
}

function Resolve-RealPath {
    param([string]$Path)
    if (-not $Path) {
        return $null
    }
    try {
        return (Resolve-Path -LiteralPath $Path -ErrorAction Stop).ProviderPath
    } catch {
        return $null
    }
}

function Validate-PluginRoot {
    param(
        [string]$Root,
        [switch]$Quiet
    )

    $missing = $false
    $requiredDirs = @(
        "overlay_client",
        "overlay_plugin"
    )
    $requiredFiles = @(
        "edmcoverlay.py",
        "load.py"
    )

    foreach ($rel in $requiredDirs) {
        $path = Join-Path $Root $rel
        if (-not (Test-Path -LiteralPath $path -PathType Container)) {
            if (-not $Quiet) {
                [Console]::Error.WriteLine("${ScriptName}: expected directory missing: $path")
            }
            $missing = $true
        }
    }

    foreach ($rel in $requiredFiles) {
        $path = Join-Path $Root $rel
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            if (-not $Quiet) {
                [Console]::Error.WriteLine("${ScriptName}: expected file missing: $path")
            }
            $missing = $true
        }
    }

    return (-not $missing)
}

function PluginRoot-IsValid {
    param([string]$Root)
    if (-not $Root) {
        return $false
    }
    return (Validate-PluginRoot -Root $Root -Quiet)
}

function Confirm-PluginRoot {
    param(
        [string]$Detected,
        [string]$Suggested
    )

    $candidate = $null
    if ($Detected -and (PluginRoot-IsValid $Detected)) {
        $candidate = $Detected
    }

    if ([Console]::IsInputRedirected) {
        if ($candidate) {
            $resolved = Resolve-RealPath $candidate
            if (-not $resolved) {
                $resolved = $candidate
            }
            [Console]::Error.WriteLine("Detected plugin root: $resolved (non-interactive, accepting)")
            return $resolved
        }
        if ($Suggested -and (PluginRoot-IsValid $Suggested)) {
            $resolved = Resolve-RealPath $Suggested
            if (-not $resolved) {
                $resolved = $Suggested
            }
            [Console]::Error.WriteLine("Using suggested plugin root: $resolved (non-interactive)")
            return $resolved
        }
        Fail "unable to locate a valid EDMC Modern Overlay installation. Run interactively and provide the plugin path."
    }

    $current = $candidate
    if (-not $current) {
        $current = $Suggested
    }

    while ($true) {
        $isValid = $false
        if ($current -and (PluginRoot-IsValid $current)) {
            $isValid = $true
        }

        if ($isValid) {
            [Console]::Error.WriteLine("Detected plugin root: $current")
            $response = Read-Host "Use this location? [Y/n]"
            if (-not $response) {
                $response = "Y"
            }
            if ($response -match "^[Yy]") {
                $resolved = Resolve-RealPath $current
                if (-not $resolved) {
                    $resolved = $current
                }
                return $resolved
            }
            if ($response -match "^[Nn]") {
                $current = $null
                continue
            }
            [Console]::Error.WriteLine("Please answer yes or no.")
            continue
        }

        if ($current -and (-not $isValid)) {
            [Console]::Error.WriteLine("The path `"$current`" does not look like an EDMC Modern Overlay installation.")
        } elseif (-not $current) {
            [Console]::Error.WriteLine("Unable to detect the plugin location automatically.")
        }

        if ($Suggested) {
            [Console]::Error.WriteLine("Suggested location: $Suggested")
        }

        if ($Suggested) {
            $input = Read-Host "Enter plugin root path [$Suggested]"
        } else {
            $input = Read-Host "Enter plugin root path"
        }

        if ([string]::IsNullOrWhiteSpace($input)) {
            if ($Suggested) {
                $input = $Suggested
            } else {
                [Console]::Error.WriteLine("Path cannot be empty.")
                $current = $null
                continue
            }
        }

        $resolved = Resolve-RealPath $input
        if (-not $resolved) {
            [Console]::Error.WriteLine("${ScriptName}: unable to resolve path: $input")
            $current = $null
            continue
        }

        $current = $resolved
    }
}

$LogLines = 60
$ShowLogs = $false

function Write-Usage {
    param([switch]$ToError)
    $text = @"
Usage: collect_overlay_debug_windows.ps1 [--log-lines N] [--show-logs]

Gather environment details, dependency checks, and recent overlay logs.

Options:
  --log-lines N   Number of lines to tail from the newest overlay_client log (default: 60)
  --show-logs     Include overlay_client log tail output
  -h, --help      Show this help message and exit
"@
    $lines = $text -split "`r?`n"
    foreach ($line in $lines) {
        if ($ToError) {
            [Console]::Error.WriteLine($line)
        } else {
            Write-Output $line
        }
    }
}
$idx = 0
while ($idx -lt $args.Count) {
    $arg = $args[$idx]
    switch ($arg) {
        "--log-lines" {
            $idx++
            if ($idx -ge $args.Count) {
                [Console]::Error.WriteLine("Missing value for --log-lines")
                exit 1
            }
            $value = $args[$idx]
            if (-not $value -or ($value -notmatch "^[0-9]+$")) {
                [Console]::Error.WriteLine("Invalid log line count: $value")
                exit 1
            }
            $LogLines = [int]$value
        }
        "--show-logs" {
            $ShowLogs = $true
        }
        "-h" {
            Write-Usage
            exit 0
        }
        "--help" {
            Write-Usage
            exit 0
        }
        default {
            [Console]::Error.WriteLine("Unknown option: $arg")
            Write-Usage -ToError
            exit 1
        }
    }
    $idx++
}

$scriptPath = Resolve-RealPath $MyInvocation.MyCommand.Path
if (-not $scriptPath) {
    Fail "unable to resolve script path."
}
$scriptDir = Split-Path -Parent $scriptPath
$detectedRoot = Resolve-RealPath (Join-Path $scriptDir "..")
if (-not $detectedRoot) {
    Fail "unable to determine plugin root."
}
$defaultPluginRoot = $null
if ($env:LOCALAPPDATA) {
    $defaultPluginRoot = Join-Path $env:LOCALAPPDATA "EDMarketConnector\plugins\EDMCModernOverlay"
}
$rootDir = Confirm-PluginRoot $detectedRoot $defaultPluginRoot
if (-not (PluginRoot-IsValid $rootDir)) {
    Fail "unable to locate a valid EDMC Modern Overlay installation."
}

$overlayClientDir = Join-Path $rootDir "overlay_client"
$settingsPath = Join-Path $rootDir "overlay_settings.json"
$portPath = Join-Path $rootDir "port.json"
$envOverridesPath = Join-Path $overlayClientDir "env_overrides.json"
$homeDir = $env:USERPROFILE

function Print-Header {
    param([string]$Title)
    Write-Output ""
    Write-Output "=== $Title ==="
}

function Abbrev-Path {
    param([string]$Path)
    if ($homeDir -and $Path -like "$homeDir*") {
        return "~" + $Path.Substring($homeDir.Length)
    }
    return $Path
}

function Get-PythonCommand {
    param([string]$VenvPython)
    if ($VenvPython -and (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
        return @{ Command = $VenvPython; Args = @(); Display = (Abbrev-Path $VenvPython) }
    }
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        return @{ Command = $pythonCmd.Source; Args = @(); Display = (Abbrev-Path $pythonCmd.Source) }
    }
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) {
        return @{ Command = $pyCmd.Source; Args = @("-3"); Display = "py -3" }
    }
    return $null
}

$venvPythonPath = Join-Path $overlayClientDir ".venv\Scripts\python.exe"
$script:PythonCommand = Get-PythonCommand -VenvPython $venvPythonPath
function Print-SystemInfo {
    Print-Header "System Information"
    $os = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction SilentlyContinue
    if ($os) {
        Write-Output "os: $($os.Caption)"
        Write-Output "version: $($os.Version) (build $($os.BuildNumber))"
        Write-Output "architecture: $($os.OSArchitecture)"
    } else {
        Write-Output "os: <unavailable>"
    }
    if ($env:COMPUTERNAME) {
        Write-Output "hostname: $env:COMPUTERNAME"
    }
    Write-Output "platform: $([System.Environment]::OSVersion.VersionString)"
    Write-Output "powershell: $($PSVersionTable.PSVersion)"
    if ($script:PythonCommand) {
        $cmd = $script:PythonCommand.Command
        $cmdArgs = @()
        if ($script:PythonCommand.Args) {
            $cmdArgs += $script:PythonCommand.Args
        }
        $cmdArgs += "-V"
        $output = & $cmd @cmdArgs 2>&1
        if ($output) {
            Write-Output ("python: " + ($output -join " "))
        } else {
            Write-Output "python: <unavailable>"
        }
    } else {
        Write-Output "python: not found"
    }
}

function Print-Environment {
    Print-Header "Environment Variables"
    $vars = @(
        "USERDOMAIN",
        "USERPROFILE",
        "LOCALAPPDATA",
        "APPDATA",
        "TEMP",
        "PROCESSOR_ARCHITECTURE",
        "PROCESSOR_IDENTIFIER",
        "NUMBER_OF_PROCESSORS",
        "EDMC_OVERLAY_FORCE_XWAYLAND",
        "EDMC_OVERLAY_SESSION_TYPE",
        "EDMC_OVERLAY_COMPOSITOR",
        "EDMC_OVERLAY_LOG_LEVEL",
        "EDMC_OVERLAY_DEBUG",
        "QT_QPA_PLATFORM",
        "QT_QPA_PLATFORMTHEME",
        "QT_PLUGIN_PATH",
        "QT_SCALE_FACTOR",
        "QT_FONT_DPI",
        "QT_AUTO_SCREEN_SCALE_FACTOR",
        "QT_SCALE_FACTOR_ROUNDING_POLICY",
        "QT_SCREEN_SCALE_FACTORS"
    )
    foreach ($key in $vars) {
        $value = [Environment]::GetEnvironmentVariable($key)
        if ($null -ne $value) {
            Write-Output "$key=$value"
        } else {
            Write-Output "$key=<unset>"
        }
    }
}

function Print-CommandAvailability {
    Print-Header "Command Availability"
    $entries = @(
        @{ Name = "python"; Args = @("--version") },
        @{ Name = "py"; Args = @("-3", "--version") },
        @{ Name = "pip"; Args = @("--version") },
        @{ Name = "pip3"; Args = @("--version") }
    )

    foreach ($entry in $entries) {
        $cmd = Get-Command $entry.Name -ErrorAction SilentlyContinue
        if ($cmd) {
            Write-Output ("{0}: {1}" -f $entry.Name, $cmd.Source)
            if ($entry.Args.Count -gt 0) {
                $output = & $cmd.Source @($entry.Args) 2>&1
                $status = $LASTEXITCODE
                if ($output) {
                    foreach ($line in $output) {
                        Write-Output "  $line"
                    }
                } elseif ($status -ne 0) {
                    Write-Output ("  note: exit {0} with no output" -f $status)
                }
            }
        } else {
            Write-Output ("{0}: <not found>" -f $entry.Name)
        }
    }
}

function Check-RequiredPackages {
    Print-Header "Required Packages (install_matrix.json)"
    Write-Output "Not applicable on Windows; skipping package checks."
}

function Print-MonitorInfo {
    Print-Header "Monitors"
    $printed = $false
    try {
        Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
        $screens = [System.Windows.Forms.Screen]::AllScreens
        if ($screens.Count -gt 0) {
            foreach ($screen in $screens) {
                $bounds = $screen.Bounds
                $working = $screen.WorkingArea
                Write-Output ("{0}: bounds={1}x{2}+{3}+{4} working={5}x{6}+{7}+{8} primary={9}" -f `
                    $screen.DeviceName, $bounds.Width, $bounds.Height, $bounds.X, $bounds.Y, `
                    $working.Width, $working.Height, $working.X, $working.Y, $screen.Primary)
            }
            $printed = $true
        }
    } catch {
        $printed = $false
    }

    if (-not $printed) {
        $monitors = Get-CimInstance -ClassName Win32_DesktopMonitor -ErrorAction SilentlyContinue
        if ($monitors) {
            foreach ($mon in $monitors) {
                $name = $mon.Name
                if (-not $name) {
                    $name = "<unnamed>"
                }
                Write-Output ("{0}: screen_height={1} screen_width={2}" -f $name, $mon.ScreenHeight, $mon.ScreenWidth)
            }
            $printed = $true
        }
    }

    if (-not $printed) {
        Write-Output "No monitor enumeration available."
    }
}
function Check-Virtualenv {
    Print-Header "Overlay Client Virtualenv"
    $venvDir = Join-Path $overlayClientDir ".venv"
    $venvPython = Join-Path $venvDir "Scripts\python.exe"
    $venvPip = Join-Path $venvDir "Scripts\pip.exe"
    $requirementsFile = Join-Path $overlayClientDir "requirements.txt"
    $baseRequirementsFile = Join-Path $overlayClientDir "requirements\base.txt"

    if (Test-Path -LiteralPath $venvDir -PathType Container) {
        Write-Output (".venv: {0}" -f (Abbrev-Path $venvDir))
    } else {
        Write-Output ".venv: <missing>"
    }

    if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
        Write-Output ("python: {0}" -f (Abbrev-Path $venvPython))
        $version = & $venvPython -V 2>&1
        Write-Output ("python version: {0}" -f ($version -join " "))
    } else {
        Write-Output "python: <missing>"
    }

    if (Test-Path -LiteralPath $venvPip -PathType Leaf) {
        $pipVersion = & $venvPip --version 2>&1
        if ($homeDir) {
            $pipVersion = $pipVersion -replace [regex]::Escape($homeDir), "~"
        }
        Write-Output ("pip: {0}" -f ($pipVersion -join " "))
    } else {
        Write-Output "pip: <missing>"
    }

    if (Test-Path -LiteralPath $requirementsFile -PathType Leaf) {
        Write-Output ("requirements.txt: {0}" -f (Abbrev-Path $requirementsFile))
    } else {
        Write-Output "requirements.txt: <missing>"
    }

    if (Test-Path -LiteralPath $baseRequirementsFile -PathType Leaf) {
        Write-Output ("requirements/base.txt: {0}" -f (Abbrev-Path $baseRequirementsFile))
    } else {
        Write-Output "requirements/base.txt: <missing>"
    }

    $requirementsCheck = $null
    if (Test-Path -LiteralPath $requirementsFile -PathType Leaf) {
        $requirementsCheck = $requirementsFile
    } elseif (Test-Path -LiteralPath $baseRequirementsFile -PathType Leaf) {
        $requirementsCheck = $baseRequirementsFile
    }

    if ((Test-Path -LiteralPath $venvPython -PathType Leaf) -and $requirementsCheck) {
        $pyScript = @"
import sys
from pathlib import Path
try:
    import importlib.metadata as metadata
except ImportError:
    import importlib_metadata as metadata

try:
    from packaging.requirements import Requirement
except Exception:
    Requirement = None

req_path = Path(sys.argv[1])
missing = []
evaluated = 0
lines = req_path.read_text(encoding="utf-8").splitlines()

for raw_line in lines:
    line = raw_line.strip()
    if not line or line.startswith("#"):
        continue
    candidate = line
    if Requirement is not None:
        try:
            req = Requirement(candidate)
        except Exception:
            req = None
        if req is not None:
            if req.marker and not req.marker.evaluate():
                continue
            candidate = req.name
    else:
        candidate = candidate.split("#", 1)[0].strip()
        for sep in ("[", ";", "<", ">", "=", "!", "~", " ", "\t"):
            idx = candidate.find(sep)
            if idx != -1:
                candidate = candidate[:idx]
                break
    name = candidate.strip()
    if not name:
        continue
    evaluated += 1
    try:
        metadata.version(name)
    except metadata.PackageNotFoundError:
        missing.append(name)

if not evaluated:
    print("no installable requirements listed")
elif missing:
    print("missing packages: " + ", ".join(sorted(set(missing))))
    sys.exit(1)
else:
    print("requirements satisfied")
"@
        $checkOutput = $pyScript | & $venvPython - $requirementsCheck 2>&1
        $status = $LASTEXITCODE
        if ($checkOutput) {
            foreach ($line in $checkOutput) {
                Write-Output "  $line"
            }
        }
        if ($status -ne 0) {
            Write-Output ("  requirements status: pip check failed (exit {0})" -f $status)
        } elseif (-not $checkOutput) {
            Write-Output "  requirements status: ok"
        }
    }
}
function Check-PythonModules {
    Print-Header "Python Module Checks"
    $modules = @("PyQt6")
    $interpreters = @()

    if (Test-Path -LiteralPath $venvPythonPath -PathType Leaf) {
        $interpreters += @{ Command = $venvPythonPath; Args = @(); Display = (Abbrev-Path $venvPythonPath) }
    }
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $interpreters += @{ Command = $pythonCmd.Source; Args = @(); Display = (Abbrev-Path $pythonCmd.Source) }
    }
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) {
        $interpreters += @{ Command = $pyCmd.Source; Args = @("-3"); Display = "py -3" }
    }

    if ($interpreters.Count -eq 0) {
        $interpreters += @{ Command = "python"; Args = @(); Display = "python" }
    }

    foreach ($module in $modules) {
        Write-Output ("{0}:" -f $module)
        $found = $false
        foreach ($interpreter in $interpreters) {
            $cmdArgs = @()
            if ($interpreter.Args) {
                $cmdArgs += $interpreter.Args
            }
            $cmdArgs += @("-c", "import $module")
            $output = & $interpreter.Command @cmdArgs 2>&1
            $status = $LASTEXITCODE
            if ($status -eq 0) {
                Write-Output ("  {0}: available" -f $interpreter.Display)
                $found = $true
                break
            }
            $summary = "import_failed"
            if ($output -match "ModuleNotFoundError") {
                $summary = "missing module"
            } elseif ($output -match "ImportError") {
                $summary = "import error"
            }
            Write-Output ("  {0}: {1}" -f $interpreter.Display, $summary)
        }
        if (-not $found) {
            Write-Output "  (module unavailable in checked interpreters)"
        }
    }
}

function Print-WaylandHelpers {
    Print-Header "Wayland Helper Commands"
    Write-Output "Not applicable on Windows."
}

function Gather-OverlayLogCandidates {
    $searchRoots = @(
        (Join-Path $overlayClientDir "logs\EDMCModernOverlay"),
        (Join-Path $rootDir "logs\EDMCModernOverlay")
    )
    $parentRoot = Resolve-RealPath (Join-Path $rootDir "..\..")
    if ($parentRoot) {
        $searchRoots += (Join-Path $parentRoot "logs\EDMCModernOverlay")
    }
    $parentDir = Split-Path -Parent $rootDir
    if ($parentDir) {
        $searchRoots += (Join-Path $parentDir "logs\EDMCModernOverlay")
    }
    if ($homeDir) {
        $searchRoots += (Join-Path $homeDir "EDMCModernOverlay")
        $searchRoots += (Join-Path $homeDir "EDMarketConnector\logs\EDMCModernOverlay")
    }
    if ($env:LOCALAPPDATA) {
        $searchRoots += (Join-Path $env:LOCALAPPDATA "EDMarketConnector\logs\EDMCModernOverlay")
    }

    $candidates = @()
    foreach ($dir in $searchRoots) {
        if (Test-Path -LiteralPath $dir -PathType Container) {
            $items = Get-ChildItem -LiteralPath $dir -Filter "overlay_client.log*" -File -ErrorAction SilentlyContinue
            if ($items) {
                $candidates += $items
            }
        }
    }

    if (-not $candidates -or $candidates.Count -eq 0) {
        return @()
    }

    $sorted = $candidates | Sort-Object -Property LastWriteTimeUtc -Descending
    return $sorted | ForEach-Object { $_.FullName }
}

function Dump-Json {
    param(
        [string]$Label,
        [string]$Path
    )
    Print-Header $Label
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Write-Output ("Unable to read {0}: missing" -f $Label)
        return
    }
    try {
        $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
        $data = $raw | ConvertFrom-Json -ErrorAction Stop
    } catch {
        Write-Output ("Unable to read {0}: invalid JSON or read error" -f $Label)
        return
    }
    $json = $data | ConvertTo-Json -Depth 20
    Write-Output $json
}

function Print-EnvOverrides {
    Print-Header "Env Overrides (overlay_client/env_overrides.json)"
    Write-Output "Note: overrides are opt-in; keys shown here were applied when accepted during install."
    Write-Output "Runtime env vars still win; provenance reflects detection context."
    if (-not (Test-Path -LiteralPath $envOverridesPath -PathType Leaf)) {
        Write-Output "Not present."
        return
    }
    try {
        $raw = Get-Content -LiteralPath $envOverridesPath -Raw -Encoding UTF8
        $data = $raw | ConvertFrom-Json -ErrorAction Stop
    } catch {
        Write-Output ("Unable to read env_overrides.json: {0}" -f $_.Exception.Message)
        return
    }

    $envData = $data.env
    $provData = $data.provenance

    if ($envData -and $envData.PSObject.Properties.Count -gt 0) {
        Write-Output "env:"
        foreach ($key in ($envData.PSObject.Properties.Name | Sort-Object)) {
            Write-Output ("  {0}={1}" -f $key, $envData.$key)
        }
    } else {
        Write-Output "env: <empty>"
    }

    if ($provData -and $provData.PSObject.Properties.Count -gt 0) {
        Write-Output "provenance:"
        foreach ($key in ($provData.PSObject.Properties.Name | Sort-Object)) {
            Write-Output ("  {0}: {1}" -f $key, $provData.$key)
        }
    }
}

function Print-Logs {
    Print-Header "Overlay Client Logs"
    $sorted = Gather-OverlayLogCandidates
    if (-not $sorted -or $sorted.Count -eq 0) {
        Write-Output "No overlay_client logs found in standard locations."
        return
    }
    $latest = $sorted[0]
    $latestDisplay = Abbrev-Path $latest
    Write-Output ("Latest log: {0}" -f $latestDisplay)
    if (Test-Path -LiteralPath $latest -PathType Leaf) {
        $lines = Get-Content -LiteralPath $latest -Tail $LogLines -ErrorAction SilentlyContinue
        if (-not $lines) {
            Write-Output "  <unable to read log file>"
            return
        }
        foreach ($line in $lines) {
            $displayLine = $line
            if ($homeDir) {
                $displayLine = $displayLine -replace [regex]::Escape($homeDir), "~"
            }
            Write-Output ("  {0}" -f $displayLine)
        }
    } else {
        Write-Output "  <unable to read log file>"
    }
}
function Print-DebugOverlaySnapshot {
    Print-Header "Debug Overlay Snapshot"
    $sorted = Gather-OverlayLogCandidates
    if (-not $sorted -or $sorted.Count -eq 0) {
        Write-Output "No overlay_client logs found in standard locations."
        return
    }
    $latest = $sorted[0]
    if (-not (Test-Path -LiteralPath $latest -PathType Leaf)) {
        Write-Output "Latest overlay_client log missing; unable to extract debug overlay information."
        return
    }
    if (-not $script:PythonCommand) {
        Write-Output "Python not available; unable to extract debug overlay information."
        return
    }

    $pyScript = @"
import json
import re
import sys
from pathlib import Path

log_path = Path(sys.argv[1])
settings_path = Path(sys.argv[2])
home_path = str(Path.home())

def abbreviate(path):
    path = str(path)
    if home_path and path.startswith(home_path):
        return "~" + path[len(home_path):]
    return path

try:
    settings_data = json.loads(settings_path.read_text(encoding="utf-8"))
except Exception:
    settings_data = {}

min_font = float(settings_data.get("min_font_point", 6.0))
max_font = float(settings_data.get("max_font_point", 18.0))

patterns = {
    "move": re.compile(
        r"Overlay moveEvent: pos=\((?P<pos>[^)]*)\) frame=\((?P<frame>[^)]*)\) .*? monitor=(?P<monitor>[^;]+);\s*size=(?P<size>[0-9]+x[0-9]+)px scale_x=(?P<scale_x>[0-9.]+) scale_y=(?P<scale_y>[0-9.]+)"
    ),
    "tracker": re.compile(
        r"Tracker state: id=(?P<id>0x[0-9a-fA-F]+) global=\((?P<global>[^)]*)\) size=(?P<size>[0-9]+x[0-9]+) .*?; size=(?P<overlay>[0-9]+x[0-9]+)px scale_x=(?P<scale_x>[0-9.]+) scale_y=(?P<scale_y>[0-9.]+)"
    ),
    "raw": re.compile(r"Raw tracker window geometry: pos=\((?P<pos>[^)]*)\) size=(?P<size>[0-9]+x[0-9]+)"),
    "calculated": re.compile(
        r"Calculated overlay geometry: target=\((?P<target>[^)]*)\);\s*size=(?P<size>[0-9]+x[0-9]+)px scale_x=(?P<scale_x>[0-9.]+) scale_y=(?P<scale_y>[0-9.]+)"
    ),
    "wm": re.compile(
        r"Recorded WM authoritative rect \((?P<meta>[^)]*)\): actual=\((?P<actual>[^)]*)\) tracker=(?P<tracker>[^;]+);\s*size=(?P<size>[0-9]+x[0-9]+)px(?: scale_x=(?P<scale_x>[0-9.]+) scale_y=(?P<scale_y>[0-9.]+))?"
    ),
    "scaling": re.compile(
        r"Overlay scaling updated: window=(?P<width>[0-9]+)x(?P<height>[0-9]+) px "
        r"mode=(?P<mode>[a-z]+) base_scale=(?P<base_scale>[0-9.]+) "
        r"scale_x=(?P<scale_x>[0-9.]+) scale_y=(?P<scale_y>[0-9.]+) diag=(?P<diag>[0-9.]+) "
        r"scaled=(?P<scaled_w>[0-9.]+)x(?P<scaled_h>[0-9.]+) "
        r"offset=\((?P<offset_x>-?[0-9.]+),(?P<offset_y>-?[0-9.]+)\) "
        r"overflow_x=(?P<overflow_x>[01]) overflow_y=(?P<overflow_y>[01]) message_pt=(?P<message>[0-9.]+)"
    ),
    "title_offset": re.compile(
        r"Title bar offset updated: enabled=(?P<enabled>True|False) height=(?P<height>[0-9]+) offset=(?P<offset>-?[0-9]+) scale_y=(?P<scale_y>[0-9.]+)"
    ),
}

latest = {key: None for key in patterns}

with log_path.open("r", encoding="utf-8", errors="replace") as handle:
    for line in handle:
        for key, pattern in patterns.items():
            if key == "move" and "Overlay moveEvent:" not in line:
                continue
            if key == "tracker" and "Tracker state:" not in line:
                continue
            if key == "raw" and "Raw tracker window geometry:" not in line:
                continue
            if key == "calculated" and "Calculated overlay geometry:" not in line:
                continue
            if key == "wm" and "Recorded WM authoritative rect" not in line:
                continue
            if key == "scaling" and "Overlay scaling updated:" not in line:
                continue
            if key == "title_offset" and "Title bar offset updated:" not in line:
                continue
            match = pattern.search(line)
            if match:
                latest[key] = match.groupdict()

def parse_rect(text):
    try:
        parts = [int(p.strip()) for p in text.split(",")]
        if len(parts) == 4:
            return parts
    except Exception:
        pass
    return None

def parse_point(text):
    try:
        parts = [int(p.strip()) for p in text.split(",")]
        if len(parts) == 2:
            return parts
    except Exception:
        pass
    return None

def parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

lines = [f"Source log: {abbreviate(log_path)}"]

move_info = latest.get("move")
tracker_info = latest.get("tracker")
wm_info = latest.get("wm")
raw_info = latest.get("raw")
calc_info = latest.get("calculated")
scaling_info = latest.get("scaling")
title_info = latest.get("title_offset")

scaling_mode = None
scaling_base = None
scaling_scale_x = None
scaling_scale_y = None
scaling_diag = None
scaling_scaled_w = None
scaling_scaled_h = None
scaling_offset_x = None
scaling_offset_y = None
scaling_overflow_x = None
scaling_overflow_y = None
scaling_message = None

if scaling_info:
    raw_mode = (scaling_info.get("mode") or "").strip()
    scaling_mode = raw_mode if raw_mode else None
    scaling_base = parse_float(scaling_info.get("base_scale"))
    scaling_scale_x = parse_float(scaling_info.get("scale_x"))
    scaling_scale_y = parse_float(scaling_info.get("scale_y"))
    scaling_diag = parse_float(scaling_info.get("diag"))
    scaling_scaled_w = parse_float(scaling_info.get("scaled_w"))
    scaling_scaled_h = parse_float(scaling_info.get("scaled_h"))
    scaling_offset_x = parse_float(scaling_info.get("offset_x"))
    scaling_offset_y = parse_float(scaling_info.get("offset_y"))
    scaling_overflow_x = scaling_info.get("overflow_x")
    scaling_overflow_y = scaling_info.get("overflow_y")
    scaling_message = parse_float(scaling_info.get("message"))

lines.append("Monitor:")
if move_info:
    monitor_label = (move_info.get("monitor") or "").strip() or "unknown"
    lines.append(f"  active={monitor_label}")
else:
    lines.append("  active=<unavailable>")

if tracker_info:
    tracker_point = parse_point(tracker_info.get("global", ""))
    tracker_size = tracker_info.get("size", "")
    overlay_size = tracker_info.get("overlay", "")
    scale_x = tracker_info.get("scale_x")
    scale_y = tracker_info.get("scale_y")
    parts = []
    if tracker_point and tracker_size:
        parts.append(f"({tracker_point[0]},{tracker_point[1]}) {tracker_size}")
    if overlay_size:
        parts.append(f"overlay={overlay_size}")
    if scale_x and scale_y:
        parts.append(f"scale={float(scale_x):.2f}x{float(scale_y):.2f}")
    lines.append(f"  tracker={' '.join(parts) if parts else '<unavailable>'}")
else:
    lines.append("  tracker=<unavailable>")

if wm_info:
    actual_rect = parse_rect(wm_info.get("actual", ""))
    meta = wm_info.get("meta", "")
    classification = None
    if "classification=" in meta:
        classification = meta.split("classification=", 1)[-1].strip()
    tracker_rect = wm_info.get("tracker", "").strip()
    if actual_rect:
        rect_desc = f"({actual_rect[0]},{actual_rect[1]}) {actual_rect[2]}x{actual_rect[3]}"
    else:
        rect_desc = wm_info.get("actual", "").strip() or "<unavailable>"
    suffix = f" [{classification}]" if classification else ""
    lines.append(f"  wm_rect={rect_desc}{suffix}")
    if tracker_rect and tracker_rect.lower() != "none":
        lines.append(f"  wm_tracker={tracker_rect}")
else:
    lines.append("  wm_rect=<unavailable>")

lines.append("")
lines.append("Overlay:")
if calc_info:
    rect = parse_rect(calc_info.get("target", ""))
    if rect:
        lines.append(f"  frame=({rect[0]},{rect[1]}) {rect[2]}x{rect[3]}")
    else:
        lines.append(f"  frame={calc_info.get('target', '<unavailable>')}")
    size_desc = calc_info.get("size")
    if size_desc:
        lines.append(f"  widget={size_desc}")
    scale_x = calc_info.get("scale_x")
    scale_y = calc_info.get("scale_y")
    if scale_x and scale_y:
        lines.append(f"  calc_scale={float(scale_x):.2f}x{float(scale_y):.2f}")
else:
    lines.append("  frame=<unavailable>")

if raw_info:
    raw_point = parse_point(raw_info.get("pos", ""))
    raw_size = raw_info.get("size", "")
    if raw_point:
        lines.append(f"  raw=({raw_point[0]},{raw_point[1]}) {raw_size}")
    else:
        lines.append(f"  raw={raw_info.get('pos', '<unavailable>')} {raw_size}")
else:
    lines.append("  raw=<unavailable>")

if move_info:
    move_size = move_info.get("size")
    move_scale_x = move_info.get("scale_x")
    move_scale_y = move_info.get("scale_y")
    if move_size and move_scale_x and move_scale_y:
        lines.append(f"  move_event={move_size} scale={float(move_scale_x):.2f}x{float(move_scale_y):.2f}")

lines.append("")
lines.append("Scaling:")
if scaling_info:
    mode_label = scaling_mode or "<unknown>"
    if scaling_base is not None:
        lines.append(f"  mode={mode_label} base_scale={scaling_base:.4f}")
    else:
        lines.append(f"  mode={mode_label}")
    if scaling_scale_x is not None and scaling_scale_y is not None:
        lines.append(f"  physical_scale={scaling_scale_x:.3f}x{scaling_scale_y:.3f}")
    if (
        scaling_scaled_w is not None
        and scaling_scaled_h is not None
        and scaling_offset_x is not None
        and scaling_offset_y is not None
    ):
        lines.append(
            "  scaled_canvas={:.1f}x{:.1f} offset=({:.1f},{:.1f})".format(
                scaling_scaled_w,
                scaling_scaled_h,
                scaling_offset_x,
                scaling_offset_y,
            )
        )
    if scaling_overflow_x is not None and scaling_overflow_y is not None:
        overflow_x = "yes" if str(scaling_overflow_x) == "1" else "no"
        overflow_y = "yes" if str(scaling_overflow_y) == "1" else "no"
        lines.append(f"  overflow_x={overflow_x} overflow_y={overflow_y}")
else:
    lines.append("  mode=<unavailable>")

lines.append("")
lines.append("Fonts:")
if (
    scaling_scale_x is not None
    and scaling_scale_y is not None
    and scaling_diag is not None
    and scaling_message is not None
):
    lines.append(f"  scale_x={scaling_scale_x:.2f} scale_y={scaling_scale_y:.2f} diag={scaling_diag:.2f}")
    lines.append(f"  ui_scale={scaling_diag:.2f}")
    lines.append(f"  bounds={min_font:.1f}-{max_font:.1f}")
    lines.append(f"  message={scaling_message:.1f}")
    normal_point = max(min_font, min(max_font, 10.0 * scaling_diag))
    small_point = max(1.0, normal_point - 2.0)
    large_point = max(1.0, normal_point + 2.0)
    huge_point = max(1.0, normal_point + 4.0)
    lines.append(f"  status={normal_point:.1f}")
    lines.append(f"  legacy={normal_point:.1f}")
    lines.append(
        "  legacy presets: S={:.1f} N={:.1f} L={:.1f} H={:.1f}".format(
            small_point, normal_point, large_point, huge_point
        )
    )
else:
    if scaling_scale_x is not None and scaling_scale_y is not None and scaling_diag is not None:
        lines.append(f"  scale_x={scaling_scale_x:.2f} scale_y={scaling_scale_y:.2f} diag={scaling_diag:.2f}")
    else:
        lines.append("  scale_x=<unavailable> scale_y=<unavailable> diag=<unavailable>")
    if scaling_diag is not None:
        lines.append(f"  ui_scale={scaling_diag:.2f}")
    else:
        lines.append("  ui_scale=<unavailable>")
    lines.append(f"  bounds={min_font:.1f}-{max_font:.1f}")
    if scaling_message is not None:
        lines.append(f"  message={scaling_message:.1f}")
    else:
        lines.append("  message=<unavailable>")
    lines.append("  status=<unavailable>")
    lines.append("  legacy=<unavailable>")
    lines.append("  legacy presets: <unavailable>")

title_enabled = bool(settings_data.get("title_bar_enabled", False))
try:
    title_height = int(settings_data.get("title_bar_height", 0))
except (TypeError, ValueError):
    title_height = 0

lines.append("")
lines.append("Settings:")
lines.append(f"  title_bar_compensation={'on' if title_enabled else 'off'} height={title_height}")
applied_line = None
if title_info:
    try:
        applied_offset = int(title_info.get("offset", "0"))
    except (TypeError, ValueError):
        applied_offset = None
    scale_value = title_info.get("scale_y")
    if applied_offset is not None:
        if scale_value:
            try:
                applied_line = f"  applied_offset={applied_offset} scale_y={float(scale_value):.2f}"
            except (TypeError, ValueError):
                applied_line = f"  applied_offset={applied_offset}"
        else:
            applied_line = f"  applied_offset={applied_offset}"
if applied_line is None:
    applied_line = "  applied_offset=<unavailable>"
lines.append(applied_line)

print("\n".join(lines))
"@
    $cmd = $script:PythonCommand.Command
    $cmdArgs = @()
    if ($script:PythonCommand.Args) {
        $cmdArgs += $script:PythonCommand.Args
    }
    $cmdArgs += @("-", $latest, $settingsPath)
    $output = $pyScript | & $cmd @cmdArgs 2>&1
    $status = $LASTEXITCODE
    if ($status -ne 0) {
        Write-Output ("Unable to extract debug overlay information from {0}." -f $latest)
        return
    }
    if ($output) {
        foreach ($line in $output) {
            Write-Output $line
        }
    } else {
        Write-Output ("Unable to extract debug overlay information from {0}." -f $latest)
    }
}
function Print-Notes {
    Print-Header "Notes"
    Write-Output "Share this output when reporting overlay issues. Sensitive data is not collected, but review"
    Write-Output "the log snippet before sharing if you have concerns."
}

Clear-Host
Write-Output "EDMC Modern Overlay - Environment Snapshot"
Write-Output "Generated by collect_overlay_debug_windows.ps1"

Print-SystemInfo
Print-Environment
Print-CommandAvailability
Print-MonitorInfo
Check-RequiredPackages
Check-Virtualenv
Check-PythonModules
Print-WaylandHelpers
Print-DebugOverlaySnapshot
Dump-Json "overlay_settings.json" $settingsPath
Print-EnvOverrides
Dump-Json "port.json" $portPath
if ($ShowLogs) {
    Print-Logs
} else {
    Write-Output ""
    Write-Output "(Overlay client logs omitted; re-run with --show-logs to include them.)"
}
Print-Notes

exit 0
