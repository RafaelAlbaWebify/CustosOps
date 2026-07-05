$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptRoot
$FrontendPath = Join-Path $Root "frontend"
$PackagePath = Join-Path $FrontendPath "package.json"
$PackageLockPath = Join-Path $FrontendPath "package-lock.json"
$HashPath = Join-Path $FrontendPath ".deps_installed.hash"

Set-Location -LiteralPath $FrontendPath

Write-Host ""
Write-Host "Starting CustosOps frontend..."
Write-Host "Frontend path: $FrontendPath"
Write-Host ""

$NpmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue

if (-not $NpmCommand) {
    Write-Host "npm.cmd was not found on PATH."
    Write-Host "Install Node.js LTS, reopen PowerShell, then try again."
    exit 1
}

if (-not (Test-Path -LiteralPath $PackagePath)) {
    Write-Host "Missing frontend package.json: $PackagePath"
    exit 1
}

$HashParts = @((Get-FileHash -LiteralPath $PackagePath -Algorithm SHA256).Hash)

if (Test-Path -LiteralPath $PackageLockPath) {
    $HashParts += (Get-FileHash -LiteralPath $PackageLockPath -Algorithm SHA256).Hash
}

$DependencyHash = ($HashParts -join "-")
$ExistingHash = ""

if (Test-Path -LiteralPath $HashPath) {
    $ExistingHash = (Get-Content -LiteralPath $HashPath -Raw).Trim()
}

$NeedInstall = (-not (Test-Path -LiteralPath (Join-Path $FrontendPath "node_modules"))) -or (-not (Test-Path -LiteralPath $HashPath)) -or ($ExistingHash -ne $DependencyHash)

if ($NeedInstall) {
    Write-Host "Installing or refreshing frontend dependencies..."
    & npm.cmd install

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Frontend dependency installation failed."
        exit 1
    }

    Set-Content -LiteralPath $HashPath -Value $DependencyHash -Encoding ASCII
}
else {
    Write-Host "Frontend dependencies match package files. Skipping npm install."
}

Write-Host ""
Write-Host "Frontend URL: http://localhost:5173"
Write-Host "Press CTRL+C in this window to stop the frontend."
Write-Host ""

& npm.cmd run dev -- --host 127.0.0.1