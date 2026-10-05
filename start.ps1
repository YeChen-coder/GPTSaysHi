param([ValidateSet('chatgpt','classic')][string]$App='chatgpt',[int]$Seconds=1800,[switch]$RecordAudio)
$ErrorActionPreference='Stop'
& (Join-Path $PSScriptRoot 'start_avatar.ps1')
$python=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$bridgeArguments=@((Join-Path $PSScriptRoot 'bridge.py'),'--app',$App,'--seconds',"$Seconds",'--name','manual')
if($RecordAudio) {$bridgeArguments+='--record'}
& $python @bridgeArguments
if($LASTEXITCODE -ne 0) { throw 'Audio capture failed' }
