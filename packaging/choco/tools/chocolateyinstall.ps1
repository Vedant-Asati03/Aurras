# Chocolatey install script for Aurras
$ErrorActionPreference = 'Stop'

$packageName = 'aurras'
$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"

Write-Host     if ($LASTEXITCODE -eq 0) {
        Write-Host "Aurras installed successfully!" -ForegroundColor Green
        Write-Host "Version: $versionOutput"
        $verificationPassed = $true
    } else {ting Aurras installation..."
Write-Host "Package: $packageName"
Write-Host "Tools directory: $toolsDir"
Write-Host "Current working directory: $(Get-Location)"
Write-Host "PowerShell version: $($PSVersionTable.PSVersion)"

# Get package parameters with error handling
Write-Host "Getting package parameters..."
$packageParameters = @{}
try {
    $packageParameters = Get-PackageParameters
    Write-Host "Package parameters received: $($packageParameters.Keys -join ', ')"
} catch {
    Write-Warning "Could not get package parameters (this is normal outside Chocolatey context): $_"
    # Default parameters for better compatibility
    $packageParameters = @{
        'SkipPythonCheck' = $false
        'IgnoreInstallErrors' = $false
        'PythonTimeout' = 300
    }
}

# Check if Python is available with timeout
Write-Host "Checking Python installation..."
$pythonExe = $null
$timeoutSeconds = if ($packageParameters.PythonTimeout) { $packageParameters.PythonTimeout } else { 300 }
Write-Host "Using timeout: $timeoutSeconds seconds"

try {
    Write-Host "Looking for 'python' command..."
    $pythonExe = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonExe) {
        Write-Host "'python' not found, looking for 'python3'..."
        $pythonExe = Get-Command python3 -ErrorAction SilentlyContinue
    }
    if (-not $pythonExe) {
        Write-Host "Python not found in PATH. Please install Python 3.8+ manually:" -ForegroundColor Yellow
        Write-Host "  Option 1: choco install python312" -ForegroundColor Cyan
        Write-Host "  Option 2: Download from https://python.org" -ForegroundColor Cyan
        Write-Host "  Option 3: Use --params '/SkipPythonCheck' if Python is installed elsewhere" -ForegroundColor Cyan
        
        if ($packageParameters.SkipPythonCheck) {
            Write-Warning "Python not found but SkipPythonCheck specified. Continuing..."
            $pythonExe = @{ Source = "python" }
        } else {
            throw "Python not found in PATH. Install Python first or use --params '/SkipPythonCheck'"
        }
    } else {
        Write-Host "Found Python executable: $($pythonExe.Source)"
        $pythonVersion = & $pythonExe.Source --version 2>&1
        Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
        
        # Also check pip
        Write-Host "Checking pip availability..."
        $pipVersion = & $pythonExe.Source -m pip --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Pip version: $pipVersion" -ForegroundColor Green
        } else {
            Write-Warning "Pip check failed, but continuing..."
        }
    }
} catch {
    Write-Host "Python detection failed: $_" -ForegroundColor Red
    Write-Host "Solutions:" -ForegroundColor Yellow
    Write-Host "  1. Install Python: choco install python312" -ForegroundColor Cyan
    Write-Host "  2. Restart PowerShell after Python installation" -ForegroundColor Cyan
    Write-Host "  3. Use: choco install aurras --params '/SkipPythonCheck'" -ForegroundColor Cyan
    
    if (-not $packageParameters.SkipPythonCheck) {
        Write-Error "Python is required but not found. Use --params '/SkipPythonCheck' to bypass this check."
        throw "Python dependency not satisfied"
    }
}

# Install via pip (uses our Windows wheel with bundled DLL)
Write-Host "Installing Aurras music player..."
try {
    # Determine which Python command to use
    $pythonCmd = if ($pythonExe -and $pythonExe.Source) { $pythonExe.Source } else { "python" }
    Write-Host "Using Python command: $pythonCmd"
    
    # Run pip install with verbose output for debugging
    Write-Host "Running: $pythonCmd -m pip install aurras --upgrade --timeout $timeoutSeconds"
    $pipResult = & $pythonCmd -m pip install aurras --upgrade --timeout $timeoutSeconds 2>&1
    
    # Log the pip output for debugging
    Write-Host "Pip output:"
    $pipResult | ForEach-Object { Write-Host "  $_" }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Pip install returned exit code $LASTEXITCODE"
        Write-Warning "Full pip output: $pipResult"
        if (-not $packageParameters.IgnoreInstallErrors) {
            throw "pip install failed with exit code $LASTEXITCODE"
        }
    } else {
        Write-Host "Pip install completed successfully (exit code 0)" -ForegroundColor Green
    }
    
    # Immediately verify the package was installed
    Write-Host "Checking if package was installed..."
    try {
        $pipShowResult = & $pythonCmd -m pip show aurras 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Package verification successful:" -ForegroundColor Green
            $pipShowResult | ForEach-Object { Write-Host "  $_" }
        } else {
            Write-Warning "Package verification failed - pip show returned exit code $LASTEXITCODE"
            $pipShowResult | ForEach-Object { Write-Warning "  $_" }
        }
    } catch {
        Write-Warning "Could not verify package installation: $_"
    }
} catch {
    Write-Host "Exception during pip install: $_" -ForegroundColor Red
    Write-Host "Exception type: $($_.Exception.GetType().FullName)"
    if ($packageParameters.IgnoreInstallErrors) {
        Write-Warning "Installation may have failed: $_"
        Write-Warning "Continuing anyway due to IgnoreInstallErrors parameter"
    } else {
        Write-Error "Failed to install Aurras via pip: $_"
        throw "Aurras pip installation failed"
    }
}

# Verify installation and ensure PATH is updated
Write-Host "Verifying installation..."

# Get Python Scripts directory and add to PATH if needed
try {
    Write-Host "Determining Python Scripts directory..."
    $pythonScriptsDir = if ($pythonExe -and $pythonExe.Source) {
        & $pythonExe.Source -c "import sys; import os; print(os.path.join(sys.prefix, 'Scripts'))" 2>$null
    } else {
        & python -c "import sys; import os; print(os.path.join(sys.prefix, 'Scripts'))" 2>$null
    }
    
    if ($pythonScriptsDir -and (Test-Path $pythonScriptsDir)) {
        Write-Host "Python Scripts directory: $pythonScriptsDir" -ForegroundColor Green
        
        # List contents of Scripts directory for debugging
        Write-Host "Contents of Scripts directory:"
        Get-ChildItem $pythonScriptsDir | ForEach-Object { Write-Host "  $($_.Name)" }
        
        # Check if Scripts directory is in PATH
        $currentPath = $env:PATH
        if ($currentPath -notlike "*$pythonScriptsDir*") {
            Write-Host "Adding Python Scripts directory to PATH for this session..."
            $env:PATH = "$pythonScriptsDir;$currentPath"
        } else {
            Write-Host "Python Scripts directory already in PATH"
        }
        
        # Also update the PATH for the current process
        $machinePath = [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
        $userPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
        $env:PATH = "$pythonScriptsDir;$machinePath;$userPath"
        Write-Host "Updated PATH for current session"
    } else {
        Write-Warning "Python Scripts directory not found or doesn't exist: $pythonScriptsDir"
    }
} catch {
    Write-Warning "Could not determine Python Scripts directory: $_"
    Write-Host "Exception details: $($_.Exception.Message)"
}

# Try multiple verification methods
$verificationPassed = $false

# Method 1: Try direct aurras command
try {
    Write-Host "Testing direct 'aurras' command..."
    $versionOutput = & aurras --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Aurras installed successfully!" -ForegroundColor Green
        Write-Host "Version: $versionOutput"
        $verificationPassed = $true
    } else {
        throw "aurras --version failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host "Direct 'aurras' command not available, trying alternatives..."
}

# Method 2: Try python -m aurras if direct command failed
if (-not $verificationPassed) {
    try {
        Write-Host "Testing 'python -m aurras' command..."
        if ($pythonExe -and $pythonExe.Source) {
            $versionOutput = & $pythonExe.Source -m aurras --version 2>&1
        } else {
            $versionOutput = & python -m aurras --version 2>&1
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Aurras installed successfully (via python -m)!" -ForegroundColor Green
            Write-Host "Version: $versionOutput"
            Write-Host "Note: Use 'python -m aurras' if direct 'aurras' command doesn't work"
            $verificationPassed = $true
        } else {
            throw "python -m aurras failed with exit code $LASTEXITCODE"
        }
    } catch {
        Write-Warning "Python module execution failed: $_"
    }
}

# Method 3: Check if aurras executable exists in Scripts directory
if (-not $verificationPassed -and $pythonScriptsDir) {
    $aurrasExe = Join-Path $pythonScriptsDir "aurras.exe"
    if (Test-Path $aurrasExe) {
        try {
            Write-Host "Testing aurras executable directly from Scripts directory..."
            $versionOutput = & $aurrasExe --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Aurras executable found and working!" -ForegroundColor Green
                Write-Host "Version: $versionOutput"
                Write-Host "Path: $aurrasExe"
                $verificationPassed = $true
            }
        } catch {
            Write-Warning "Direct executable test failed: $_"
        }
    }
}

# Final verification result
if (-not $verificationPassed) {
    if ($packageParameters.SkipVerification) {
        Write-Warning "Verification skipped due to SkipVerification parameter"
    } else {
        Write-Warning "Installation completed but verification failed"
        Write-Warning "Aurras may still work. Try the following commands manually:"
        Write-Host "Troubleshooting:" -ForegroundColor Yellow
        Write-Host "  1. Try: python -m aurras --version"
        Write-Host "  2. Try: pip show aurras"
        Write-Host "  3. Restart your terminal/PowerShell session"
        Write-Host "  4. Add Python Scripts directory to your PATH manually"
        if ($pythonScriptsDir) {
            Write-Host "     Python Scripts directory: $pythonScriptsDir"
        }
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
