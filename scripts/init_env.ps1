$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath '.env') { throw '.env ya existe; se conserva su contenido.' }
$randomBytes = [byte[]]::new(48)
$secretGenerator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$secretGenerator.GetBytes($randomBytes)
$appSecret = [Convert]::ToBase64String($randomBytes)
$secretGenerator.GetBytes($randomBytes)
$databasePassword = [BitConverter]::ToString($randomBytes).Replace('-', '')
$secretGenerator.Dispose()
$template = Get-Content -LiteralPath '.env.example' -Raw
$envContent = $template.Replace('replace-with-at-least-32-random-characters', $appSecret).Replace('replace-with-random-password', $databasePassword)
[System.IO.File]::WriteAllText((Join-Path (Get-Location).Path '.env'), $envContent, [System.Text.UTF8Encoding]::new($false))
Write-Output '.env creado con secretos aleatorios. No versionarlo.'
