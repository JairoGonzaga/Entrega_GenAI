param(
  [ValidateSet('pre-commit', 'pre-push', 'full')]
  [string]$Mode = 'full'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')

function Invoke-External {
  param(
    [Parameter(Mandatory = $true)]
    [scriptblock]$Command
  )

  & $Command
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}

function Resolve-PythonExe {
  $rootVenv = Join-Path $repoRoot '.venv\Scripts\python.exe'
  if (Test-Path $rootVenv) {
    return $rootVenv
  }

  $backendVenv = Join-Path $repoRoot 'backend\.venv\Scripts\python.exe'
  if (Test-Path $backendVenv) {
    return $backendVenv
  }

  if (Get-Command python -ErrorAction SilentlyContinue) {
    return 'python'
  }

  if (Get-Command py -ErrorAction SilentlyContinue) {
    return 'py'
  }

  throw 'Python executable not found. Create/activate .venv or install Python in PATH.'
}

$pythonExe = Resolve-PythonExe

function Invoke-FrontendLint {
  Write-Host '[qa-cli] frontend lint'
  Set-Location (Join-Path $repoRoot 'frontend')
  Invoke-External { corepack pnpm lint }
}

function Invoke-FrontendTests {
  Write-Host '[qa-cli] frontend tests'
  Set-Location (Join-Path $repoRoot 'frontend')
  Invoke-External { corepack pnpm test }
}

function Invoke-FrontendBuild {
  Write-Host '[qa-cli] frontend build'
  Set-Location (Join-Path $repoRoot 'frontend')
  Invoke-External { corepack pnpm build }
}

function Invoke-BackendTests {
  Write-Host '[qa-cli] backend tests'
  Set-Location $repoRoot

  if ($pythonExe -eq 'py') {
    Invoke-External { py -3 -m pytest backend -q }
    return
  }

  Invoke-External { & $pythonExe -m pytest backend -q }
}

switch ($Mode) {
  'pre-commit' {
    Invoke-FrontendLint
    Invoke-BackendTests
  }
  'pre-push' {
    Invoke-FrontendLint
    Invoke-FrontendTests
    Invoke-BackendTests
  }
  'full' {
    Invoke-FrontendLint
    Invoke-FrontendTests
    Invoke-FrontendBuild
    Invoke-BackendTests
  }
}

Write-Host '[qa-cli] done' -ForegroundColor Green