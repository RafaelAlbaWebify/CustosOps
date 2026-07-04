param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

$Script = Join-Path $Root "scripts\export_redaction_lifecycle_proof_pack.py"
$Python = Join-Path $Root "backend\.venv\Scripts\python.exe"

& $Python $Script --root $Root
