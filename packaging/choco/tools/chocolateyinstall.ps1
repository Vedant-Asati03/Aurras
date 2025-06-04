# Chocolatey install script for Aurras
$ErrorActionPreference = 'Stop'

$packageName = 'aurras'
$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"

# Install via pip (uses our Windows wheel with bundled DLL)
Write-Host "Installing Aurras music player..."
& python -m pip install aurras --upgrade

# Verify installation
Write-Host "Verifying installation..."
try {
    & aurras --version
    Write-Host "✅ Aurras installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎵 Usage:" -ForegroundColor Cyan
    Write-Host "  aurras          # Start CLI mode"
    Write-Host "  aurras-tui      # Start TUI mode"
    Write-Host ""
    Write-Host "📖 Documentation: https://github.com/vedant-asati03/Aurras"
} catch {
    Write-Error "❌ Installation verification failed: $_"
    throw "Aurras installation failed"
}
