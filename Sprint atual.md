# Sprint Atual: Correção UTF-8 no Motor Maps & Novo Frontend Intuitivo de Relatórios Prontos

- **Projeto**: Painel de Busca (`c:\Projetos Quecine\Painel de Busca`)
- **Data de Início**: 31/10/2026 às 17:55
- **Status**: Em andamento (80%)
- **Repositório GitHub**: `https://github.com/Gallo41/painel-de-busca.git`

---

## 🎯 Objetivo da Sprint
1. Corrigir definitivamente o erro `'charmap' codec can't encode character '\u25b6'` no Windows ao executar buscas com o motor Docker ativo (`scripts/scrape.py` e `app/services/maps_scraper.py`).
2. Redesenhar a experiência do Frontend (`index.html`, `styles.css`, `app.js`) para ser **extremamente intuitiva, limpa e focada em entregar Relatórios Prontos** — sem caixas técnicas confusas: o usuário apenas escolhe a Cidade + Nichos, clica em **"Gerar Relatório Pronto"**, e recebe fichas completas e mastigadas de cada possível cliente (com o diagnóstico das 8 ferramentas traduzido em português simples, o que vender para cada um e o botão de chamar no WhatsApp em 1 clique).

## Próximo passo
- Criar testes automatizados (`tests/test_ready_reports.py`) testando busca para `Piracicaba - SP` e validando zero erros de encoding e estrutura completa dos Relatórios Prontos (Marco 90%).

---

## 📋 Checklist de Progresso Obrigatório (Regra dos 10%)

- [x] **10%** - Planejamento da Sprint 3 e diagnóstico da causa-raiz do erro `'charmap' codec` em `scripts/scrape.py`
- [x] **20%** - Corrigir encoding UTF-8 no Windows em `scripts/scrape.py`, `app/main.py` e `app/services/maps_scraper.py` (eliminando `UnicodeEncodeError`)
- [x] **30%** - Otimizar e blindar `POST /api/jobs` e `run_live_maps_scrape` para execução rápida, combinando motor Docker + descoberta CNAE + fallback sem travar a interface
- [x] **40%** - Criar formatador de **Relatório Pronto por Cliente** no backend (traduzindo o Raio-X das 8 ferramentas em tópicos comerciais claros e diretos)
- [x] **50%** - Adicionar endpoint e estrutura de **Resumo Executivo do Relatório** (`/api/reports/summary` e retorno enriquecido em `/api/leads`)
- [x] **60%** - Redesenhar `app/static/index.html` em uma interface limpa de 3 passos focada em **Relatórios Prontos** (sem inputs técnicos espalhados)
- [x] **70%** - Atualizar `app/static/styles.css` com design de **Ficha de Relatório Executivo** e modo de impressão/PDF limpo (`@media print`)
- [x] **80%** - Atualizar `app/static/app.js` com visualização em Cards de Relatório Prontos, abas inteligentes por tipo de serviço a vender e 1-clique para WhatsApp/Fila do Robô
- [ ] **90%** - Criar testes automatizados (`tests/test_ready_reports.py`) testando busca para `Piracicaba - SP` e validando zero erros de encoding
- [ ] **100%** - Validar 100% da suíte `pytest`, atualizar grafo `graphify-out/`, testar busca real em `http://127.0.0.1:8090` e sincronizar com GitHub

---

## 📝 Diário de Bordo & Checkpoints Salvos (10% em 10%)
| % Concluído | Data / Hora | Descrição do Progresso / Entrega Parcial | Arquivos Modificados |
| :---: | :---: | :--- | :--- |
| **10%** | 31/10/2026 17:55 | Início da Sprint 3: mapeamento do erro `UnicodeEncodeError` no Windows em `scripts/scrape.py` e definição do novo layout de Relatórios Prontos. | `Sprint atual.md`, `task.md` |
| **20%** | 31/10/2026 18:03 | Correção definitiva de encoding UTF-8 no Windows em `scripts/scrape.py` e `app/main.py`. | `scripts/scrape.py`, `app/main.py` |
| **30%** | 31/10/2026 18:03 | Otimização de `run_live_maps_scrape` e `geocode_city_embedded` (incluindo Piracicaba e cidades SP) para resposta rápida sem bloqueio. | `app/services/maps_scraper.py`, `Sprint atual.md` |
| **40%** | 31/10/2026 18:06 | Implementação de `build_ready_report_for_lead` em `app/services/outreach_generator.py` traduzindo as 8 ferramentas em tópicos comerciais claros. | `app/services/outreach_generator.py` |
| **50%** | 31/10/2026 18:06 | Implementação de `build_executive_summary_report` e rota `GET /api/reports/summary` em `app/routers/leads_router.py`. | `app/services/outreach_generator.py`, `app/routers/leads_router.py` |
| **60%** | 31/10/2026 18:10 | Redesenho completo de `app/static/index.html` focado em 3 passos intuitivos e Relatórios Prontos por Cliente. | `app/static/index.html` |
| **70%** | 31/10/2026 18:11 | Atualização de `app/static/styles.css` com estilos de Fichas de Relatório Prontas, abas 1-clique e modo `@media print`. | `app/static/styles.css` |
| **80%** | 31/10/2026 18:16 | Atualização de `app/static/app.js` com renderização de Fichas de Relatório Prontas (`renderReadyReportsGrid`), Resumo Executivo e inclusão automática de empresas recém-abertas (CNPJ). | `app/static/app.js` |

---
*Gerado e mantido automaticamente pelo protocolo de sincronismo Antigravity <-> Operador <-> Obsidian.*