# Sprint Atual: Instalador 1-Clique e Assistente de Configuração para Novos Usuários

- **Projeto**: Painel de Busca (`c:\Projetos Quecine\Painel de Busca`)
- **Data de Início**: 01/11/2026 às 22:30
- **Status**: Em andamento (80%)
- **Repositório GitHub**: `https://github.com/Gallo41/painel-de-busca.git`

---

## 🎯 Objetivo da Sprint
Criar uma experiência de instalação e uso 100% à prova de falhas ("zero friction") para amigos e parceiros que forem rodar o Painel de Busca pela primeira vez no Windows:
1. **Instalador 1-Clique (`INSTALAR_PAINEL.bat`)**: Checa se o Python está presente no sistema (com fallback para instalação silenciosa via `winget`), cria o ambiente virtual `.venv`, instala todas as bibliotecas e gera o atalho na Área de Trabalho com ícone.
2. **Inicializador Inteligente com Auto-Cura (`iniciar_painel.bat`)**: Caso o usuário dê dois cliques direto no inicializador sem ter instalado antes, o script detecta automaticamente a ausência das dependências e realiza o setup sem quebras ou telas pretas fechando do nada.
3. **Atalho na Área de Trabalho (`scripts/criar_atalho.ps1`)**: Criação de atalho `.lnk` no Desktop do Windows com caminho e ícone configurados.
4. **Gerador Opcional de Executável Standalone (`scripts/compilar_exe.bat`)**: Permite compilar um executável `.exe` localmente usando PyInstaller caso queira distribuir sem expor scripts (respeitando a regra do Git de não commitar binários pesados).
5. **Guia Rápido Amigável (`COMO_INSTALAR.txt` e `README.md`)**: Instruções visuais, claras e diretas para quem acabou de baixar ou clonar o projeto.

---

## 📋 Checklist de Progresso Obrigatório (Regra dos 10%)

- [x] **10%** - Abertura da Sprint no `Sprint atual.md`, espelhamento no Operador e no `task.md`
- [x] **20%** - Script utilitário para geração de atalho na Área de Trabalho (`scripts/criar_atalho.ps1`)
- [x] **30%** - Instalador principal `INSTALAR_PAINEL.bat` (detecção de Python, winget fallback e diagnósticos)
- [x] **40%** - Provisionamento automático do `.venv` e dependências (`requirements.txt`) no instalador
- [x] **50%** - Mecanismo de auto-cura no `iniciar_painel.bat` (detecta ausência de ambiente e auto-instala)
- [x] **60%** - Script opcional para compilação local de executável `.exe` (`scripts/compilar_exe.bat`) via PyInstaller
- [x] **70%** - Guias simplificados para o amigo (`COMO_INSTALAR.txt` e `docs/guia-instalacao-amigo.md`)
- [x] **80%** - Atualização do `README.md` com instruções de 1-clique para parceiros
- [ ] **90%** - Testes dos scripts de instalação e execução da suíte `pytest`
- [ ] **100%** - Atualização do grafo Graphify (`graphify update .`), fechamento da Sprint e push final

---

## 📝 Diário de Bordo & Checkpoints Salvos (10% em 10%)
| % Concluído | Data / Hora | Descrição do Progresso / Entrega Parcial | Arquivos Modificados |
| :---: | :---: | :--- | :--- |
| **10%** | 01/11/2026 22:30 | Abertura da Sprint de empacotamento amigável e instalador 1-clique para parceiros, com checklist de 10 marcos e espelhamento no Operador. | `Sprint atual.md`, `task.md` |
| **20%** | 01/11/2026 22:31 | Criação do ícone multi-resolução `app/static/icon.ico`, vínculo no `index.html` e script PowerShell `scripts/criar_atalho.ps1` para gerar o atalho na Área de Trabalho. | `app/static/icon.ico`, `app/static/index.html`, `scripts/criar_atalho.ps1` |
| **30%** | 01/11/2026 22:32 | Implementação do assistente `INSTALAR_PAINEL.bat` com detecção de executável Python (`python`, `py -3`, caminhos padrão) e fallback automático para instalação via `winget`. | `INSTALAR_PAINEL.bat` |
| **40%** | 01/11/2026 22:33 | Provisionamento do ambiente virtual `.venv`, instalação das dependências via `requirements.txt`, criação de diretórios de dados e validação de imports. | `INSTALAR_PAINEL.bat`, `Sprint atual.md` |
| **50%** | 01/11/2026 22:35 | Implementação de rotina de auto-cura no `iniciar_painel.bat` com detecção inteligente de `.venv` e dependências com chamada automática ao instalador. | `iniciar_painel.bat` |
| **60%** | 01/11/2026 22:36 | Script de compilação em executável standalone `scripts/compilar_exe.bat` com `launcher_exe.py` e inclusão de `dist/`, `build/` e `*.spec` no `.gitignore`. | `scripts/compilar_exe.bat`, `scripts/launcher_exe.py`, `.gitignore` |
| **70%** | 01/11/2026 22:37 | Criação do guia direto ao ponto em texto plano `COMO_INSTALAR.txt` na raiz e documentação completa com troubleshooting em `docs/guia-instalacao-amigo.md`. | `COMO_INSTALAR.txt`, `docs/guia-instalacao-amigo.md` |
| **80%** | 01/11/2026 22:38 | Atualização da documentação no `README.md` com seção dedicada de instalação 1-clique, modos de inicialização diária e compilação standalone. | `README.md` |

---
*Gerado e mantido automaticamente pelo protocolo de sincronismo Antigravity <-> Operador <-> Obsidian.*
