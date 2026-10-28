@echo off
REM Atalho para o script de sincronizacao automatica do Git
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0git-auto-sync.ps1" %*
