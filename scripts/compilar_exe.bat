@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
title Compilador de Executavel Standalone (.EXE) - Painel de Busca

echo ======================================================================
echo    COMPILADOR DE EXECUTAVEL STANDALONE (.EXE) - PAINEL DE BUSCA
echo ======================================================================
echo   Este script opcional compila o Painel de Busca em um executavel .exe
echo   utilizando PyInstaller para quem prefere rodar sem scripts visiveis.
echo ======================================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [AVISO] Ambiente .venv nao encontrado. Executando INSTALAR_PAINEL.bat primeiro...
    call "INSTALAR_PAINEL.bat"
)

echo [1/3] Verificando instalacao do PyInstaller no ambiente virtual...
".venv\Scripts\python.exe" -m pip install pyinstaller --quiet
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar PyInstaller via pip.
    pause
    exit /b 1
)

echo [2/3] Compilando executavel com icone e arquivos estaticos embutidos...
echo Aguarde, a compilacao leva cerca de 1 a 2 minutos...
echo.

".venv\Scripts\python.exe" -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --name "PainelDeBusca" ^
    --icon "app/static/icon.ico" ^
    --add-data "app/static;app/static" ^
    --hidden-import "uvicorn.logging" ^
    --hidden-import "uvicorn.loops" ^
    --hidden-import "uvicorn.loops.auto" ^
    --hidden-import "uvicorn.protocols" ^
    --hidden-import "uvicorn.protocols.http" ^
    --hidden-import "uvicorn.protocols.http.auto" ^
    --hidden-import "uvicorn.protocols.websockets" ^
    --hidden-import "uvicorn.protocols.websockets.auto" ^
    --hidden-import "uvicorn.lifespans" ^
    --hidden-import "uvicorn.lifespans.on" ^
    --hidden-import "email_validator" ^
    "scripts/launcher_exe.py"

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Aconteceu um erro durante o processo do PyInstaller.
    pause
    exit /b 1
)

echo [3/3] Criando atalho na Area de Trabalho apontando para o executavel...
powershell -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$s = $ws.CreateShortcut([IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'Painel de Busca (EXE).lnk')); " ^
    "$s.TargetPath = [IO.Path]::GetFullPath('dist\\PainelDeBusca\\PainelDeBusca.exe'); " ^
    "$s.WorkingDirectory = [IO.Path]::GetFullPath('dist\\PainelDeBusca'); " ^
    "$s.IconLocation = [IO.Path]::GetFullPath('app\\static\\icon.ico') + ',0'; " ^
    "$s.Save()"

echo.
echo ======================================================================
echo   [SUCESSO] Executavel gerado com sucesso!
echo   Pasta de saida: dist\PainelDeBusca\
echo   Arquivo gerado: dist\PainelDeBusca\PainelDeBusca.exe
echo   Atalho criado no Desktop: 'Painel de Busca (EXE)'
echo ======================================================================
echo.
pause
