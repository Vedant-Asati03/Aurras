# Chocolatey uninstall script for Aurras
$ErrorActionPreference = 'Stop'

Write-Host "Uninstalling Aurras music player..."

try {
    & python -m pip uninstall aurras -y
    Write-Host "✅ Aurras uninstalled successfully!" -ForegroundColor Green
} catch {
    Write-Warning "Could not uninstall via pip: $_"
    Write-Host "You may need to manually run: pip uninstall aurras"
}
