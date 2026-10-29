@echo off
cd /d "%~dp0"
title Painel de Busca e Prospeccao de Leads (Porta 8090)
echo ======================================================================
echo   Painel de Busca, Raio-X das 8 Ferramentas e Central de Outreach
echo   Diretorio: %CD%
echo   Iniciando servidor web local em http://127.0.0.1:8090 ...
echo ======================================================================
start "" "http://127.0.0.1:8090"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8090 --reload --reload-dir app
