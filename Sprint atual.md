# Sprint Atual: Construção do Painel de Busca, Raio-X das 8 Ferramentas e Central de Outreach

- **Projeto**: Painel de Busca (`c:\Projetos Quecine\Painel de Busca`)
- **Data de Início**: 28/10/2026 às 19:08
- **Status**: Em andamento (60%)
- **Repositório GitHub**: `https://github.com/Gallo41/painel-de-busca.git`

---

## 🎯 Objetivo da Sprint
Construir um Painel Web Local completo (FastAPI + SQLite + Dashboard SPA) para prospecção de clientes freelance (Sites, Reformas e Sistemas Complexos), integrando a skill `google-maps-scraper` (`Mahanaicoach/google-maps-scraper-kit`), as 8 ferramentas de diagnóstico da imagem (Google Maps, Casa dos Dados, Registro.br RDAP, DownForEveryoneOrJustMe, BuiltWith, Wappalyzer, WhatCMS e Web Archive), gerador automático de scripts de abordagem (WhatsApp 1-clique, E-mail, Instagram DM) e API/fila pré-pronta para automação futura de disparo.

## Próximo passo
- Implementar a Central de Contato & Gerador Automático de Scripts de Abordagem (`app/services/outreach_generator.py`) para WhatsApp 1-clique, E-mail e Instagram DM, para atingir o marco de **70%**.

---

## 📋 Checklist de Progresso Obrigatório (Regra dos 10%)

- [x] **10%** - Onboarding Padrão Delbor (`.agents/rules/`, `.githooks/post-commit`, `scripts/git-auto-sync.*`, `.gitignore`), criação do repositório GitHub (`Gallo41/painel-de-busca`), Especificação Arquitetural (`docs/superpowers/specs/`) e Plano de Implementação (`docs/superpowers/plans/`)
- [x] **20%** - Camada de Banco de Dados SQLite e Modelos (`app/database.py`, `app/models.py`) para `niches`, `search_jobs`, `leads` e `outreach_queue` + testes (`tests/test_database.py`)
- [x] **30%** - Catálogo de Nichos pré-selecionados + Integração com a skill `google-maps-scraper` (`docker-compose.yml`, `scripts/scrape.py`, `app/services/maps_scraper.py`) + testes (`tests/test_maps_scraper.py`)
- [x] **40%** - Módulo "Achar o Negócio" (`app/services/business_discovery.py`): verificador oficial de domínio `.com.br` livre via API RDAP do **Registro.br**, Health Check HTTP/SSL (**DownForEveryoneOrJustMe**) e buscador/importador **Casa dos Dados / CNPJ** + testes (`tests/test_business_discovery.py`)
- [x] **50%** - Módulo "Raio-X do Site Atual" (`app/services/site_xray.py`): detector de tecnologias e CMS (**BuiltWith / Wappalyzer / WhatCMS**), detector de oportunidade para **Sistemas Mais Complexos** e consulta de idade/abandono via **Web Archive (Wayback Machine)** + testes (`tests/test_site_xray.py`)
- [x] **60%** - Motor de Pontuação de Oportunidade (`app/services/lead_scorer.py` - Score 0–100) e Classificador de Dor Principal (`SEM_SITE`, `DOMINIO_LIVRE`, `SITE_FORA_DO_AR`, `SITE_AMADOR_ANTIGO`, `OPORTUNIDADE_SISTEMA`) + testes (`tests/test_lead_scorer.py`)
- [ ] **70%** - Central de Contato & Gerador Automático de Scripts de Abordagem (`app/services/outreach_generator.py`): geração de mensagens personalizadas para WhatsApp (link 1-clique `wa.me`), E-mail e Instagram DM + divisão de carteira (`Eu` / `Amigo`) + testes (`tests/test_outreach_generator.py`)
- [ ] **80%** - API REST Completa + Infraestrutura Pré-Pronta para Automação Futura (`app/main.py`, `app/routers/`): fila `outreach_queue`, webhooks e endpoints para bots futuros de WhatsApp/n8n + testes (`tests/test_api.py`)
- [ ] **90%** - Dashboard Web Local (`app/static/`): Seletor de Nichos & Cidade antes de gerar relatórios, Tabela de Leads com Score Raio-X, Modal das 8 Ferramentas e Central de Contato 1-Clique + testes de UI (`tests/test_dashboard_ui.py`)
- [ ] **100%** - Geração e atualização completa do Grafo de Conhecimento Graphify (`graphify-out/`), script de inicialização rápida (`iniciar_painel.bat`), documentação (`README.md`) e validação 100% da suíte de testes

---

## 📝 Diário de Bordo & Checkpoints Salvos (10% em 10%)
| % Concluído | Data / Hora | Descrição do Progresso / Entrega Parcial | Arquivos Modificados |
| :---: | :---: | :--- | :--- |
| **10%** | 28/10/2026 19:11 | Onboarding Delbor completo, repositório GitHub `Gallo41/painel-de-busca` criado, skill `google-maps-scraper` instalada globalmente, Spec e Plano de Implementação criados. | `.agents/rules/*`, `.githooks/post-commit`, `scripts/git-auto-sync.*`, `docs/superpowers/*`, `Sprint atual.md` |
| **20%** | 28/10/2026 19:15 | Camada de banco de dados SQLite (`niches`, `search_jobs`, `leads`, `outreach_queue`) e modelos Pydantic implementados e validados com 100% dos testes passando (4/4). | `app/database.py`, `app/models.py`, `tests/test_database.py` |
| **30%** | 28/10/2026 19:18 | Catálogo de 12 nichos de alta conversão + integração nativa com a skill `google-maps-scraper` (`docker-compose.yml`, `scripts/scrape.py`, `app/services/maps_scraper.py`) validados com testes (5/5). | `docker-compose.yml`, `scripts/scrape.py`, `app/services/niches_catalog.py`, `app/services/maps_scraper.py`, `tests/test_maps_scraper.py` |
| **40%** | 28/10/2026 19:20 | Módulo "Achar o Negócio" (`business_discovery.py`) implementado com RDAP Registro.br, Health Check HTTP/SSL (DownForEveryoneOrJustMe) e filtros Casa dos Dados / CNPJ (5/5 testes passando). | `app/services/business_discovery.py`, `tests/test_business_discovery.py` |
| **50%** | 28/10/2026 19:22 | Módulo "Raio-X do Site Atual" (`site_xray.py`) implementado com detector de CMS/Tech Stack (BuiltWith/Wappalyzer/WhatCMS), Wayback Machine e links das 8 ferramentas (5/5 testes passando). | `app/services/site_xray.py`, `tests/test_site_xray.py` |
| **60%** | 29/10/2026 19:18 | Motor de Lead Scoring (0-100) e Classificador de Dor Principal (`SEM_SITE`, `DOMINIO_LIVRE`, `SITE_FORA_DO_AR`, `SITE_AMADOR_ANTIGO`, `OPORTUNIDADE_SISTEMA`) implementados e validados (3/3 testes). | `app/services/lead_scorer.py`, `tests/test_lead_scorer.py` |

---
*Gerado e mantido automaticamente pelo protocolo de sincronismo Antigravity <-> Operador <-> Obsidian.*
