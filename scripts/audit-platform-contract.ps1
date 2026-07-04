param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

$Python = Join-Path $Root "backend\.venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\audit_platform_contract.py"

& $Python $Script --root $Root
