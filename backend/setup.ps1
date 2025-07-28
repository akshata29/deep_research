# Deep Research Backend Setup Script
# This script sets up the backend development environment on Windows

param(
    [switch]$SkipVenv,
    [switch]$SkipDeps,
    [switch]$SkipEnv,
    [string]$PythonPath = "python"
)

Write-Host "=== Deep Research Backend Setup ===" -ForegroundColor Cyan

# Check if Python is available
try {
    $pythonVersion = & $PythonPath --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
    
    # Check Python version (should be 3.11+)
    $versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
    if ($versionMatch) {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            Write-Host "Error: Python 3.11 or higher is required. Found: $pythonVersion" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "Error: Python not found. Please install Python 3.11+ or specify path with -PythonPath" -ForegroundColor Red
    exit 1
}

# Create virtual environment
if (-not $SkipVenv) {
    if (-not (Test-Path "venv")) {
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        & $PythonPath -m venv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error: Failed to create virtual environment" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Virtual environment already exists" -ForegroundColor Green
    }

    # Activate virtual environment
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
}

# Install dependencies
if (-not $SkipDeps) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install --upgrade pip
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "Dependencies installed successfully" -ForegroundColor Green
}

# Check for wkhtmltopdf (required for PDF export)
Write-Host "Checking wkhtmltopdf..." -ForegroundColor Yellow
$wkhtmltopdfPaths = @(
    "C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
    "C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe"
)

$wkhtmltopdfFound = $false
foreach ($path in $wkhtmltopdfPaths) {
    if (Test-Path $path) {
        Write-Host "Found wkhtmltopdf at: $path" -ForegroundColor Green
        $wkhtmltopdfFound = $true
        break
    }
}

if (-not $wkhtmltopdfFound) {
    # Try to find in PATH
    try {
        $null = Get-Command wkhtmltopdf -ErrorAction Stop
        Write-Host "Found wkhtmltopdf in PATH" -ForegroundColor Green
        $wkhtmltopdfFound = $true
    } catch {
        Write-Host "wkhtmltopdf not found. PDF export will not work." -ForegroundColor Yellow
        Write-Host "To enable PDF export, download and install wkhtmltopdf from:" -ForegroundColor Yellow
        Write-Host "https://wkhtmltopdf.org/downloads.html" -ForegroundColor Cyan
        Write-Host "Choose the Windows installer (64-bit or 32-bit depending on your system)" -ForegroundColor Gray
    }
}

# Set up environment file
if (-not $SkipEnv) {
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Write-Host "Creating .env file from template..." -ForegroundColor Yellow
            Copy-Item ".env.example" ".env"
            Write-Host "Please update .env with your Azure configuration" -ForegroundColor Yellow
        } else {
            Write-Host "Warning: No .env.example found" -ForegroundColor Yellow
        }
    } else {
        Write-Host ".env file already exists" -ForegroundColor Green
    }
}

# Check Azure CLI
Write-Host "Checking Azure CLI..." -ForegroundColor Yellow
try {
    $azAccount = az account show 2>$null | ConvertFrom-Json
    if ($azAccount) {
        Write-Host "Azure CLI authenticated as: $($azAccount.user.name)" -ForegroundColor Green
    } else {
        Write-Host "Azure CLI not authenticated. Run 'az login' to authenticate" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Azure CLI not found. Please install Azure CLI" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "Next steps:" -ForegroundColor White
Write-Host "1. Update .env with your Azure configuration" -ForegroundColor Gray
Write-Host "2. Run 'az login' if not already authenticated" -ForegroundColor Gray
Write-Host "3. Start the development server:" -ForegroundColor Gray
Write-Host "   python run.py serve" -ForegroundColor White
Write-Host ""
Write-Host "Available commands:" -ForegroundColor White
Write-Host "  python run.py serve     # Start development server" -ForegroundColor Gray
Write-Host "  python run.py test      # Run tests" -ForegroundColor Gray
Write-Host "  python run.py health    # Check system health" -ForegroundColor Gray
Write-Host "  python run.py --help    # Show all commands" -ForegroundColor Gray
