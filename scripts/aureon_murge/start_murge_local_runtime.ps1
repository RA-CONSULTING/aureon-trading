param(
  [int]$WebPort = 4173,
  [int]$RuntimePort = 7331,
  [switch]$StartDesktop,
  [switch]$EnableHostTerminal,
  [switch]$EnableSandbox,
  [switch]$EnableProviderApi
)

$ErrorActionPreference = "Stop"
$repo = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$murgeRoot = Join-Path $repo "integrations\aureon_murge"
$webRoot = Join-Path $murgeRoot "web_app"
$runtimeRoot = Join-Path $murgeRoot "runtime"
$desktopRoot = Join-Path $murgeRoot "desktop"
$logRoot = Join-Path $murgeRoot "logs\activation"

New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

function Test-Url {
  param([string]$Url)
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
    return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
  } catch {
    return $false
  }
}

function Start-MurgeNodeService {
  param(
    [string]$Name,
    [string]$WorkingDirectory,
    [string[]]$Arguments,
    [string]$HealthUrl,
    [hashtable]$ExtraEnv
  )

  if (Test-Url $HealthUrl) {
    return [pscustomobject]@{ name = $Name; started = $false; reachable = $true; pid = $null; healthUrl = $HealthUrl }
  }

  foreach ($key in $ExtraEnv.Keys) {
    [Environment]::SetEnvironmentVariable($key, [string]$ExtraEnv[$key], "Process")
  }

  $stdout = Join-Path $logRoot "$Name.out.log"
  $stderr = Join-Path $logRoot "$Name.err.log"
  $proc = Start-Process -FilePath "node" -ArgumentList $Arguments -WorkingDirectory $WorkingDirectory -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr

  $reachable = $false
  for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    if (Test-Url $HealthUrl) {
      $reachable = $true
      break
    }
  }

  return [pscustomobject]@{ name = $Name; started = $true; reachable = $reachable; pid = $proc.Id; healthUrl = $HealthUrl; stdout = $stdout; stderr = $stderr }
}

$baseEnv = @{
  HOST = "127.0.0.1"
  PORT = "$WebPort"
  FLAMEBORN_RUNTIME_HOST = "127.0.0.1"
  FLAMEBORN_RUNTIME_PORT = "$RuntimePort"
  FLAMEBORN_RUNTIME_ALLOW_REMOTE = "false"
  TERMINAL_ALLOW_REMOTE = "false"
  MURGE_HOST_TERMINAL_ENABLED = $(if ($EnableHostTerminal) { "1" } else { "0" })
  MURGE_SANDBOX_ENABLED = $(if ($EnableSandbox) { "1" } else { "0" })
  MURGE_PROVIDER_API_ENABLED = $(if ($EnableProviderApi) { "1" } else { "0" })
  MURGE_CLOUDFLARE_ENABLED = "0"
  FLAMEBORN_DESKTOP_AUTO_AUREON = "false"
  FLAMEBORN_SKIP_AUTO_SERVERS = "true"
}

$runtime = Start-MurgeNodeService -Name "murge-runtime" -WorkingDirectory $murgeRoot -Arguments @("runtime\server.mjs") -HealthUrl "http://127.0.0.1:$RuntimePort/health" -ExtraEnv $baseEnv
$web = Start-MurgeNodeService -Name "murge-web" -WorkingDirectory $webRoot -Arguments @("server.mjs") -HealthUrl "http://127.0.0.1:$WebPort/api/aureon/status" -ExtraEnv $baseEnv

$desktop = $null
if ($StartDesktop) {
  if (-not ($runtime.reachable -and $web.reachable)) {
    throw "Desktop launch blocked: web/runtime health did not pass."
  }
  [Environment]::SetEnvironmentVariable("MURGE_DESKTOP_ENABLED", "1", "Process")
  [Environment]::SetEnvironmentVariable("FLAMEBORN_WEB_URL", "http://127.0.0.1:$WebPort", "Process")
  [Environment]::SetEnvironmentVariable("FLAMEBORN_RUNTIME_URL", "http://127.0.0.1:$RuntimePort", "Process")
  $desktopProc = Start-Process -FilePath "npm" -ArgumentList @("start") -WorkingDirectory $desktopRoot -PassThru -WindowStyle Hidden
  $desktop = [pscustomobject]@{ name = "murge-desktop"; started = $true; pid = $desktopProc.Id }
}

$auditJson = & (Join-Path $repo ".venv\Scripts\python.exe") -m aureon.autonomous.aureon_murge_runtime_activation_stress_audit --json --no-external-fabric

[pscustomobject]@{
  web = $web
  runtime = $runtime
  desktop = $desktop
  audit = ($auditJson | ConvertFrom-Json)
} | ConvertTo-Json -Depth 8
