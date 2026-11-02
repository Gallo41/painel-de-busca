@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

cd /d "%~dp0"
title Assistente de Instalacao - Painel de Busca

echo ======================================================================
echo           PAINEL DE BUSCA - INSTALADOR 1-CLIQUE (WINDOWS)
echo ======================================================================
echo   Este instalador configura tudo o que voce precisa para usar o painel.
echo   Pasta do projeto: %CD%
echo ======================================================================
echo.

:: ----------------------------------------------------------------------
:: 1. VERIFICACAO DO PYTHON
:: ----------------------------------------------------------------------
echo [Passo 1/4] Verificando instalacao do Python...

set "PYTHON_EXE="

:: Testa o comando 'python'
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
    goto :PYTHON_ENCONTRADO
)

:: Testa o launcher 'py -3'
py -3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=py -3"
    goto :PYTHON_ENCONTRADO
)

:: Se nao encontrou, tenta caminhos padroes no LocalAppData
for %%P in (
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
) do (
    if exist %%P (
        set "PYTHON_EXE=%%~P"
        goto :PYTHON_ENCONTRADO
    )
)

:: Python realmente nao encontrado. Tentar instalar via winget.
echo.
echo [AVISO] Python nao foi localizado no seu sistema.
echo Tentando instalar o Python 3.12 automaticamente via Windows Package Manager (winget)...
echo.

winget --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Baixando e instalando o Python silenciosamente...
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    if %errorlevel% equ 0 (
        echo [OK] Python instalado com sucesso via winget!
        echo Recarregando variaveis de ambiente...
        set "PYTHON_EXE=python"
        goto :PYTHON_ENCONTRADO
    )
)

:: Se winget falhou ou nao existe, orientar o usuario amigavelmente
echo ======================================================================
echo [ERRO] Nao foi possivel instalar o Python automaticamente.
echo.
echo Por favor, faca o seguinte:
echo   1. Acesse: https://www.python.org/downloads/
echo   2. Baixe e execute o instalador do Python.
echo   3. IMPORTANTE: Na primeira tela, marque a caixa:
echo      [X] "Add python.exe to PATH" (Adicionar Python ao PATH)
echo   4. Conclua a instalacao e rode este instalador novamente!
echo ======================================================================
echo.
set /p OPEN_BROWSER="Deseja abrir o site do Python agora no navegador? (S/N): "
if /i "%OPEN_BROWSER%"=="S" (
    start https://www.python.org/downloads/
)
pause
exit /b 1

:PYTHON_ENCONTRADO
echo [OK] Python detectado:
%PYTHON_EXE% --version
echo.

:: ----------------------------------------------------------------------
:: 2. CRIACAO DO AMBIENTE VIRTUAL (.venv)
:: ----------------------------------------------------------------------
echo [Passo 2/4] Configurando ambiente isolado (.venv)...

if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual em .venv ...
    %PYTHON_EXE% -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao criar o ambiente virtual .venv.
        pause
        exit /b 1
    )
    echo [OK] Ambiente virtual criado com sucesso!
) else (
    echo [OK] Ambiente virtual .venv ja existe.
)
echo.

:: ----------------------------------------------------------------------
:: 3. INSTALACAO DAS DEPENDENCIAS
:: ----------------------------------------------------------------------
echo [Passo 3/4] Instalando dependencias do Painel de Busca...
echo Isso pode levar de 30 segundos a 2 minutos na primeira vez...
echo.

".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
if %errorlevel% neq 0 (
    echo [AVISO] Nao foi possivel atualizar o pip, continuando instalacao dos pacotes...
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar as dependencias do requirements.txt.
    echo Verifique sua conexao com a internet e tente novamente.
    pause
    exit /b 1
)

:: Garante pastas de dados
if not exist "data" mkdir "data"
if not exist "data\exports" mkdir "data\exports"

:: Teste rapido de importacao
".venv\Scripts\python.exe" -c "import fastapi, uvicorn, pydantic, httpx; print('[OK] Todas as dependencias foram validadas!')"
if %errorlevel% neq 0 (
    echo [ERRO] Erro na validacao dos modulos essenciais.
    pause
    exit /b 1
)
echo.

:: ----------------------------------------------------------------------
:: 4. CRIACAO DE ATALHO NA AREA DE TRABALHO
:: ----------------------------------------------------------------------
echo [Passo 4/4] Criando atalho na Area de Trabalho...
powershell -ExecutionPolicy Bypass -File "./scripts/criar_atalho.ps1" -Silent
if %errorlevel% equ 0 (
    echo [OK] Atalho "Painel de Busca" criado na sua Area de Trabalho!
) else (
    echo [AVISO] Nao foi possivel criar o atalho automaticamente na Area de Trabalho.
    echo Mas voce pode iniciar direto pelo arquivo "iniciar_painel.bat".
)
echo.

:: ----------------------------------------------------------------------
:: CONCLUSAO COM SUCESSO
:: ----------------------------------------------------------------------
echo ======================================================================
echo    PARABENS! O PAINEL DE BUSCA FOI INSTALADO COM SUCESSO!
echo ======================================================================
echo.
echo   Como usar no dia a dia:
echo   - De dois cliques no atalho "Painel de Busca" na Area de Trabalho
echo     ou de dois cliques em "iniciar_painel.bat" nesta pasta.
echo   - O painel abrira automaticamente em: http://127.0.0.1:8090
echo ======================================================================
echo.

set /p START_NOW="Deseja abrir o Painel de Busca agora? (S/N) [S]: "
if "%START_NOW%"=="" set "START_NOW=S"
if /i "%START_NOW%"=="S" (
    echo Iniciando o painel...
    start "" "iniciar_painel.bat"
)

echo.
echo Pressione qualquer tecla para fechar esta janela.
pause >nul
exit /b 0
