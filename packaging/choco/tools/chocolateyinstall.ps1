$ErrorActionPreference = 'Stop'

$packageName = 'aurras'
$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"

Write-Host "Starting Aurras installation..."
Write-Host "Package: $packageName"
Write-Host "Tools directory: $toolsDir"
Write-Host "Current working directory: $(Get-Location)"
Write-Host "PowerShell version: $($PSVersionTable.PSVersion)"

$packageParameters = @{}
try {
    $packageParameters = Get-PackageParameters
    Write-Host "Package parameters received: $($packageParameters.Keys -join ', ')"
} catch {
    Write-Warning "Could not get package parameters (this is normal outside Chocolatey context): $_"
    $packageParameters = @{
        'SkipPythonCheck' = $false
        'IgnoreInstallErrors' = $false
        'PythonTimeout' = 300
    }
}

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
        Write-Host "'python3' not found, looking for 'py'..."
        $pythonExe = Get-Command py -ErrorAction SilentlyContinue
    }
    if (-not $pythonExe) {
        Write-Host "Trying Python launcher with specific version..."
        $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
        if ($pyLauncher) {
            try {
                $versionCheck = & py -3.12 --version 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "Found Python 3.12 via launcher"
                    $pythonExe = @{ Source = "py -3.12" }
                }
            } catch {
                Write-Host "Python launcher check failed: $_"
            }
        }
    }
    if (-not $pythonExe) {
        Write-Host "Standard Python commands not found. Checking Python installation paths..."
        
        $commonPaths = @(
            "${env:ProgramFiles}\Python312\python.exe",
            "${env:ProgramFiles(x86)}\Python312\python.exe",
            "${env:LOCALAPPDATA}\Programs\Python\Python312\python.exe",
            "${env:LOCALAPPDATA}\Programs\Python\Python312-32\python.exe",
            "$env:ProgramData\chocolatey\lib\python312\tools\python.exe",
            "${env:ProgramFiles}\Python\Python312\python.exe"
        )
        
        foreach ($path in $commonPaths) {
            if (Test-Path $path) {
                Write-Host "Found Python at: $path"
                $pythonExe = @{ Source = $path }
                break
            }
        }
    }
    
    if (-not $pythonExe) {
        Write-Host "Python not found in PATH or common locations." -ForegroundColor Yellow
        Write-Host "Note: python312 should be installed as a dependency." -ForegroundColor Cyan
        Write-Host "If you see this message, there may be an issue with the Python dependency installation." -ForegroundColor Yellow
        
        if ($packageParameters.SkipPythonCheck) {
            Write-Warning "Python not found but SkipPythonCheck specified. Continuing..."
            $pythonExe = @{ Source = "python" }
        } else {
            Write-Warning "Python not found. This is unexpected since python312 is a dependency."
            Write-Host "Attempting to continue anyway..." -ForegroundColor Yellow
            $pythonExe = $null
        }
    } else {
        Write-Host "Found Python executable: $($pythonExe.Source)"
        $pythonVersion = & $pythonExe.Source --version 2>&1
        Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
        
        # Verify Python version is 3.12+
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $majorVersion = [int]$matches[1]
            $minorVersion = [int]$matches[2]
            if ($majorVersion -lt 3 -or ($majorVersion -eq 3 -and $minorVersion -lt 12)) {
                Write-Warning "Found Python $($matches[0]), but Python 3.12+ is recommended for Aurras"
                Write-Host "Continuing anyway, but you may encounter compatibility issues..." -ForegroundColor Yellow
            } else {
                Write-Host "Python version check passed: $($matches[0])" -ForegroundColor Green
            }
        } else {
            Write-Warning "Could not parse Python version from: $pythonVersion"
        }
        
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
    Write-Host "  1. Restart PowerShell session" -ForegroundColor Cyan
    Write-Host "  2. Check if python312 dependency installed correctly" -ForegroundColor Cyan
    Write-Host "  3. Use: choco install aurras --params '/SkipPythonCheck'" -ForegroundColor Cyan
    
    if (-not $packageParameters.SkipPythonCheck) {
        Write-Warning "Python detection failed. Attempting to continue anyway..."
        Write-Host "Installation may fail if Python is not available." -ForegroundColor Yellow
        $pythonExe = $null
    }
}

Write-Host "Installing Aurras music player..."

if (-not $pythonExe -and -not $packageParameters.SkipPythonCheck) {
    Write-Host "Python is not available. Cannot install Aurras via pip." -ForegroundColor Red
    Write-Host ""
    Write-Host "UNEXPECTED: python312 should have been installed as a dependency." -ForegroundColor Yellow
    Write-Host "This suggests an issue with dependency resolution." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "SOLUTIONS:" -ForegroundColor Yellow
    Write-Host "  Step 1: Restart PowerShell session to refresh PATH" -ForegroundColor Cyan
    Write-Host "  Step 2: Try manually: choco install python312" -ForegroundColor Cyan
    Write-Host "  Step 3: Then retry: choco install aurras" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or try: choco install aurras --params '/SkipPythonCheck'" -ForegroundColor Gray
    throw "Python dependency not satisfied. Please install Python first."
}

try {
    # Use the detected Python command (could be python, python3, py, py -3.12, or full path)
    $pythonCmd = if ($pythonExe -and $pythonExe.Source) { $pythonExe.Source } else { "python" }
    Write-Host "Using Python command: $pythonCmd"
    
    Write-Host "Running: $pythonCmd -m pip install aurras --upgrade --timeout $timeoutSeconds"
    $pipResult = & $pythonCmd -m pip install aurras --upgrade --timeout $timeoutSeconds 2>&1
    
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

Write-Host "Verifying installation..."

try {
    Write-Host "Determining Python Scripts directory..."
    $pythonScriptsDir = $null
    
    if ($pythonExe -and $pythonExe.Source) {
        # Handle Python launcher commands differently
        if ($pythonExe.Source -like "py *") {
            $pythonScriptsDir = & py -3.12 -c "import sys; import os; print(os.path.join(sys.prefix, 'Scripts'))" 2>$null
        } else {
            $pythonScriptsDir = & $pythonExe.Source -c "import sys; import os; print(os.path.join(sys.prefix, 'Scripts'))" 2>$null
        }
    } else {
        $pythonScriptsDir = & python -c "import sys; import os; print(os.path.join(sys.prefix, 'Scripts'))" 2>$null
    }
    
    if (-not $pythonScriptsDir -or -not (Test-Path $pythonScriptsDir)) {
        Write-Host "Could not determine Scripts directory from Python. Trying common locations..."
        $commonScriptsPaths = @(
            "${env:ProgramFiles}\Python312\Scripts",
            "${env:ProgramFiles(x86)}\Python312\Scripts",
            "${env:LOCALAPPDATA}\Programs\Python\Python312\Scripts",
            "${env:LOCALAPPDATA}\Programs\Python\Python312-32\Scripts",
            "$env:ProgramData\chocolatey\lib\python312\tools\Scripts",
            "${env:ProgramFiles}\Python\Python312\Scripts"
        )
        
        foreach ($path in $commonScriptsPaths) {
            if (Test-Path $path) {
                Write-Host "Found Scripts directory at: $path"
                $pythonScriptsDir = $path
                break
            }
        }
    }
    
    if ($pythonScriptsDir -and (Test-Path $pythonScriptsDir)) {
        Write-Host "Python Scripts directory: $pythonScriptsDir" -ForegroundColor Green
        
        Write-Host "Contents of Scripts directory:"
        Get-ChildItem $pythonScriptsDir | ForEach-Object { Write-Host "  $($_.Name)" }
        
        $currentPath = $env:PATH
        if ($currentPath -notlike "*$pythonScriptsDir*") {
            Write-Host "Adding Python Scripts directory to PATH for this session..."
            $env:PATH = "$pythonScriptsDir;$currentPath"
        } else {
            Write-Host "Python Scripts directory already in PATH"
        }
        
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

$verificationPassed = $false

try {
    Write-Host "Testing direct 'aurras' command..."
    $versionOutput = & aurras --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Aurras installed successfully!" -ForegroundColor Green
        Write-Host "Version: $versionOutput"
        $verificationPassed = $true
    } else {
        throw "aurras --version failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host "Direct 'aurras' command not available, trying alternatives..."
}

if (-not $verificationPassed) {
    try {
        Write-Host "Testing 'python -m aurras' command..."
        if ($pythonExe -and $pythonExe.Source) {
            # Handle Python launcher commands
            if ($pythonExe.Source -like "py *") {
                $versionOutput = & py -3.12 -m aurras --version 2>&1
            } else {
                $versionOutput = & $pythonExe.Source -m aurras --version 2>&1
            }
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
Write-Host "  aurras"
Write-Host "  aurras-tui"
Write-Host ""
Write-Host "Documentation: https://github.com/vedant-asati03/Aurras"
Write-Host ""
if ($packageParameters.Count -gt 0) {
    Write-Host "Available parameters for next install:" -ForegroundColor Yellow
    Write-Host "  --params '/SkipPythonCheck /SkipVerification /IgnoreInstallErrors /PythonTimeout:600'"
}
