param(
  [string]$DataRoot = 'D:/lake/content-studio-github-main/runtime-data',
  [string]$PythonPath = '',
  [int]$BackendPort = 8010,
  [int]$UiPort = 3002,
  [switch]$Build
)
$ErrorActionPreference = 'Stop'
$uiRoot = $PSScriptRoot
if (-not $PythonPath) { $PythonPath = Join-Path $uiRoot '.venv/Scripts/python.exe' }
$backendCode = Join-Path $uiRoot 'content-studio/backend'
$backendUrl = "http://127.0.0.1:$BackendPort"
foreach ($required in @($DataRoot, $PythonPath, (Join-Path $DataRoot '.env'), (Join-Path $backendCode 'main.py'))) {
  if (-not (Test-Path -LiteralPath $required)) { throw "Missing required path: $required" }
}

Push-Location $uiRoot
try {
  if ($Build) {
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'UI build failed' }
  }
  if (-not (Test-Path -LiteralPath (Join-Path $uiRoot 'dist/server.cjs'))) { throw 'Run npm run build first' }
  $health = $null
  try { $health = Invoke-RestMethod "$backendUrl/health" -TimeoutSec 2 } catch {}
  if ($health -and $health.ui_compat -ne 2) { throw "Port $BackendPort is occupied by a different backend. Stop it explicitly or choose another BackendPort." }
  if (-not $health) {
    # Code is transplanted into this repository; only runtime data stays at DataRoot.
    $env:FRONTEND_URL = "http://127.0.0.1:$UiPort"
    $env:BACKEND_PUBLIC_URL = $env:FRONTEND_URL
    $backendStdout = Join-Path $DataRoot 'backend.stdout.log'
    $backendStderr = Join-Path $DataRoot 'backend.stderr.log'
    $backendProcess = Start-Process -FilePath $PythonPath -ArgumentList @(
      '-m', 'uvicorn', 'main:app', '--app-dir', $backendCode,
      '--host', '127.0.0.1', '--port', "$BackendPort"
    ) -WorkingDirectory $DataRoot -WindowStyle Hidden -RedirectStandardOutput $backendStdout -RedirectStandardError $backendStderr -PassThru
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
      if ($backendProcess.HasExited) { throw 'FastAPI exited during startup' }
      try { $health = Invoke-RestMethod "$backendUrl/health" -TimeoutSec 2 } catch {}
      if ($health.ui_compat -eq 2) { break }
      Start-Sleep -Milliseconds 500
    }
    if ($health.ui_compat -ne 2) { throw 'FastAPI readiness check failed' }
  }
  $env:PORT = "$UiPort"
  $env:HOST = '127.0.0.1'
  $env:NODE_ENV = 'production'
  $env:BACKEND_URL = $backendUrl
  $uiStdout = Join-Path $DataRoot 'ui.stdout.log'
  $uiStderr = Join-Path $DataRoot 'ui.stderr.log'
  $uiProcess = Start-Process -FilePath 'node' -ArgumentList (Join-Path $uiRoot 'dist/server.cjs') -WorkingDirectory $uiRoot -WindowStyle Hidden -RedirectStandardOutput $uiStdout -RedirectStandardError $uiStderr -PassThru
  $uiReady = $false
  for ($attempt = 0; $attempt -lt 20; $attempt++) {
    if ($uiProcess.HasExited) { break }
    try {
      $uiHealth = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$UiPort/health" -TimeoutSec 2
      if ($uiHealth.StatusCode -eq 200) { $uiReady = $true; break }
    } catch {}
    Start-Sleep -Milliseconds 500
  }
  if (-not $uiReady) {
    $tail = if (Test-Path $uiStderr) { Get-Content $uiStderr -Tail 40 -Raw } else { '' }
    throw "UI gateway failed to start. $tail"
  }
  Write-Host "GitHub UI: http://127.0.0.1:$UiPort"
  Write-Host "FastAPI: http://127.0.0.1:$BackendPort"
  Write-Host "后台进程已启动；日志：$DataRoot"
} finally { Pop-Location }
