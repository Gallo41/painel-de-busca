# Sprint Atual: Paginação na Tabela de Recomendações e Oportunidades do Painel

- **Projeto**: Painel de Busca (`c:\Projetos Quecine\Painel de Busca`)
- **Data de Início**: 01/11/2026 às 20:45
- **Status**: Em Andamento (20%)
- **Repositório GitHub**: `https://github.com/Gallo41/painel-de-busca.git`

---

## 🎯 Objetivo da Sprint
Implementar paginação completa, fluida e responsiva na tabela de recomendações/oportunidades do Painel de Busca:
1. **Controles Completos de Paginação**: Adicionar botões `« Anterior`, números de página com elipses inteligentes (ex: `1 ... 4 5 6 ... 17`), `Próxima »`, contador `1–10 de X empresas` e seletor de itens por página (`10`, `20`, `50`, `100`).
2. **Experiência Visual e Usabilidade**: Evitar listas infinitas que exigem rolagem excessiva, integrando perfeitamente a navegação entre páginas com a Central de Contato lateral e atalhos de teclado (`ArrowUp`, `ArrowDown`, `j`, `k`).
3. **Persistência e Suporte Completo**: Garantir reset automático para página 1 ao filtrar ou buscar, retenção da seleção atual de empresa, e compatibilidade com impressão e temas Dark/Light.

---

## 📋 Checklist de Progresso Obrigatório (Regra dos 10%)

- [x] **10%** - Diagnóstico e Especificação da Paginação (mapeamento do estado em `app.js`, markup em `index.html` e estilos em `styles.css`)
- [x] **20%** - Estrutura HTML da Barra de Paginação (controles `« Anterior`, números de página, `Próxima »`, seletor por página e contadores)
- [ ] **30%** - Estilização CSS responsiva e compatível com temas Dark/Light (`.pagination-bar`, botões, badges, estados ativo/desabilitado)
- [ ] **40%** - Lógica de Estado da Paginação no JavaScript (`page`, `pageSize`, cálculo de `totalPages`, fatiamento `slice` dos leads)
- [ ] **50%** - Renderização dinâmica dos botões numéricos com elipses inteligentes (ex: `1 ... 4 5 6 ... 17`)
- [ ] **60%** - Integração com filtros, buscas, abas e KPIs (reset automático para página 1 ao filtrar ou buscar)
- [ ] **70%** - Interatividade completa: seletor de itens por página (10, 20, 50, 100), seleção sincronizada com Central de Contato e navegação por setas
- [ ] **80%** - Compatibilidade com atalhos de teclado, modo impressão (`beforeprint`/`afterprint`) e visualização mobile/overlay
- [ ] **90%** - Testes automatizados em `tests/test_dashboard_ui.py` cobrindo a presença e integridade dos elementos de paginação
- [ ] **100%** - Validação completa com suíte `pytest` (36+ testes), `graphify update .`, verificação final e sincronização com GitHub

---

## 📝 Diário de Bordo & Checkpoints Salvos (10% em 10%)
| % Concluído | Data / Hora | Descrição do Progresso / Entrega Parcial | Arquivos Modificados |
| :---: | :---: | :--- | :--- |
| **10%** | 01/11/2026 20:45 | Diagnóstico realizado: mapeamento de renderRows(), estado do frontend, markup e estilos necessários para substituir lista única por paginação estruturada. | `Sprint atual.md`, `task.md` |
| **20%** | 01/11/2026 20:46 | Estrutura HTML da barra de navegação/paginação implementada com controles de página anterior, próxima, números e seletor de itens por página. | `app/static/index.html` |

---
*Gerado e mantido automaticamente pelo protocolo de sincronismo Antigravity <-> Operador <-> Obsidian.*


---

# Sprint Paralela: Landing Pages de Demonstração Automáticas por Cliente

- **Projeto**: Painel de Busca (`c:\Projetos Quecine\Painel de Busca`)
- **Data de Início**: 01/11/2026 às 20:45
- **Status**: Em andamento (60%)
- **Repositório GitHub**: `https://github.com/Gallo41/painel-de-busca.git`

---

## Objetivo
Gerar automaticamente, para cada lead elegível (sem site ou com site ruim), uma landing page de exemplo personalizada (nome, nicho, cidade, WhatsApp, avaliações) para usar na apresentação comercial. Template fixo por nicho + textos via Gemini (opcional, com fallback).

## Premissas adotadas (aguardando confirmação do usuário)
- Elegibilidade: `has_website = 0` ou `primary_pain` de site ruim.
- Conteúdo: template + Gemini (`GEMINI_API_KEY`), fallback determinístico.
- Publicação: servida localmente em `/demo/{slug}` (túnel/deploy a definir).

## Arquivos alvo
`app/database.py`, `app/services/landing_generator.py`, `app/routers/landing_router.py`, `app/main.py`, `app/static/*`, `app/services/outreach_generator.py`, `tests/test_landing_generator.py`

---

## Checklist de Progresso (Regra dos 10%)

- [x] **10%** - Definir elegibilidade e abordagem de geração (premissas acima)
- [x] **20%** - Tabela `landing_pages` + funções no `database.py`
- [x] **30%** - Template base genérico com dados do lead (HTML escapado)
- [x] **40%** - `landing_generator.py` (slug, contexto, render, persistência)
- [x] **50%** - Rotas `POST/GET /api/leads/{id}/landing` e `GET /demo/{slug}`
- [x] **60%** - Temas por nicho (saúde, beleza, serviços, comércio, genérico)
- [ ] **70%** - Copy via Gemini com fallback (implementado) + teste com chave real
- [ ] **80%** - Gatilho automático no pipeline + fila em background
- [ ] **90%** - UI (botão/status no card do lead) + `{link_demo}` nos scripts de outreach
- [ ] **100%** - Testes `pytest`, `graphify update .`, commit/push

---

## Diário de Bordo & Checkpoints Salvos
| % Concluído | Data / Hora | Descrição | Arquivos Modificados |
| :---: | :---: | :--- | :--- |
| **10-60%** | 01/11/2026 20:47 | Tabela `landing_pages`, gerador com temas por nicho, rotas de geração e `/demo/{slug}`, 7 testes novos (42 passando). | `app/database.py`, `app/services/landing_generator.py`, `app/routers/landing_router.py`, `app/main.py`, `tests/test_landing_generator.py` |

