@echo off
title Painel de Busca e Prospeccao de Leads (Porta 8090)
echo ======================================================================
echo   Painel de Busca, Raio-X das 8 Ferramentas e Central de Outreach
echo   Iniciando servidor web local em http://localhost:8090 ...
echo ======================================================================
start "" "http://localhost:8090"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8090 --reload
