Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $repoRoot

git config core.hooksPath .githooks

Write-Host 'Git hooks path configured to .githooks' -ForegroundColor Green
Write-Host 'Now pre-commit and pre-push are enabled via scripts/qa-cli.sh.' -ForegroundColor Green