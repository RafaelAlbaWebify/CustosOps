param(
    [string]$Root = "C:\Users\ralba\Documents\GitHub\custosops"
)

$Script = Join-Path $Root "scripts\export_redaction_lifecycle_proof_pack.py"
$Python = Join-Path $Root "backend\.venv\Scripts\python.exe"

& $Python $Script --root $Root
