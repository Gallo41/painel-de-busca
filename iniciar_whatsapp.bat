@echo off
chcp 65001 >nul
cd /d "%~dp0whatsapp_bridge"
title WhatsApp Bridge - Agente IA (Porta 3100)

echo ======================================================================
echo   WhatsApp Bridge (Baileys) - Conector do Agente IA com QR Code
echo   Pasta: %CD%
echo ======================================================================
echo.

rem Libera a porta 3100 se ja estiver em uso por processo anterior
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 3100 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1

if not exist "node_modules" (
    echo [INFO] Instalando dependencias do conector WhatsApp...
    call npm.cmd install
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar dependencias do Node.js.
        pause
        exit /b 1
    )
)

echo.
echo [OK] Iniciando conector na porta 3100...
echo Se ja estiver conectado, ficara online automaticamente.
echo Se precisar parear, o QR Code aparecera abaixo.
echo ======================================================================
echo.

node server.js
if errorlevel 1 (
    echo.
    echo [ERRO] O servidor encerrou com erro.
    pause
)
pause
