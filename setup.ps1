$ErrorActionPreference='Stop'
$projectRoot=$PSScriptRoot
$python=Join-Path $projectRoot '.venv\Scripts\python.exe'
if(-not (Test-Path -LiteralPath $python)) {
    & python -m venv (Join-Path $projectRoot '.venv')
    if($LASTEXITCODE -ne 0) { throw 'Python environment creation failed. Install Python 3.11 or newer.' }
}
& $python -m pip install -r (Join-Path $projectRoot 'requirements.txt')
if($LASTEXITCODE -ne 0) { throw 'Audio bridge dependency installation failed' }
& $python (Join-Path $projectRoot 'assets.py')
if($LASTEXITCODE -ne 0) { throw 'Avatar asset installation failed' }
$compiler='C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$native=Join-Path $projectRoot 'ProcessAudio.exe'
$source=Join-Path $projectRoot 'ProcessAudio.cs'
if(-not (Test-Path -LiteralPath $native) -or (Get-Item $source).LastWriteTimeUtc -gt (Get-Item $native).LastWriteTimeUtc) {
    & $compiler /nologo /platform:x64 /target:exe "/out:$native" $source
    if($LASTEXITCODE -ne 0) { throw 'Native capture helper compilation failed. Stop an active capture before rebuilding.' }
}
Write-Output 'GPTSaysHi setup completed.'
