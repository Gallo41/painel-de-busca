<#
.SYNOPSIS
    Script de Sincronização e Commit Automático para o repositório painel-de-busca.
.DESCRIPTION
    Realiza git add, commit com mensagem estruturada/timestamp e push automático para a branch configurada.
    Também pode ser executado em modo contínuo (-Watch) para monitorar alterações em tempo real.
.PARAMETER Message
    Mensagem personalizada para o commit. Se omitida, gera uma mensagem com data/hora e resumo de arquivos.
.PARAMETER Watch
    Ativa o modo contínuo de monitoramento de alterações (daemon de auto-commit).
.PARAMETER IntervalSeconds
    Intervalo em segundos entre verificações quando no modo -Watch (padrão: 30 segundos).
#>
param(
    [string]$Message = "",
    [switch]$Watch,
    [int]$IntervalSeconds = 30
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName

function Sync-GitRepo {
    param([string]$CommitMsg)

    Push-Location $RepoRoot
    try {
        $status = git status --porcelain
        if (-not $status) {
            Write-Host "[Git Auto-Sync] Nenhuma alteracao pendente para commitar." -ForegroundColor Cyan
            return $false
        }

        if (-not $CommitMsg) {
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $changedCount = ($status -split "`n").Count
            $CommitMsg = "auto: sincronizacao automatica ($changedCount arquivo(s)) em $timestamp"
        }

        Write-Host "[Git Auto-Sync] Identificadas alteracoes pendentes..." -ForegroundColor Yellow
        Write-Host "[Git Auto-Sync] Executando: git add -A" -ForegroundColor Gray
        git add -A

        Write-Host "[Git Auto-Sync] Criando commit: '$CommitMsg'" -ForegroundColor Gray
        git commit -m "$CommitMsg"

        Write-Host "[Git Auto-Sync] Sincronizando com GitHub (git push origin HEAD)..." -ForegroundColor Green
        git push origin HEAD

        Write-Host "[Git Auto-Sync] Sincronizacao concluida com sucesso no GitHub!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Warning "[Git Auto-Sync] Erro durante a sincronizacao: $_"
        return $false
    }
    finally {
        Pop-Location
    }
}

if ($Watch) {
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host " [Git Auto-Sync Daemon] Monitoramento ativado para: $RepoRoot" -ForegroundColor Cyan
    Write-Host " Verificando a cada $IntervalSeconds segundos. Pressione Ctrl+C para encerrar." -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan

    while ($true) {
        Sync-GitRepo -CommitMsg ""
        Start-Sleep -Seconds $IntervalSeconds
    }
}
else {
    Sync-GitRepo -CommitMsg $Message
}
