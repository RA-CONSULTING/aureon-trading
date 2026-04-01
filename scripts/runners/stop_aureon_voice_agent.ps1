$RepoRoot = "C:\Users\ayman kattan\aureon-trading"
$stateDir = Join-Path $RepoRoot "state"
$stopFile = Join-Path $stateDir "aureon_voice_agent.stop"
$lockFile = Join-Path $stateDir "aureon_voice_agent_supervisor.lock"

$null = New-Item -ItemType Directory -Force -Path $stateDir
Set-Content -Path $stopFile -Value "STOP" -Encoding ascii

if (Test-Path $lockFile) {
    Write-Output "Stop requested. Supervisor will exit."
} else {
    Write-Output "Stop file written. No active supervisor lock found."
}
