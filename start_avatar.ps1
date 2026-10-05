$ErrorActionPreference='Stop'
$projectRoot=$PSScriptRoot
$python=Join-Path $projectRoot '.venv\Scripts\python.exe'
if(-not (Test-Path -LiteralPath $python) -or -not (Test-Path -LiteralPath (Join-Path $projectRoot 'ProcessAudio.exe'))) {
    & (Join-Path $projectRoot 'setup.ps1')
}
& $python (Join-Path $projectRoot 'assets.py') --verify
if($LASTEXITCODE -ne 0) { throw 'Avatar assets are incomplete. Run setup.ps1.' }
& docker compose -f (Join-Path $projectRoot 'compose.yaml') up -d --build
if($LASTEXITCODE -ne 0) { throw 'Avatar startup failed. Check Docker Desktop and NVIDIA GPU support.' }
$ready=$false
for($attempt=0;$attempt -lt 90;$attempt++) {
    try {
        $state=Invoke-RestMethod 'http://127.0.0.1:19088/health' -TimeoutSec 2
        if($state.ok -and $state.release -eq '20261004-selected-idle-1-pingpong' -and $state.takeover_policy -eq 'latest_connection') {$ready=$true;break}
    } catch { }
    Start-Sleep -Seconds 2
}
if(-not $ready) { throw 'Avatar did not become ready. Inspect docker compose logs.' }
Write-Output 'GPTSaysHi is ready: http://127.0.0.1:19088/ . Connect a ChatGPT audio source.'
