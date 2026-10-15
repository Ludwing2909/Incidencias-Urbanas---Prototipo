$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Instale el entorno siguiendo README.md.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot '.env'))) { throw 'Primero ejecute scripts/init_env.ps1.' }
Set-Location -LiteralPath $projectRoot
& $pythonPath -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Migración fallida.' }
Write-Output 'API: http://127.0.0.1:8000 · En otra terminal ejecute npm.cmd run dev --prefix frontend'
& $pythonPath -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --no-access-log
