@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Painel de Busca e Prospeccao de Leads (Porta 8090)

echo ======================================================================
echo   Painel de Busca, Raio-X das 8 Ferramentas e Central de Leads
echo   Pasta: %CD%
echo ======================================================================

:: ----------------------------------------------------------------------
:: 1. AUTO-CURA: Verifica se o ambiente virtual .venv existe
:: ----------------------------------------------------------------------
if exist ".venv\Scripts\python.exe" goto :VENV_OK

echo.
echo [AVISO] Ambiente virtual .venv nao foi encontrado.
echo Detectamos que este e o primeiro acesso ou o projeto acabou de ser baixado.
echo Iniciando o instalador automatico agora mesmo...
echo.
pause
call "INSTALAR_PAINEL.bat"

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo [ERRO] A instalacao nao foi concluida com sucesso.
    pause
    exit /b 1
)

:VENV_OK
set "PYTHON_RUNNER=.venv\Scripts\python.exe"

:: ----------------------------------------------------------------------
:: 2. Verifica se os modulos essenciais estao instalados
:: ----------------------------------------------------------------------
"%PYTHON_RUNNER%" -c "import uvicorn, fastapi" >nul 2>&1
if %errorlevel% equ 0 goto :DEPS_OK

echo.
echo [AVISO] Dependencias essenciais estao ausentes no .venv.
echo Executando instalacao dos pacotes...
call "INSTALAR_PAINEL.bat"

:DEPS_OK
:: Garante pastas de dados locais
if not exist "data" mkdir "data"
if not exist "data\exports" mkdir "data\exports"

:: ----------------------------------------------------------------------
:: 3. Inicializacao do Servidor Web Local
:: ----------------------------------------------------------------------
echo.
echo [OK] Ambiente validado com sucesso!
echo Iniciando servidor em http://127.0.0.1:8090 ...
echo Pressione Ctrl+C para encerrar quando terminar de usar.
echo ======================================================================
echo.

:: Abre o navegador padrao em segundo plano
start "" "http://127.0.0.1:8090"

:: Roda o servidor local
"%PYTHON_RUNNER%" -m uvicorn app.main:app --host 127.0.0.1 --port 8090 --reload --reload-dir app

if %errorlevel% neq 0 (
    echo.
    echo ======================================================================
    echo [ERRO] O servidor encerrou com codigo de erro %errorlevel%.
    echo Verifique se a porta 8090 ja nao esta em uso por outro programa.
    echo ======================================================================
    pause
)
