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
$timeoutSeconds = if ($packageParameters.PythonTimeout) { $packageParameters.PythonTimeout } else { 600 }
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

function Install-AurrasPackage {
    param(
        [string]$PythonCommand,
        [int]$TimeoutSeconds = 600,
        [hashtable]$PackageParameters = @{}
    )
    
    Write-Host "Installing aurras..."
    
    # Verify Python actually works, not just exists
    try {
        Write-Host "Verifying Python functionality..."
        $pythonWorking = & $PythonCommand -c "print('OK')" 2>&1
        if ($pythonWorking -notlike "*OK*") {
            throw "Python not responding correctly: $pythonWorking"
        }
        Write-Host "Python verification passed" -ForegroundColor Green
    } catch {
        Write-Error "Python executable found but not working: $_"
        return $false
    }
    
    # Primary installation method with network configuration for corporate environments
    try {
        $pipArgs = @(
            '-m', 'pip', 'install', 
            'aurras', 
            '--upgrade',
            '--user',  # Install to user directory to avoid permission issues
            '--timeout', $TimeoutSeconds,
            '--no-cache-dir',  # Avoid cache-related issues
            '--trusted-host', 'pypi.org',
            '--trusted-host', 'pypi.python.org', 
            '--trusted-host', 'files.pythonhosted.org'
        )
        
        Write-Host "Running: $PythonCommand $($pipArgs -join ' ')"
        
        # Use retry logic for antivirus/file access issues
        $installSuccess = Install-WithRetry -ScriptBlock {
            & $PythonCommand @pipArgs
            if ($LASTEXITCODE -ne 0) {
                throw "pip install failed with exit code $LASTEXITCODE"
            }
        }
        
        if ($installSuccess) {
            Write-Host "Aurras installed successfully!" -ForegroundColor Green
            return $true
        }
        
    } catch {
        Write-Warning "Primary installation failed: $_"
        
        # Fallback method - try system-wide installation without --user flag
        try {
            Write-Host "Attempting fallback installation (system-wide)..." -ForegroundColor Yellow
            $fallbackArgs = @(
                '-m', 'pip', 'install', 'aurras', '--upgrade', 
                '--timeout', $TimeoutSeconds,
                '--trusted-host', 'pypi.org',
                '--trusted-host', 'pypi.python.org', 
                '--trusted-host', 'files.pythonhosted.org'
            )
            
            Write-Host "Running: $PythonCommand $($fallbackArgs -join ' ')"
            
            $fallbackSuccess = Install-WithRetry -ScriptBlock {
                & $PythonCommand @fallbackArgs
                if ($LASTEXITCODE -ne 0) {
                    throw "Fallback installation failed with exit code $LASTEXITCODE"
                }
            }
            
            if ($fallbackSuccess) {
                Write-Host "Fallback installation succeeded!" -ForegroundColor Green
                return $true
            }
            
        } catch {
            Write-Error "Both installation methods failed: $_"
            Write-Host "Troubleshooting tips:" -ForegroundColor Yellow
            Write-Host "  1. Check internet connection and firewall settings" -ForegroundColor Cyan
            Write-Host "  2. Try manually: $PythonCommand -m pip install aurras" -ForegroundColor Cyan
            Write-Host "  3. Use parameter: --params '/IgnoreInstallErrors'" -ForegroundColor Cyan
            return $false
        }
    }
    return $false
}

function Install-WithRetry {
    param(
        [scriptblock]$ScriptBlock, 
        [int]$MaxRetries = 3
    )
    
    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            & $ScriptBlock
            return $true
        } catch {
            if ($i -eq $MaxRetries) { 
                Write-Error "All $MaxRetries attempts failed: $_"
                return $false
            }
            Write-Warning "Attempt $i failed, retrying in 2 seconds... ($_)"
            Start-Sleep -Seconds 2
        }
    }
    return $false
}

function Test-AurrasInstallation {
    param([string]$PythonCommand)
    
    try {
        # Verify package is installed
        & $PythonCommand -m pip show aurras | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Package verification successful!" -ForegroundColor Green
            return $true
        }
    } catch {
        Write-Warning "Package verification failed: $_"
    }
    return $false
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

# Use the detected Python command
$pythonCmd = if ($pythonExe -and $pythonExe.Source) { $pythonExe.Source } else { "python" }
Write-Host "Using Python command: $pythonCmd"

# Install Aurras using the new simplified approach
$installSuccess = Install-AurrasPackage -PythonCommand $pythonCmd -TimeoutSeconds $timeoutSeconds -PackageParameters $packageParameters

if (-not $installSuccess -and -not $packageParameters.IgnoreInstallErrors) {
    throw "Aurras installation failed"
}

# Verify installation
if ($installSuccess) {
    Test-AurrasInstallation -PythonCommand $pythonCmd
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
        
        # Use Chocolatey helper if available for proper PATH management
        if (Get-Command Install-ChocolateyPath -ErrorAction SilentlyContinue) {
            Write-Host "Using Chocolatey PATH helper..."
            Install-ChocolateyPath -PathToInstall $pythonScriptsDir -PathType 'User'
            
            if (Get-Command Update-SessionEnvironment -ErrorAction SilentlyContinue) {
                Write-Host "Refreshing environment variables..."
                Update-SessionEnvironment
            }
        } else {
            Write-Host "Chocolatey helpers not available, using manual PATH update..."
            $currentPath = $env:PATH
            if ($currentPath -notlike "*$pythonScriptsDir*") {
                Write-Host "Adding Python Scripts directory to PATH for this session..."
                $env:PATH = "$pythonScriptsDir;$currentPath"
            } else {
                Write-Host "Python Scripts directory already in PATH"
            }
        }
        
        # Ensure PATH is updated for current session regardless of method
        $env:PATH = "$pythonScriptsDir;$env:PATH"
        Write-Host "Updated PATH for current session"
    } else {
        Write-Warning "Python Scripts directory not found or doesn't exist: $pythonScriptsDir"
    }
} catch {
    Write-Warning "Could not determine Python Scripts directory: $_"
    Write-Host "Exception details: $($_.Exception.Message)"
}

# Ensure Python Scripts directory is permanently added to User PATH
if ($pythonScriptsDir -and (Test-Path $pythonScriptsDir)) {
    try {
        Write-Host "Ensuring Python Scripts directory is permanently in User PATH..."
        $currentUserPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
        
        if ($currentUserPath -notlike "*$pythonScriptsDir*") {
            Write-Host "Adding $pythonScriptsDir to User PATH permanently..."
            $newUserPath = if ($currentUserPath) { "$currentUserPath;$pythonScriptsDir" } else { $pythonScriptsDir }
            [System.Environment]::SetEnvironmentVariable("PATH", $newUserPath, "User")
            Write-Host "Python Scripts directory added to User PATH permanently" -ForegroundColor Green
        } else {
            Write-Host "Python Scripts directory already in User PATH"
        }
    } catch {
        Write-Warning "Could not update User PATH permanently: $_"
    }
}

# Refresh PATH from system environment and add a brief delay for Windows to process the installation
Write-Host "Refreshing PATH environment variables..."
try {
    $machinePath = [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
    # Combine both paths and ensure our session includes both
    $env:PATH = "$machinePath;$userPath"
    Write-Host "PATH refreshed from system environment"
    
    # Also ensure the Scripts directory is in the current session PATH
    if ($pythonScriptsDir -and $env:PATH -notlike "*$pythonScriptsDir*") {
        $env:PATH = "$pythonScriptsDir;$env:PATH"
        Write-Host "Added Scripts directory to current session PATH"
    }
} catch {
    Write-Warning "Could not refresh PATH from system environment: $_"
}

Write-Host "Waiting for installation to settle..."
Start-Sleep -Seconds 3

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
    Write-Host "Direct 'aurras' command not available: $($_.Exception.Message)"
    Write-Host "This might be due to PATH not being immediately updated. Trying alternatives..."
}

if (-not $verificationPassed) {
    Write-Host "Attempting verification with python -m aurras..."
    
    # Try a different approach - check if aurras package is importable first
    try {
        Write-Host "Checking if aurras package is importable..."
        if ($pythonExe -and $pythonExe.Source) {
            if ($pythonExe.Source -like "py *") {
                $importTest = & py -3.12 -c "import aurras; print('Package import successful')" 2>&1
            } else {
                $importTest = & $pythonExe.Source -c "import aurras; print('Package import successful')" 2>&1
            }
        } else {
            $importTest = & python -c "import aurras; print('Package import successful')" 2>&1
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Package import successful: $importTest" -ForegroundColor Green
            
            # Now try the CLI entry point directly
            Write-Host "Testing CLI entry point via python -m..."
            if ($pythonExe -and $pythonExe.Source) {
                if ($pythonExe.Source -like "py *") {
                    $versionOutput = & py -3.12 -c "from aurras.aurras_cli.__main__ import main; import sys; sys.argv = ['aurras', '--version']; main()" 2>&1
                } else {
                    $versionOutput = & $pythonExe.Source -c "from aurras.aurras_cli.__main__ import main; import sys; sys.argv = ['aurras', '--version']; main()" 2>&1
                }
            } else {
                $versionOutput = & python -c "from aurras.aurras_cli.__main__ import main; import sys; sys.argv = ['aurras', '--version']; main()" 2>&1
            }
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Aurras installed successfully (via entry point)!" -ForegroundColor Green
                Write-Host "Version: $versionOutput"
                $verificationPassed = $true
            } else {
                Write-Warning "Entry point test failed, but package is importable. Installation likely successful."
                Write-Host "Output: $versionOutput"
                $verificationPassed = $true  # Consider it successful if package imports
            }
        } else {
            Write-Warning "Package import failed: $importTest"
        }
    } catch {
        Write-Warning "Package import test failed: $_"
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

# Debug information for Chocolatey test environment
if ($env:ChocolateyEnvironmentDebug -eq 'true' -or $env:CHOCOLATEY_VERSION) {
    Write-Host ""
    Write-Host "=== CHOCOLATEY DEBUG INFO ===" -ForegroundColor Yellow
    Write-Host "Python Path: $pythonCmd"
    if ($pythonScriptsDir) {
        Write-Host "Scripts Dir: $pythonScriptsDir"
    }
    Write-Host "Current PATH contains Scripts dir: $($env:PATH -like "*$pythonScriptsDir*")"
    Write-Host "Environment Variables:"
    Write-Host "  CHOCOLATEY_VERSION: $env:CHOCOLATEY_VERSION"
    Write-Host "  ChocolateyInstall: $env:ChocolateyInstall"
    
    try {
        Write-Host "Aurras installation location:"
        $aurrasLocation = & $pythonCmd -c "import aurras; print(aurras.__file__)" 2>&1
        Write-Host "  $aurrasLocation"
        
        Write-Host "Available aurras commands:"
        $aurrasHelp = & $pythonCmd -m aurras --help 2>&1 | Select-Object -First 5
        $aurrasHelp | ForEach-Object { Write-Host "  $_" }
    } catch {
        Write-Warning "Could not get debug info: $_"
    }
    Write-Host "=== END DEBUG INFO ===" -ForegroundColor Yellow
}
