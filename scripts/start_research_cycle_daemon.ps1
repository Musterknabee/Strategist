# Start 24/7 research cycle daemon (host venv). Logs to artifact_root/research_cycle_scheduler/daemon.log

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$venvPy = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    Write-Error "Missing venv at $venvPy"
}

$hostLib = "C:\var\lib\strategy-validator"
if (-not (Test-Path $hostLib)) {
    New-Item -ItemType Directory -Force -Path $hostLib | Out-Null
}
$art = Join-Path $hostLib "artifacts"
New-Item -ItemType Directory -Force -Path $art | Out-Null

$logDir = Join-Path $art "research_cycle_scheduler"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "daemon.log"

$interval = if ($env:RESEARCH_CYCLE_INTERVAL_SECONDS) { $env:RESEARCH_CYCLE_INTERVAL_SECONDS } else { "3600" }
$heavyEvery = if ($env:RESEARCH_CYCLE_HEAVY_EVERY) { $env:RESEARCH_CYCLE_HEAVY_EVERY } else { "12" }

$args = @(
    "scripts\research_cycle_daemon.py",
    "--artifact-root", $art,
    "--interval-seconds", $interval,
    "--heavy-every", $heavyEvery
)
if ($env:RESEARCH_CYCLE_ALLOW_NETWORK -eq "1") {
    $args += "--allow-network"
}

Write-Host "Starting research cycle daemon (interval=${interval}s, heavy_every=${heavyEvery})"
Write-Host "  log: $log"
Write-Host "  trigger from UI: POST /ui/research-cycle/trigger"

Start-Process -FilePath $venvPy -ArgumentList $args -WindowStyle Hidden -RedirectStandardOutput $log -RedirectStandardError $log

Write-Host "Daemon started. Status: GET http://127.0.0.1:8000/ui/research-cycle/status/latest"
