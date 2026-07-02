param(
    [string]$Root = "C:\Users\ralba\Documents\GitHub\custosops"
)

$Python = Join-Path $Root "backend\.venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\audit_platform_contract.py"

& $Python $Script --root $Root
