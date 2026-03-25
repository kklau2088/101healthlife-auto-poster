# ============================================================
#  101HealthLife Auto Poster — Windows Task Scheduler Setup
#  Run this script as Administrator in PowerShell
#  Right-click PowerShell -> Run as Administrator
# ============================================================

$TaskName  = "101HealthLife Auto Post"
$PostTime  = "08:00AM"   # Change this if you want a different time

# ── Auto-detect paths ────────────────────────────────────────
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptPath = Join-Path $ScriptDir "main.py"
$PythonPath = (where.exe python 2>$null | Select-Object -First 1)

if (-not $PythonPath) {
    Write-Host ""
    Write-Host "[ERROR] Python not found. Please install Python first." -ForegroundColor Red
    Write-Host "Download: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation."
    pause
    exit 1
}

$PythonPath = $PythonPath.Trim()

if (-not (Test-Path $ScriptPath)) {
    Write-Host ""
    Write-Host "[ERROR] main.py not found at: $ScriptPath" -ForegroundColor Red
    Write-Host "Please run this script from inside the auto-poster folder."
    pause
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  101HealthLife Auto Poster — Scheduler Setup"
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Python path : $PythonPath"
Write-Host "Script path : $ScriptPath"
Write-Host "Working dir : $ScriptDir"
Write-Host "Post time   : $PostTime (daily)"
Write-Host ""

# ── Remove existing task if present ─────────────────────────
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# ── Create new task ──────────────────────────────────────────
$Action   = New-ScheduledTaskAction `
                -Execute $PythonPath `
                -Argument $ScriptPath `
                -WorkingDirectory $ScriptDir

$Trigger  = New-ScheduledTaskTrigger -Daily -At $PostTime

$Settings = New-ScheduledTaskSettingsSet `
                -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
                -RestartCount 3 `
                -RestartInterval (New-TimeSpan -Minutes 5) `
                -StartWhenAvailable        # Run missed task if PC was off at schedule time

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action   $Action `
    -Trigger  $Trigger `
    -Settings $Settings `
    -RunLevel Highest `
    -Force | Out-Null

# ── Verify ───────────────────────────────────────────────────
$info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
$task = Get-ScheduledTask     -TaskName $TaskName -ErrorAction SilentlyContinue

if ($task -and $task.State -ne "Unknown") {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  Scheduler set up successfully!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Task name  : $TaskName"
    Write-Host "  Status     : $($task.State)"
    Write-Host "  Runs daily : $PostTime (Hong Kong time)"
    Write-Host "  Next run   : $($info.NextRunTime)"
    Write-Host ""
    Write-Host "  Useful commands:" -ForegroundColor Cyan
    Write-Host "  Test now   : Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Check info : Get-ScheduledTaskInfo -TaskName '$TaskName'"
    Write-Host "  Disable    : Disable-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Delete     : Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "[ERROR] Task creation may have failed. Please run as Administrator." -ForegroundColor Red
}

pause
