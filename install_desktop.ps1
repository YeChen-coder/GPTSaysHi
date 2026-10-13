param([string]$DesktopPath=[Environment]::GetFolderPath('Desktop'))
$ErrorActionPreference='Stop'
$projectRoot=$PSScriptRoot.Replace('%','%%')
if(-not (Test-Path -LiteralPath $DesktopPath -PathType Container)) { throw 'Desktop directory does not exist.' }
$start=@'
@echo off
setlocal
title Start GPTSaysHi
set "GPTSAYSHI_ROOT=__PROJECT_ROOT__"
if not exist "%GPTSAYSHI_ROOT%\start_avatar.ps1" (
    echo GPTSaysHi project was moved. Run install_desktop.ps1 in its new directory.
    pause
    exit /b 1
)
pushd "%GPTSAYSHI_ROOT%"
powershell.exe -NoProfile -File "%GPTSAYSHI_ROOT%\start_avatar.ps1"
if errorlevel 1 (
    echo GPTSaysHi startup failed.
    popd
    pause
    exit /b 1
)
if /I not "%~1"=="--no-browser" start "" "http://127.0.0.1:19088/"
popd
exit /b 0
'@
$stop=@'
@echo off
setlocal
title Stop GPTSaysHi
set "GPTSAYSHI_ROOT=__PROJECT_ROOT__"
if not exist "%GPTSAYSHI_ROOT%\stop.ps1" (
    echo GPTSaysHi project was moved. Run install_desktop.ps1 in its new directory.
    pause
    exit /b 1
)
pushd "%GPTSAYSHI_ROOT%"
powershell.exe -NoProfile -File "%GPTSAYSHI_ROOT%\stop.ps1"
if errorlevel 1 (
    echo GPTSaysHi shutdown failed.
    popd
    pause
    exit /b 1
)
popd
exit /b 0
'@
foreach($entry in @(@{Name='GPTSaysHi-Start.cmd';Text=$start},@{Name='GPTSaysHi-Stop.cmd';Text=$stop})) {
    $path=Join-Path $DesktopPath $entry.Name
    $content=$entry.Text.Replace('__PROJECT_ROOT__',$projectRoot).Replace("`r`n","`n").Replace("`n","`r`n")+"`r`n"
    [IO.File]::WriteAllText($path,$content,[Text.Encoding]::ASCII)
    Write-Output "Created: $path"
}
