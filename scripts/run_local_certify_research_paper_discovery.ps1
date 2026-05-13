#Requires -Version 5.1
<#
.SYNOPSIS
  Run full Research-and-Paper-Discovery local_certify with clearer exit semantics on Windows.

.DESCRIPTION
  Integrated terminals (including IDE-hosted shells) sometimes stop long jobs before Python exits; the
  process can receive SIGINT even when you did not press Ctrl+C. $LASTEXITCODE may then be -1.
  This script maps -1 to exit 130 (interrupt-style failure) so CI/scripts do not treat the run as success.

  On Windows, local_certify uses CREATE_NO_WINDOW (stdio stays redirected) plus CREATE_BREAKAWAY_FROM_JOB when
  permitted; certification_stability uses the same pattern for pytest children so console control events are less
  likely to surface as KeyboardInterrupt in the parent. The parent Python process can still receive direct signals.

  Usage (from repo root):
    pwsh -File scripts/run_local_certify_research_paper_discovery.ps1
    pwsh -File scripts/run_local_certify_research_paper_discovery.ps1 -SkipJson

  Extra args are forwarded to local_certify.py after the fixed profile flags.
#>
param(
    [switch]$SkipJson,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "python not found on PATH"
    exit 127
}
$python = $pythonCmd.Source

$cmd = @(
    "scripts/local_certify.py"
    "--certify-research-paper-discovery"
)
if (-not $SkipJson) {
    $cmd += "--json"
}
if ($RemainingArgs -and $RemainingArgs.Count -gt 0) {
    $cmd += $RemainingArgs
}

Write-Host ("Running: " + $python + " " + ($cmd -join " "))
& $python @cmd
$code = $LASTEXITCODE

if ($null -eq $code) {
    $code = 0
}

Write-Host "local_certify exit code (raw): $code"

if ($code -eq -1) {
    Write-Host "Shell reported exit code -1 (job stopped or exit not captured). Treating as failure (130)." -ForegroundColor Yellow
    Write-Host "See artifacts/local_certify/latest/local_certify_interrupted.json (interrupt may be host-driven, not Ctrl+C)." -ForegroundColor Yellow
    exit 130
}

exit $code
