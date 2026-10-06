$ErrorActionPreference = "Continue"
Write-Host "Python:" (Get-Command python -ErrorAction SilentlyContinue).Source
Write-Host "PowerShell:" (Get-Command powershell -ErrorAction SilentlyContinue).Source
Write-Host "pwsh:" (Get-Command pwsh -ErrorAction SilentlyContinue).Source
Write-Host "WSL:" (Get-Command wsl -ErrorAction SilentlyContinue).Source
Write-Host "ADB:" (Get-Command adb -ErrorAction SilentlyContinue).Source
Write-Host "Git:" (Get-Command git -ErrorAction SilentlyContinue).Source
Write-Host "GGDV_MOTOR_ENABLE=$env:GGDV_MOTOR_ENABLE"
Write-Host "GGDV_APP_ADAPTER=$env:GGDV_APP_ADAPTER"
