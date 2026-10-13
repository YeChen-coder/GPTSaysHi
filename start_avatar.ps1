$ErrorActionPreference='Stop'
$projectRoot=$PSScriptRoot
$python=Join-Path $projectRoot '.venv\Scripts\python.exe'
if(-not (Test-Path -LiteralPath $python) -or -not (Test-Path -LiteralPath (Join-Path $projectRoot 'ProcessAudio.exe'))) {
    & (Join-Path $projectRoot 'setup.ps1')
}
$characterJson=& $python (Join-Path $projectRoot 'characters.py')
if($LASTEXITCODE -ne 0) { throw 'Invalid GPTSAYSHI_CHARACTER. Use gentleman or QinChe.' }
$character=$characterJson | ConvertFrom-Json
& $python (Join-Path $projectRoot 'assets.py')
if($LASTEXITCODE -ne 0) { throw 'Selected avatar assets could not be installed. Run setup.ps1.' }
& docker compose --project-directory $projectRoot -f (Join-Path $projectRoot 'compose.yaml') up -d --build
if($LASTEXITCODE -ne 0) { throw 'Avatar startup failed. Check Docker Desktop and NVIDIA GPU support.' }
$ready=$false
for($attempt=0;$attempt -lt 90;$attempt++) {
    try {
        $state=Invoke-RestMethod 'http://127.0.0.1:19088/health' -TimeoutSec 2
        if($state.ok -and $state.character -eq $character.name -and $state.release -eq $character.release -and $state.takeover_policy -eq 'latest_connection') {$ready=$true;break}
    } catch { }
    Start-Sleep -Seconds 2
}
if(-not $ready) { throw 'Avatar did not become ready. Inspect docker compose logs.' }
Write-Output "GPTSaysHi is ready ($($character.name)): http://127.0.0.1:19088/ . Connect a ChatGPT audio source."
