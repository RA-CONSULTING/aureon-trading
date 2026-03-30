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
    (Join-Path $RepoRoot "aureon\monitors"),
    (Join-Path $RepoRoot "aureon\data_feeds")
)

$existingPythonPath = $env:PYTHONPATH
if ($existingPythonPath) {
    $pythonPathEntries += $existingPythonPath
}
$env:PYTHONPATH = ($pythonPathEntries -join ";")

$scriptPath = Join-Path $RepoRoot "aureon\exchanges\alpaca_capital_runner.py"

Write-Host "Repo root: $RepoRoot"
Write-Host "Python: $PythonExe"
Write-Host "Running Alpaca capital-style trader..."
if ($args -contains "--free-assets" -or $args -contains "--free-assets-only") {
    Write-Host "Free-assets mode enabled."
}

& $PythonExe $scriptPath @args
