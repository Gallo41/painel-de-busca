# Sprint Atual: Correção de Cache do Navegador, Migração de Base Existente e Resiliência do Botão WhatsApp

- **Projeto**: Painel de Busca (`c:\Projetos Quecine\Painel de Busca`)
- **Data de Início**: 03/11/2026 às 21:40
- **Status**: Em Andamento (70%)
- **Repositório GitHub**: `https://github.com/Gallo41/painel-de-busca.git`

---

## 🎯 Objetivo da Sprint
Resolver o cenário onde o usuário abriu o painel e tudo permaneceu igual ao comportamento anterior (*"não foi aqui comigo, tá igual antes"*):
1. **Causa 1 - Cache Persistente do Navegador (`app.js?v=2.4` e `index.html`)**: O navegador armazenou o JavaScript em cache local, impedindo o download das funções `openWhatsApp` e `copyCardMessage`. Bumper de versão para `v=2.5.2` e inclusão de headers HTTP anti-cache (`no-cache, no-store, must-revalidate`).
2. **Causa 2 - Leads já Gravados no SQLite com Texto Antigo**: Os 227 leads já existentes no banco `painel_busca.db` continham o JSON antigo pré-gerado. Criação de rotina de migração automática (`migrate_humanized_scripts_db`) para atualizar todos os registros existentes.
3. **Causa 3 - Bloqueador de Pop-ups e Reconhecimento de Telefone**: Garantir abertura com elemento âncora programático (fallback anti-popup) e expandir `waNumber` para ler `l.phone` caso `whatsapp_clean` falte.

---

## 📋 Checklist de Progresso Obrigatório (Regra dos 10%)

- [x] **10%** - Diagnóstico e abertura da Sprint no `Sprint atual.md`, Operador e `task.md`
- [x] **20%** - Implementação de `migrate_humanized_scripts_db` em `app/database.py` e migração da base SQLite
- [x] **30%** - Integração automática de `migrate_humanized_scripts_db` na inicialização do servidor em `app/main.py`
- [x] **40%** - Headers HTTP anti-cache (`no-cache, no-store, must-revalidate`) no endpoint raiz em `app/main.py`
- [x] **50%** - Cache-busting e meta-tags anti-cache em `app/static/index.html` (`v=2.5.2`)
- [x] **60%** - Fallback de `waNumber(l)` aceitando `l.phone` e abertura com elemento âncora DOM em `app/static/app.js`
- [x] **70%** - Vinculação explícita de `window.openWhatsApp` e `window.copyCardMessage` no escopo global
- [ ] **80%** - Criação de testes unitários para a migração de banco e validação de headers anti-cache
- [ ] **90%** - Execução da suíte completa de testes (`pytest`) sem regressões
- [ ] **100%** - Atualização do grafo Graphify, finalização da sprint e commit/push Git

---

## 📝 Diário de Bordo & Checkpoints Salvos (10% em 10%)
| % Concluído | Data / Hora | Descrição do Progresso / Entrega Parcial | Arquivos Modificados |
| :---: | :---: | :--- | :--- |
| **10%** | 03/11/2026 21:40 | Diagnóstico das causas-raiz: cache em disco do navegador de app.js?v=2.4 e 227 leads pré-salvos com JSON antigo no SQLite. | `Sprint atual.md`, `task.md` |
| **20%** | 03/11/2026 21:42 | Implementação de `migrate_humanized_scripts_db` em `app/database.py` com migração dos 227 leads existentes no banco de produção. | `app/database.py`, `Sprint atual.md` |
| **30%** | 03/11/2026 21:43 | Chamada automática de `migrate_humanized_scripts_db(db_path)` no startup do FastAPI em `app/main.py`. | `app/main.py`, `Sprint atual.md` |
| **40%** | 03/11/2026 21:44 | Inclusão de cabeçalhos HTTP anti-cache (`Cache-Control: no-cache, no-store, must-revalidate`) no `serve_dashboard()`. | `app/main.py`, `Sprint atual.md` |
| **50%** | 03/11/2026 21:46 | Adição de meta tags anti-cache no `<head>` e bump para `v=2.5.2` em `index.html` forçando recarga imediata de JS e CSS. | `app/static/index.html`, `Sprint atual.md` |
| **60%** | 03/11/2026 21:47 | Atualização de `waNumber(l)` para aceitar `l.phone` como fallback e rotina anti-bloqueador de popup com âncora programática. | `app/static/app.js`, `Sprint atual.md` |
| **70%** | 03/11/2026 21:48 | Vinculação direta de `openWhatsApp`, `copyCardMessage` e `cleanWhatsAppNumber` ao `window` para total compatibilidade inline. | `app/static/app.js`, `Sprint atual.md` |

---
*Gerado e mantido automaticamente pelo protocolo de sincronismo Antigravity <-> Operador <-> Obsidian.*
