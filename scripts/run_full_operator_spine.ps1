# Full paper-only operator spine: all example strategy batches + provider loop + runtime demo + operator run.
# Uses one-shot `docker run --rm` with repo + durable volumes (avoids slow `docker exec` on some Windows hosts).
$ErrorActionPreference = "Continue"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo

if (-not (Test-Path "deployment.env")) {
    Write-Error "Missing deployment.env"
}

$image = "strategist-local"
$art = "/var/lib/strategy-validator/artifacts"
$app = "/app"

function Invoke-SpineCli {
    param([string]$Label, [string[]]$Cmd)
    Write-Host "`n=== $Label ===" -ForegroundColor Cyan
    docker run --rm `
        -v "${repo}:${app}:ro" `
        -v strategist-local-lib:/var/lib/strategy-validator `
        -v strategist-local-backups:/var/backups/strategy-validator `
        --env-file deployment.env `
        -w $app `
        $image @Cmd
    $code = $LASTEXITCODE
    if ($code -ne 0) { Write-Host "WARN: exit $code" -ForegroundColor Yellow }
    return $code
}

Write-Host "Building image if needed ..."
docker build -t $image -f Dockerfile . 2>&1 | Out-Host
docker volume create strategist-local-lib 2>$null | Out-Null
docker volume create strategist-local-backups 2>$null | Out-Null

$batchDir = "$app/configs/strategy_batches"
$batches = @(
    "example_batch.json",
    "example_gauntlet_batch.json",
    "example_local_bars_batch.json",
    "example_mean_reversion_batch.json",
    "example_market_structure_batch.json",
    "example_candlestick_volume_batch.json",
    "example_price_volume_batch.json",
    "example_chart_pattern_batch.json",
    "example_advanced_technical_batch.json",
    "example_provider_snapshot_batch.json"
)

$failures = @()
foreach ($name in $batches) {
    $runId = "full-" + ($name -replace '\.json$','' -replace 'example_','')
    $code = Invoke-SpineCli "batch $name" @(
        "strategy-validator-strategy-batch-run",
        "--batch", "$batchDir/$name",
        "--output-root", "$art/strategy_runs",
        "--run-id", $runId,
        "--overwrite",
        "--json"
    )
    if ($code -ne 0) { $failures += "batch:$name" }
}

$code = Invoke-SpineCli "provider paper loop" @(
    "strategy-validator-provider-paper-loop",
    "--artifact-root", $art,
    "--run-id", "full-provider-paper",
    "--fixture-provider-snapshot", "$app/tests/fixtures/provider_snapshots/demo_provider_bars_manifest.json",
    "--batch-spec", "$batchDir/example_provider_snapshot_batch.json",
    "--allow-network",
    "--allow-broker-network",
    "--overwrite",
    "--json"
)
if ($code -ne 0) { $failures += "provider-paper-loop" }

Invoke-SpineCli "paper broker status" @(
    "strategy-validator-paper-broker", "status",
    "--output-root", "$art/paper_broker",
    "--allow-network",
    "--json"
) | Out-Null

$code = Invoke-SpineCli "research os runtime (full cycle)" @(
    "strategy-validator-research-os-runtime-demo",
    "--artifact-root", $art,
    "--run-id", "full-runtime",
    "--batch-spec", "$batchDir/example_gauntlet_batch.json",
    "--full-research-os-cycle",
    "--allow-synthetic-demo",
    "--overwrite",
    "--skip-benchmark",
    "--json"
)
if ($code -ne 0) { $failures += "runtime-demo" }

$code = Invoke-SpineCli "research os operator run" @(
    "strategy-validator-research-os-run", "run",
    "--artifact-root", $art,
    "--repo-root", $app,
    "--run-id", "full-operator",
    "--overwrite",
    "--json"
)
if ($code -ne 0) { $failures += "operator-run" }

# Ensure API container serves the volume (recreate if missing)
$apiId = docker ps -q -f "name=strategist-local-api" 2>$null
if (-not $apiId) {
    Write-Host "Starting API container ..."
    docker rm -f strategist-local-api 2>$null | Out-Null
    docker run -d --name strategist-local-api `
        -p 127.0.0.1:8000:8000 `
        -v strategist-local-lib:/var/lib/strategy-validator `
        -v strategist-local-backups:/var/backups/strategy-validator `
        --env-file deployment.env $image | Out-Null
    Start-Sleep -Seconds 8
}

Write-Host "`n=== API summary ===" -ForegroundColor Cyan
try {
    $batch = Invoke-RestMethod -Uri "http://127.0.0.1:8000/ui/strategy-batches/latest" -TimeoutSec 60
    Write-Host "Latest batch:" $batch.latest.batch_id "/" $batch.latest.run_id "count:" $batch.latest.strategy_count
} catch { Write-Host "API read failed: $_" -ForegroundColor Yellow }

if ($failures.Count -gt 0) {
    Write-Host "Done with failures: $($failures -join ', ')" -ForegroundColor Yellow
    exit 1
}
Write-Host "Full operator spine completed." -ForegroundColor Green
