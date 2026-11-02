import os
import pathlib

def test_installer_assets_exist():
    root = pathlib.Path(__file__).parent.parent
    
    # 1. Scripts e guias essenciais
    assert (root / "INSTALAR_PAINEL.bat").exists(), "INSTALAR_PAINEL.bat deve existir na raiz"
    assert (root / "iniciar_painel.bat").exists(), "iniciar_painel.bat deve existir na raiz"
    assert (root / "COMO_INSTALAR.txt").exists(), "COMO_INSTALAR.txt deve existir na raiz"
    assert (root / "docs" / "guia-instalacao-amigo.md").exists(), "docs/guia-instalacao-amigo.md deve existir"
    
    # 2. Icone multi-resolucao e scripts utilitarios
    icon_file = root / "app" / "static" / "icon.ico"
    assert icon_file.exists(), "app/static/icon.ico deve existir"
    assert icon_file.stat().st_size > 1000, "app/static/icon.ico deve ter conteudo valido"
    
    assert (root / "scripts" / "criar_atalho.ps1").exists(), "scripts/criar_atalho.ps1 deve existir"
    assert (root / "scripts" / "compilar_exe.bat").exists(), "scripts/compilar_exe.bat deve existir"
    assert (root / "scripts" / "launcher_exe.py").exists(), "scripts/launcher_exe.py deve existir"

def test_installer_scripts_contain_key_routines():
    root = pathlib.Path(__file__).parent.parent
    
    # Valida INSTALAR_PAINEL.bat
    install_bat = (root / "INSTALAR_PAINEL.bat").read_text(encoding="utf-8", errors="ignore")
    assert "chcp 65001" in install_bat
    assert ".venv" in install_bat
    assert "requirements.txt" in install_bat
    assert "criar_atalho.ps1" in install_bat
    
    # Valida auto-cura no iniciar_painel.bat
    init_bat = (root / "iniciar_painel.bat").read_text(encoding="utf-8", errors="ignore")
    assert "INSTALAR_PAINEL.bat" in init_bat
    assert "uvicorn" in init_bat
    assert "http://127.0.0.1:8090" in init_bat

def test_gitignore_protects_binaries_and_builds():
    root = pathlib.Path(__file__).parent.parent
    gitignore = (root / ".gitignore").read_text(encoding="utf-8", errors="ignore")
    
    assert "*.exe" in gitignore
    assert "dist/" in gitignore
    assert "build/" in gitignore
    assert "*.spec" in gitignore
    assert ".venv/" in gitignore
