param(
    [Parameter(Mandatory, Position = 0)]
    [string] $ScriptPath,

    [switch] $CompileOnly
)

$ErrorActionPreference = "Stop"

function Test-UsablePythonPath {
    param([string] $Path)

    return $Path -and
        (Test-Path -LiteralPath $Path -PathType Leaf) -and
        $Path -notmatch "(?i)[\\/]Microsoft[\\/]WindowsApps[\\/]"
}

function Get-PythonVersion {
    param([string] $Path)

    $text = (Get-Item -LiteralPath $Path).VersionInfo.ProductVersion
    $match = [regex]::Match($text, "\d+(?:\.\d+){1,3}")
    if ($match.Success) {
        return [version] $match.Value
    }
    return [version] "0.0"
}

function Resolve-PythonExecutable {
    if ($env:KARPATHY_PYTHON) {
        $override = [Environment]::ExpandEnvironmentVariables($env:KARPATHY_PYTHON)
        if (Test-UsablePythonPath $override) {
            return (Resolve-Path -LiteralPath $override).Path
        }
        throw "KARPATHY_PYTHON does not point to a usable Python executable."
    }

    $pathCandidate = Get-Command python.exe -CommandType Application -All -ErrorAction SilentlyContinue |
        ForEach-Object Source |
        Where-Object { Test-UsablePythonPath $_ } |
        Select-Object -First 1
    if ($pathCandidate) {
        return $pathCandidate
    }

    $registryPatterns = @(
        "HKCU:\Software\Python\PythonCore\*\InstallPath",
        "HKLM:\Software\Python\PythonCore\*\InstallPath",
        "HKLM:\Software\WOW6432Node\Python\PythonCore\*\InstallPath"
    )
    $candidates = @(foreach ($pattern in $registryPatterns) {
        Get-ItemProperty -Path $pattern -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.ExecutablePath) {
                $_.ExecutablePath
            }
            elseif ($_.'(default)') {
                Join-Path $_.'(default)' "python.exe"
            }
        }
    })

    $installRoots = @()
    if ($env:LOCALAPPDATA) {
        $installRoots += Join-Path $env:LOCALAPPDATA "Programs\Python"
    }
    if ($env:ProgramFiles) {
        $installRoots += $env:ProgramFiles
    }
    if (${env:ProgramFiles(x86)}) {
        $installRoots += ${env:ProgramFiles(x86)}
    }
    foreach ($root in $installRoots) {
        if (Test-Path -LiteralPath $root -PathType Container) {
            $candidates += @(Get-ChildItem -Path $root -Directory -Filter "Python*" -ErrorAction SilentlyContinue |
                ForEach-Object { Join-Path $_.FullName "python.exe" })
        }
    }

    $selected = $candidates |
        Where-Object { Test-UsablePythonPath $_ } |
        Sort-Object -Unique |
        Sort-Object { Get-PythonVersion $_ } -Descending |
        Select-Object -First 1
    if ($selected) {
        return $selected
    }

    throw "No usable Python installation was found. Set KARPATHY_PYTHON to python.exe."
}

if (-not (Test-Path -LiteralPath $ScriptPath -PathType Leaf)) {
    throw "Hook script was not found: $ScriptPath"
}

$python = Resolve-PythonExecutable
$resolvedScript = (Resolve-Path -LiteralPath $ScriptPath).Path
if ($CompileOnly) {
    & $python -X utf8 -c "import pathlib,sys; path=pathlib.Path(sys.argv[1]); compile(path.read_bytes(), str(path), 'exec')" $resolvedScript
    exit $LASTEXITCODE
}

$payload = [Console]::In.ReadToEnd()
if ($payload) {
    $payload | & $python -X utf8 $resolvedScript
}
else {
    & $python -X utf8 $resolvedScript
}
exit $LASTEXITCODE
