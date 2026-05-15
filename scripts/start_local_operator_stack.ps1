# Start production-local operator stack: Docker API + Next.js UI.

# Prerequisites: Docker Desktop, deployment.env (see setup_local_deployment.py), npm in ui/strategist-web.

$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)



if (-not (Test-Path "deployment.env")) {

    Write-Error "Missing deployment.env. Run: python scripts/setup_local_deployment.py --force"

}



$hostLib = "C:\var\lib\strategy-validator"

if (-not (Test-Path $hostLib)) {

    New-Item -ItemType Directory -Force -Path $hostLib | Out-Null

}



docker volume create strategist-local-lib 2>$null | Out-Null

docker volume create strategist-local-backups 2>$null | Out-Null



$existing = docker ps -aq -f name=strategist-local-api

if ($existing) {

    docker rm -f strategist-local-api | Out-Null

}



docker build -t strategist-local -f Dockerfile .

# Bind host production lib so host-run scripts and API share the same artifacts.

docker run -d --name strategist-local-api `

    -p 127.0.0.1:8000:8000 `

    -v "${hostLib}:/var/lib/strategy-validator" `

    -v strategist-local-backups:/var/backups/strategy-validator `

    --env-file deployment.env strategist-local



Write-Host "API: http://127.0.0.1:8000/healthz (wait for healthy)"

Write-Host "Artifacts: $hostLib (shared with host python scripts)"

Write-Host "Verify:  .\.venv\Scripts\python.exe scripts\verify_operator_wiring.py"

Write-Host "Full run: .\.venv\Scripts\python.exe scripts\run_full_operator_spine.py"
Write-Host "24/7:    .\scripts\start_research_cycle_daemon.ps1"

Write-Host "UI:      cd ui\strategist-web; npm run dev"

Write-Host "         http://localhost:3000 (or :3001 — ensure deployment.env CORS lists your port)"

