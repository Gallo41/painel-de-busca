"""
Launcher executavel standalone para empacotamento com PyInstaller.
Inicia o servidor FastAPI/Uvicorn embutido e abre o navegador automaticamente em http://127.0.0.1:8090.
"""
import os
import sys
import webbrowser
import threading
import time
import multiprocessing
import uvicorn

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8090")

def main():
    multiprocessing.freeze_support()
    
    # Garante pastas de dados locais
    os.makedirs("data", exist_ok=True)
    os.makedirs(os.path.join("data", "exports"), exist_ok=True)
    
    # Thread para abrir o navegador apos o boot
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Importa a app FastAPI do modulo
    from app.main import app
    
    # Roda o servidor local na porta 8090
    uvicorn.run(app, host="127.0.0.1", port=8090, log_level="info")

if __name__ == "__main__":
    main()
