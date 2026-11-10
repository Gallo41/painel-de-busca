# Graph Report - Painel de Busca  (2026-11-03)

## Corpus Check
- 54 files · ~41,212 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: .bat 4, (none) 1, .ico 1)

## Summary
- 552 nodes · 1199 edges · 38 communities (29 shown, 9 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 39 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c5f8648c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Site X-Ray & Tech Stack
- Google Maps Scraper Engine
- Business Discovery & RDAP
- Site X-Ray & Tech Stack
- SQLite Persistence & Lead Scoring
- 🚀 Guia de Instalação e Uso Rápido — Painel de Busca
- score_and_classify_lead
- maps_scraper.py
- Regra Mandatória: Commit e Sincronização Automática com GitHub
- Cluster 9: app/__init__.py
- Cluster 10: routers/__init__.py
- Cluster 11: services/__init__.py
- Cluster 12: post-commit
- Cluster 13: git-auto-sync.ps1
- README Painel de Busca
- Sprint Atual
- test_installer_integrity.py
- Empresa de agentes do Painel de Busca
- analista
- atendente
- contador
- copywriter
- desenvolvedor
- dev-seguranca
- gerente-geral
- gestor-de-trafego
- pesquisador
- testador
- vendedor
- web-designer
- Mapa do projeto
- AGENTS.md

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 27 edges
2. `process_and_save_lead()` - 19 edges
3. `esc()` - 18 edges
4. `run_live_maps_scrape()` - 17 edges
5. `get_lead()` - 16 edges
6. `run_full_xray_for_lead()` - 16 edges
7. `create_app()` - 14 edges
8. `api_create_and_run_job()` - 14 edges
9. `check_registro_br_availability()` - 14 edges
10. `renderRows()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `test_is_social_or_directory_url()` --calls--> `is_social_or_directory_url()`  [INFERRED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `test_suggest_domain_br_strips_accents_and_stopwords()` --calls--> `suggest_domain_br()`  [INFERRED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `test_check_site_availability_and_ssl_offline_domain()` --calls--> `check_site_availability_and_ssl()`  [INFERRED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `test_build_casadosdados_links()` --calls--> `build_casadosdados_links()`  [INFERRED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `_one()` --indirect_call--> `db_path()`  [INFERRED]
  app/services/outreach_generator.py → tests/test_database.py

## Import Cycles
- None detected.

## Communities (38 total, 9 thin omitted)

### Community 0 - "Site X-Ray & Tech Stack"
Cohesion: 0.07
Nodes (31): build_casadosdados_links(), check_registro_br_availability(), check_site_availability_and_ssl(), _default_http_get(), discover_companies_by_cnae_and_city(), extract_hostname(), format_cnpj(), is_social_or_directory_url() (+23 more)

### Community 1 - "Google Maps Scraper Engine"
Cohesion: 0.08
Nodes (20): main(), open_browser(), collect_keywords(), contact_links(), enrich_emails(), work(), enrich_socials(), work() (+12 more)

### Community 2 - "Business Discovery & RDAP"
Cohesion: 0.06
Nodes (79): ALL_LEADS, ALL_NICHES, applyFilters(), applyQuickTab(), bindShortcuts(), buildPaginationButtons(), checkQuickDomain(), cleanWhatsAppNumber() (+71 more)

### Community 3 - "Site X-Ray & Tech Stack"
Cohesion: 0.09
Nodes (41): claim_next_outreach(), create_search_job(), deduplicate_existing_leads_db(), _deserialize_job(), _deserialize_lead(), _deserialize_outreach(), enqueue_outreach(), _find_existing_lead_id() (+33 more)

### Community 4 - "SQLite Persistence & Lead Scoring"
Cohesion: 0.06
Nodes (45): LeadManagementUpdate, ManualLeadCreate, OutreachClaimRequest, OutreachEnqueueRequest, OutreachStatusUpdate, SearchJobRequest, api_casadosdados_links(), api_check_registro_br() (+37 more)

### Community 5 - "🚀 Guia de Instalação e Uso Rápido — Painel de Busca"
Cohesion: 0.22
Nodes (8): 1. O instalador avisou que o Python não foi encontrado e o winget falhou, 2. Porta 8090 já em uso, 3. Como gerar um executável `.exe` independente?, 💻 Como Abrir no Dia a Dia, ⚙️ Dúvidas Frequentes & Resolução de Problemas, 🚀 Guia de Instalação e Uso Rápido — Painel de Busca, ⚡ Instalação em 1 Clique (Método Recomendado), 🛡️ Sistema com Auto-Cura Integrado

### Community 6 - "score_and_classify_lead"
Cohesion: 0.07
Nodes (9): score_and_classify_lead(), client(), client(), test_score_lead_for_complex_system_expansion(), test_score_lead_with_offline_website(), test_score_lead_without_website_and_free_domain(), client(), test_live_maps_scrape_piracicaba_utf8_safe() (+1 more)

### Community 7 - "maps_scraper.py"
Cohesion: 0.14
Nodes (16): build_keywords_for_job(), _clean_maps_address(), generate_sample_leads_for_niches(), geocode_city_embedded(), harvest_completed_docker_jobs_for_city(), infer_niche_slug_from_row(), normalize_whatsapp_br(), parse_csv_content_to_leads() (+8 more)

### Community 8 - "Regra Mandatória: Commit e Sincronização Automática com GitHub"
Cohesion: 0.50
Nodes (3): Diretrizes de Commit Automático, Regra Mandatória: Commit e Sincronização Automática com GitHub, Repositório Oficial

### Community 9 - "Cluster 9: app/__init__.py"
Cohesion: 0.14
Nodes (13): Global Constraints, Painel de Busca & Prospecção de Leads Implementation Plan, Review Focus, Task 10 (100%): Grafo de Conhecimento Graphify (`graphify-out/`), Documentação (`README.md`) e Validação Final, Task 1 (10%): Onboarding Padrão Delbor, Repositório GitHub, Spec e Plano, Task 2 (20%): Camada de Banco de Dados SQLite e Modelos (`app/database.py`), Task 3 (30%): Catálogo de Nichos & Integração com `google-maps-scraper` (`app/services/maps_scraper.py`), Task 4 (40%): Módulo "Achar o Negócio" — Registro.br RDAP, Health Check e Casa dos Dados (`app/services/business_discovery.py`) (+5 more)

### Community 10 - "Cluster 10: routers/__init__.py"
Cohesion: 0.22
Nodes (8): 1. Iniciar o Painel Web, 2. (Opcional) Subir o Motor Docker do Google Maps Scraper, 🛠️ As 8 Ferramentas Integradas no Motor, 🤖 Base Pré-Pronta para o Projeto Futuro de Automação de Contato, Coluna 1 — Achar o Negócio (`app/services/business_discovery.py` + `maps_scraper.py`), Coluna 2 — Raio-X do Site Atual (`app/services/site_xray.py`), 🚀 Como Usar no Dia a Dia, Painel de Busca, Raio-X & Prospecção de Leads (Freelancers)

### Community 11 - "Cluster 11: services/__init__.py"
Cohesion: 0.25
Nodes (7): 1. Visão Geral e Objetivo, 2. Arquitetura do Sistema, 3. Modelo de Dados (SQLite), 4. Tratamento de Erros e Limites, Coluna 1 — Achar o Negócio (`business_discovery`), Coluna 2 — Raio-X do Site Atual (`site_xray`), Especificação Arquitetural — Painel de Busca, Raio-X e Prospecção de Leads

### Community 12 - "Cluster 12: post-commit"
Cohesion: 0.33
Nodes (5): 1. Registro Obrigatório no Início da Tarefa / Sprint, 2. Checkpoint Incremental de 10 em 10% (Salvamento Seguro), 3. Economia de Tokens com Graphify e Obsidian, 4. Sincronismo Antigravity <-> Claudinho / OpenCode, Regra Mandatória: Sprint, Checkpoint 10% e Sincronismo com Obsidian

### Community 13 - "Cluster 13: git-auto-sync.ps1"
Cohesion: 0.33
Nodes (5): 📋 Checklist de Progresso Obrigatório (Regra dos 10%), 📝 Diário de Bordo & Checkpoints Salvos (10% em 10%), 🎯 Objetivo da Sprint, Próximo passo, Sprint Atual: Embutir as 8 Ferramentas Nativamente no Painel (Zero Links Externos) & Motor Docker Ativo

### Community 22 - "test_installer_integrity.py"
Cohesion: 0.70
Nodes (3): test_gitignore_protects_binaries_and_builds(), test_installer_assets_exist(), test_installer_scripts_contain_key_routines()

### Community 23 - "Empresa de agentes do Painel de Busca"
Cohesion: 0.22
Nodes (8): Como começar, Empresa de agentes do Painel de Busca, Finalidade e estado real, Fluxo de trabalho, Gemini, DeepSeek e outras IAs, Registro mínimo de tarefa e repasse, Responsabilidades, Skills e qualidade

### Community 24 - "analista"
Cohesion: 0.40
Nodes (4): analista, Entrega e repasse, Papel e modo de trabalho, Regras obrigatórias

### Community 25 - "atendente"
Cohesion: 0.40
Nodes (4): atendente, Entrega e repasse, Papel e modo de trabalho, Regras obrigatórias

### Community 26 - "contador"
Cohesion: 0.40
Nodes (4): contador, Entrega e repasse, Papel e modo de trabalho, Regras obrigatórias

### Community 27 - "copywriter"
Cohesion: 0.40
Nodes (4): copywriter, Entrega e repasse, Papel e modo de trabalho, Regras obrigatórias

### Community 28 - "desenvolvedor"
Cohesion: 0.40
Nodes (4): desenvolvedor, Entrega e repasse, Papel e modo de trabalho, Regras obrigatórias

### Community 29 - "dev-seguranca"
Cohesion: 0.40
Nodes (4): dev-seguranca, Entrega e repasse, Papel e modo de trabalho, Regras obrigatórias

### Community 30 - "gerente-geral"
Cohesion: 0.40
Nodes (4): Entrega e repasse, gerente-geral, Papel e modo de trabalho, Regras obrigatórias

### Community 31 - "gestor-de-trafego"
Cohesion: 0.40
Nodes (4): Entrega e repasse, gestor-de-trafego, Papel e modo de trabalho, Regras obrigatórias

### Community 32 - "pesquisador"
Cohesion: 0.40
Nodes (4): Entrega e repasse, Papel e modo de trabalho, pesquisador, Regras obrigatórias

### Community 33 - "testador"
Cohesion: 0.40
Nodes (4): Entrega e repasse, Papel e modo de trabalho, Regras obrigatórias, testador

### Community 34 - "vendedor"
Cohesion: 0.40
Nodes (4): Entrega e repasse, Papel e modo de trabalho, Regras obrigatórias, vendedor

### Community 35 - "web-designer"
Cohesion: 0.40
Nodes (4): Entrega e repasse, Papel e modo de trabalho, Regras obrigatórias, web-designer

### Community 36 - "Mapa do projeto"
Cohesion: 0.40
Nodes (4): Aplicação observada, Camada de agentes, Contexto, Git e Graphify, Mapa do projeto

## Knowledge Gaps
- **2 isolated node(s):** `README Painel de Busca`, `Sprint Atual`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 220 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `create_app()` connect `Site X-Ray & Tech Stack` to `score_and_classify_lead`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **What connects `README Painel de Busca`, `Sprint Atual` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Site X-Ray & Tech Stack` be split into smaller, more focused modules?**
  _Cohesion score 0.06861239119303636 - nodes in this community are weakly interconnected._
- **Why does `run_live_maps_scrape()` connect `maps_scraper.py` to `Google Maps Scraper Engine`, `SQLite Persistence & Lead Scoring`, `score_and_classify_lead`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Should `Google Maps Scraper Engine` be split into smaller, more focused modules?**
  _Cohesion score 0.07536231884057971 - nodes in this community are weakly interconnected._
- **Why does `process_and_save_lead()` connect `SQLite Persistence & Lead Scoring` to `Site X-Ray & Tech Stack`, `Site X-Ray & Tech Stack`, `score_and_classify_lead`, `maps_scraper.py`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Should `Business Discovery & RDAP` be split into smaller, more focused modules?**
  _Cohesion score 0.057181942544459644 - nodes in this community are weakly interconnected._