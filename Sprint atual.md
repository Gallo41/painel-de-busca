# Sprint Atual: Sistema de Decisão e Marcação Rápida de Estabelecimentos (Vou Fazer / Não Vou Fazer / Fazendo)

- **Projeto**: Painel de Busca (`c:\Projetos Quecine\Painel de Busca`)
- **Data de Início**: 01/11/2026 às 21:34
- **Status**: Em Andamento (10%)
- **Repositório GitHub**: `https://github.com/Gallo41/painel-de-busca.git`

---

## 🎯 Objetivo da Sprint
Permitir que o usuário "tique" e marque de forma ágil o que vai fazer com cada estabelecimento na prospecção:
1. **Controle de 1 Clique por Linha**: Adicionar uma coluna de Decisão/Status em cada linha da tabela com pills interativas (`🎯 Vou Fazer`, `⏳ Estou Fazendo`, `❌ Não Vou Fazer`, `✅ Fechado`, `⚪ Novo`).
2. **Botões Rápidos na Central de Contato**: Bloco destacado com 4 botões de ação rápida para decidir e atualizar o lead sem burocracia.
3. **Filtros e Visual Diferenciado**: Linhas marcadas como "Não vou fazer" ficam discretas/atenuadas, linhas "Vou fazer" ganham destaque visual, e um toggle na barra permite ocultar com 1 clique todas as empresas descartadas.

---

## 📋 Checklist de Progresso Obrigatório (Regra dos 10%)

- [x] **10%** - Especificação e Mapeamento de Estados ("Vou fazer", "Estou fazendo", "Não vou fazer", "Fechado", "Novo")
- [ ] **20%** - Atualização de modelos e rotas backend (`app/models.py`, `app/database.py`) para suporte aos novos status
- [ ] **30%** - Nova coluna de "Decisão / Status" no cabeçalho e estrutura da tabela (`index.html`)
- [ ] **40%** - Estilização dos seletores de status em formato de pill/tag e destaques visuais nas linhas (`styles.css`)
- [ ] **50%** - Função `quickUpdateLeadStatus(id, newStatus)` no frontend com atualização assíncrona instantânea (`app.js`)
- [ ] **60%** - Renderização do seletor interativo em cada linha da lista paginada com cores contextuais (`app.js`)
- [ ] **70%** - Botões táteis de decisão rápida de 1-clique na Central de Contato lateral (`app.js`, `styles.css`)
- [ ] **80%** - Filtro de situação atualizado e toggle "Ocultar Não vou fazer" na barra de filtros (`index.html`, `app.js`)
- [ ] **90%** - Testes automatizados cobrindo a persistência e visualização dos status no `tests/`
- [ ] **100%** - Validação completa com `pytest`, `graphify update .`, verificação final e sincronização com GitHub

---

## 📝 Diário de Bordo & Checkpoints Salvos (10% em 10%)
| % Concluído | Data / Hora | Descrição do Progresso / Entrega Parcial | Arquivos Modificados |
| :---: | :---: | :--- | :--- |
| **10%** | 01/11/2026 21:34 | Especificação e mapeamento dos estados ("Vou fazer", "Estou fazendo", "Não vou fazer", "Fechado", "Novo") e arquitetura das ações de 1 clique na tabela e no detalhe. | `Sprint atual.md`, `task.md` |

---
*Gerado e mantido automaticamente pelo protocolo de sincronismo Antigravity <-> Operador <-> Obsidian.*
