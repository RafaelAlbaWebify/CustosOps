$ErrorActionPreference = "Stop"

function Get-CustosOpsFileSha256 {
    param([Parameter(Mandatory=$true)][string]$Path)

    $GetFileHashCommand = Get-Command Get-FileHash -ErrorAction SilentlyContinue
    if ($GetFileHashCommand) {
        return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
    }

    $Stream = [System.IO.File]::OpenRead($Path)
    try {
        $Sha = [System.Security.Cryptography.SHA256]::Create()
        try {
            $Bytes = $Sha.ComputeHash($Stream)
            return (($Bytes | ForEach-Object { $_.ToString("x2") }) -join '').ToUpperInvariant()
        }
        finally {
            $Sha.Dispose()
        }
    }
    finally {
        $Stream.Dispose()
    }
}

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptRoot
$BackendPath = Join-Path $Root "backend"
$VenvPath = Join-Path $BackendPath ".venv"
$PythonPath = Join-Path $VenvPath "Scripts\python.exe"
$RequirementsPath = Join-Path $BackendPath "requirements.txt"
$HashPath = Join-Path $BackendPath ".deps_installed.hash"

Set-Location -LiteralPath $BackendPath

Write-Host ""
Write-Host "Starting CustosOps backend..."
Write-Host "Backend path: $BackendPath"
Write-Host ""

if (-not (Test-Path -LiteralPath $RequirementsPath)) {
    Write-Host "Missing backend requirements file: $RequirementsPath"
    exit 1
}

if (-not (Test-Path -LiteralPath $PythonPath)) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue

    if (-not $PythonCommand) {
        Write-Host "Python was not found on PATH."
        Write-Host "Install Python 3.11 or newer and enable Add python.exe to PATH, then try again."
        exit 1
    }

    Write-Host "Creating backend virtual environment..."
    python -m venv .venv

    if (-not (Test-Path -LiteralPath $PythonPath)) {
        Write-Host "Backend virtual environment was not created successfully."
        exit 1
    }
}

$RequirementsHash = Get-CustosOpsFileSha256 -Path $RequirementsPath
$ExistingHash = ""

if (Test-Path -LiteralPath $HashPath) {
    $ExistingHash = (Get-Content -LiteralPath $HashPath -Raw).Trim()
}

$NeedInstall = (-not (Test-Path -LiteralPath $HashPath)) -or ($ExistingHash -ne $RequirementsHash)

if ($NeedInstall) {
    Write-Host "Installing or refreshing backend dependencies..."
    & $PythonPath -m pip install -r requirements.txt

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Backend dependency installation failed."
        exit 1
    }

    Set-Content -LiteralPath $HashPath -Value $RequirementsHash -Encoding ASCII
}
else {
    Write-Host "Backend dependencies match requirements.txt. Skipping pip install."
}

Write-Host ""
Write-Host "Checking backend import..."
& $PythonPath -c "from app.main import app; print('backend import ok')"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Backend import failed. Fix the traceback above before launching."
    exit 1
}

Write-Host ""
Write-Host "Backend URL: http://127.0.0.1:8000"
Write-Host "Health URL:  http://127.0.0.1:8000/api/health"
Write-Host "Press CTRL+C in this window to stop the backend."
Write-Host ""

& $PythonPath -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload