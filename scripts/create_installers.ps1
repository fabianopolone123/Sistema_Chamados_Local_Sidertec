$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$versionFile = Get-Content "src\chamados\version.py" -Raw
if ($versionFile -notmatch '__version__\s*=\s*"([^"]+)"') {
    throw "Nao foi possivel ler a versao em src\\chamados\\version.py"
}
$userVersion = $Matches[1]

$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $iscc)) {
    $iscc = "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
}
if (-not (Test-Path $iscc)) {
    $iscc = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
}

if (-not (Test-Path $iscc)) {
    throw "Inno Setup nao encontrado. Instale o Inno Setup 6."
}

& $iscc "/DMyAppVersion=$userVersion" "installers\ChamadosUsuario.iss"
& $iscc "installers\ChamadosTI.iss"

Write-Host "Instaladores gerados na pasta dist_installers\\ (Usuario versao $userVersion)"
