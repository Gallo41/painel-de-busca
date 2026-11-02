# =====================================================================
# Script para Criacao de Atalho na Area de Trabalho (Windows)
# Projeto: Painel de Busca e Prospeccao de Leads
# =====================================================================

param(
    [string]$ShortcutName = "Painel de Busca",
    [switch]$Silent
)

$ErrorActionPreference = "Stop"

try {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    $TargetFile = Join-Path $ProjectRoot "iniciar_painel.bat"
    $IconFile = Join-Path $ProjectRoot "app\static\icon.ico"
    $DesktopPath = [Environment]::GetFolderPath("Desktop")
    $ShortcutPath = Join-Path $DesktopPath "$ShortcutName.lnk"

    if (-not (Test-Path $TargetFile)) {
        throw "Arquivo inicializador nao encontrado em: $TargetFile"
    }

    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $TargetFile
    $Shortcut.WorkingDirectory = $ProjectRoot
    $Shortcut.Description = "Painel de Busca e Prospeccao de Clientes Locais"

    if (Test-Path $IconFile) {
        $Shortcut.IconLocation = "$IconFile,0"
    } else {
        $Shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,22"
    }

    $Shortcut.Save()

    if (-not $Silent) {
        Write-Host ""
        Write-Host "======================================================================" -ForegroundColor Cyan
        Write-Host "  [OK] Atalho criado com sucesso na Area de Trabalho!" -ForegroundColor Green
        Write-Host "  Caminho: $ShortcutPath" -ForegroundColor Gray
        Write-Host "======================================================================" -ForegroundColor Cyan
    }
    exit 0
} catch {
    Write-Warning "Nao foi possivel criar o atalho automaticamente: $_"
    exit 1
}
