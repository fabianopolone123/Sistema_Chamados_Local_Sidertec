param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt

& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name ChamadosTI `
  --paths src `
  run_ti.py

Write-Host "Build concluido: dist\\ChamadosTI\\ChamadosTI.exe"
