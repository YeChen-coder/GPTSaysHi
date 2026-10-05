$ErrorActionPreference='Stop'
$projectRoot=$PSScriptRoot
$native=Join-Path $projectRoot 'ProcessAudio.exe'
Get-CimInstance Win32_Process -Filter "Name='ProcessAudio.exe'" | Where-Object { $_.ExecutablePath -eq $native } | ForEach-Object { Stop-Process -Id $_.ProcessId }
& docker compose -f (Join-Path $projectRoot 'compose.yaml') down
if($LASTEXITCODE -ne 0) { throw 'GPTSaysHi shutdown failed' }
Write-Output 'GPTSaysHi stopped.'
