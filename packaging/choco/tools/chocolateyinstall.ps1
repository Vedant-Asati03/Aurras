# Chocolatey install script for Aurras
$ErrorActionPreference = 'Stop'

$packageName = 'aurras'
$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"

# Get package parameters
$packageParameters = Get-PackageParameters

# Check if Python is available with timeout
Write-Host "Checking Python installation..."
$pythonExe = $null
$timeoutSeconds = if ($packageParameters.PythonTimeout) { $packageParameters.PythonTimeout } else { 300 }

try {
    $pythonExe = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonExe) {
        $pythonExe = Get-Command python3 -ErrorAction SilentlyContinue
    }
    if (-not $pythonExe) {
        if ($packageParameters.SkipPythonCheck) {
            Write-Warning "Python not found but SkipPythonCheck specified. Continuing..."
            $pythonExe = @{ Source = "python" }
        } else {
            throw "Python not found in PATH"
        }
    } else {
        $pythonVersion = & $pythonExe.Source --version 2>&1
        Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
    }
} catch {
    if (-not $packageParameters.SkipPythonCheck) {
        Write-Error "Python is required but not found. Use --params '/SkipPythonCheck' to bypass this check."
        throw "Python dependency not satisfied"
    }
}

# Install via pip (uses our Windows wheel with bundled DLL)
Write-Host "Installing Aurras music player..."
try {
    if ($pythonExe -and $pythonExe.Source) {
        $pipResult = & $pythonExe.Source -m pip install aurras --upgrade --timeout $timeoutSeconds --quiet 2>&1
    } else {
        $pipResult = & python -m pip install aurras --upgrade --timeout $timeoutSeconds --quiet 2>&1
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Pip install returned exit code $LASTEXITCODE"
        if (-not $packageParameters.IgnoreInstallErrors) {
            throw "pip install failed with exit code $LASTEXITCODE"
        }
    }
    Write-Host "Installation completed"
} catch {
    if ($packageParameters.IgnoreInstallErrors) {
        Write-Warning "Installation may have failed: $_"
        Write-Warning "Continuing anyway due to IgnoreInstallErrors parameter"
    } else {
        Write-Error "Failed to install Aurras via pip: $_"
        throw "Aurras pip installation failed"
    }
}

# Verify installation
Write-Host "Verifying installation..."
try {
    $versionOutput = & aurras --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Aurras installed successfully!" -ForegroundColor Green
        Write-Host "Version: $versionOutput"
    } else {
        throw "aurras --version failed with exit code $LASTEXITCODE"
    }
} catch {
    if ($packageParameters.SkipVerification) {
        Write-Warning "Verification skipped due to SkipVerification parameter"
    } else {
        Write-Warning "Installation completed but verification failed: $_"
        Write-Warning "Aurras may still work. Try running 'aurras --version' manually."
    }
}

Write-Host ""
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  aurras          # Start CLI mode"
Write-Host "  aurras-tui      # Start TUI mode"
Write-Host ""
Write-Host "Documentation: https://github.com/vedant-asati03/Aurras"
Write-Host ""
if ($packageParameters.Count -gt 0) {
    Write-Host "Available parameters for next install:" -ForegroundColor Yellow
    Write-Host "  --params '/SkipPythonCheck /SkipVerification /IgnoreInstallErrors /PythonTimeout:600'"
}
