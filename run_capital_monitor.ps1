$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    throw "Python venv not found at $PythonExe"
}

$pythonPathEntries = @(
    $RepoRoot,
    (Join-Path $RepoRoot "aureon\core"),
    (Join-Path $RepoRoot "aureon\exchanges"),
    (Join-Path $RepoRoot "aureon\data_feeds")
)

$existingPythonPath = $env:PYTHONPATH
if ($existingPythonPath) {
    $pythonPathEntries += $existingPythonPath
}
$env:PYTHONPATH = ($pythonPathEntries -join ";")

$scriptPath = Join-Path $RepoRoot "aureon\exchanges\capital_market_monitor.py"

Write-Host "Repo root: $RepoRoot"
Write-Host "Python: $PythonExe"
Write-Host "Running Capital universe/monitor cache..."

& $PythonExe $scriptPath @args
