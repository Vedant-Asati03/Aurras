# Chocolatey uninstall script for Aurras
$ErrorActionPreference = 'Stop'

Write-Host "Uninstalling Aurras music player..."

$pythonExe = $null
try {
    $pythonExe = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonExe) {
        $pythonExe = Get-Command python3 -ErrorAction SilentlyContinue
    }
} catch {
    Write-Warning "Could not find Python executable"
}

if ($pythonExe) {
    try {
        $uninstallResult = & $pythonExe.Source -m pip uninstall aurras -y 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Aurras uninstalled successfully!" -ForegroundColor Green
        } else {
            Write-Warning "Pip uninstall returned exit code $LASTEXITCODE. Output: $uninstallResult"
        }
    } catch {
        Write-Warning "Could not uninstall via pip: $_"
        Write-Host "You may need to manually run: pip uninstall aurras"
    }
} else {
    Write-Warning "Python not found. Cannot uninstall Aurras via pip."
    Write-Host "If Aurras was installed, you may need to manually run: pip uninstall aurras"
}
