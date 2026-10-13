$ErrorActionPreference='Stop'
$projectRoot=$PSScriptRoot
$native=Join-Path $projectRoot 'ProcessAudio.exe'
$nativeProcesses=@(Get-CimInstance Win32_Process -Filter "Name='ProcessAudio.exe'" | Where-Object { $_.ExecutablePath -eq $native })
$bridge=Join-Path $projectRoot 'bridge.py'
$bridgePattern='(?i)(?:^|[\s"])'+[regex]::Escape($bridge)+'(?=$|[\s"])'
Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" | Where-Object { $_.CommandLine -match $bridgePattern } | ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
$nativeProcesses | ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
& docker compose --project-name gptsayshi --project-directory $projectRoot -f (Join-Path $projectRoot 'compose.yaml') down
if($LASTEXITCODE -ne 0) { throw 'GPTSaysHi shutdown failed' }
Write-Output 'GPTSaysHi stopped.'
