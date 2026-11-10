@echo off
chcp 65001 >nul
cd /d "%~dp0whatsapp_bridge"
title WhatsApp Bridge - Agente IA (Porta 3100)

echo ======================================================================
echo   WhatsApp Bridge (Baileys) - Conector do Agente IA com QR Code
echo   Pasta: %CD%
echo ======================================================================
echo.

if not exist "node_modules" (
    echo [INFO] Instalando dependencias do conector WhatsApp...
    call npm.cmd install
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao instalar dependencias do Node.js.
        pause
        exit /b 1
    )
)

echo.
echo [OK] Iniciando conector na porta 3100...
echo O QR Code aparecera abaixo para escanear com o WhatsApp.
echo ======================================================================
echo.

call npm.cmd start
pause
