Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath (Join-Path $Root 'frontend')

& npm.cmd install
& npm.cmd run dev