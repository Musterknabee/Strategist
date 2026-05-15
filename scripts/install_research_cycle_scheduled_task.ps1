# Register Windows Scheduled Task to start research cycle daemon at logon (24/7 on this machine).

$ErrorActionPreference = "Stop"
$repo = (Split-Path -Parent $PSScriptRoot)
$startScript = Join-Path $repo "scripts\start_research_cycle_daemon.ps1"
$taskName = "StrategistResearchCycleDaemon"

if (-not (Test-Path $startScript)) {
    Write-Error "Missing $startScript"
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$startScript`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Write-Host "Registered scheduled task: $taskName"
Write-Host "Starts at logon via: $startScript"
Write-Host "Remove with: Unregister-ScheduledTask -TaskName $taskName -Confirm:`$false"
