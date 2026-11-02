# Sprint Atual: Barra de Filtros Rápidos de Decisão & Busca Dedicada

- **Projeto**: Painel de Busca (`c:\Projetos Quecine\Painel de Busca`)
- **Data de Início**: 01/11/2026 às 21:48
- **Status**: Em Andamento (10%)
- **Repositório GitHub**: `https://github.com/Gallo41/painel-de-busca.git`

---

## 🎯 Objetivo da Sprint
Criar uma barra de filtros rápidos e busca dedicada para que o usuário possa pesquisar e filtrar instantaneamente os estabelecimentos conforme o que decidiu ("Vou fazer", "Estou fazendo", "Não vou fazer", etc.):
1. **Barra de Pílulas de Decisão**: Botões de 1 clique com contadores em tempo real para `Todos (167)`, `🎯 Vou fazer (X)`, `⏳ Fazendo (Y)`, `❌ Não vou fazer (Z)`, `✅ Fechados (W)` e `⚪ Novos (K)`.
2. **Busca Rápida Inline**: Campo de busca posicionado diretamente acima da lista para pesquisar na hora por nome, bairro ou nicho.
3. **Limpeza e Reset em 1 Clique**: Botão de limpar filtros visível sempre que houver algum filtro ativo.

---

## 📋 Checklist de Progresso Obrigatório (Regra dos 10%)

- [x] **10%** - Especificação e Wireframe da barra de filtros rápidos de decisão com contadores ao vivo
- [ ] **20%** - Estrutura HTML da barra de pílulas de decisão (`.decision-filter-strip`) em `index.html`
- [ ] **30%** - Campo de busca rápida integrado diretamente acima da tabela (`#filter-search-inline`)
- [ ] **40%** - Estilização CSS responsiva das pílulas de decisão com badges e estados ativos (`styles.css`)
- [ ] **50%** - Lógica de filtro por decisão e contadores dinâmicos no `renderSummary()` (`app.js`)
- [ ] **60%** - Função `setStatusFilter(statusKey)` com sincronização entre botões e dropdown de situação (`app.js`)
- [ ] **70%** - Sincronização bidirecional entre busca da topbar e busca inline com debounce (`app.js`)
- [ ] **80%** - Botão "Limpar filtros" com reset total e volta para "Todos" (`index.html`, `app.js`)
- [ ] **90%** - Testes automatizados cobrindo a presença dos filtros rápidos e funcionamento no `tests/`
- [ ] **100%** - Validação completa com `pytest`, `graphify update .`, commit e sincronização com GitHub

---

## 📝 Diário de Bordo & Checkpoints Salvos (10% em 10%)
| % Concluído | Data / Hora | Descrição do Progresso / Entrega Parcial | Arquivos Modificados |
| :---: | :---: | :--- | :--- |
| **10%** | 01/11/2026 21:48 | Especificação da barra de filtros rápidos por decisão com contadores e busca inline posicionada diretamente acima da tabela de empresas. | `Sprint atual.md`, `task.md` |

---
*Gerado e mantido automaticamente pelo protocolo de sincronismo Antigravity <-> Operador <-> Obsidian.*
