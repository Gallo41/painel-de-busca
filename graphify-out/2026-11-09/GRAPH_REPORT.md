# Graph Report - Painel de Busca  (2026-11-09)

## Corpus Check
- 62 files · ~55,714 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: .bat 5, (none) 1, .ico 1)

## Summary
- 733 nodes · 1760 edges · 53 communities (43 shown, 10 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 47 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1a20a767`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Site X-Ray & Tech Stack
- Google Maps Scraper Engine
- app.js
- Site X-Ray & Tech Stack
- leads_router.py
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
- esc
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
- whatsapp_agent.py
- agent_router.py
- server.js
- outreach_generator.py
- 2. Arquitetura Técnica e Componentes
- api_create_and_run_job
- check_scraper_engine_health
- api_tool_delete_maps_job
- renderRows
- renderDetail
- api_tool_discover_companies_by_cnae
- bindShortcuts
- loadHealthAndStats
- loadLeads
- initDashboard

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 44 edges
2. `get_lead()` - 22 edges
3. `get_agent_settings()` - 20 edges
4. `generate_prototype_for_lead()` - 20 edges
5. `process_and_save_lead()` - 19 edges
6. `handle_boss_incoming_message()` - 19 edges
7. `esc()` - 18 edges
8. `_now_iso()` - 17 edges
9. `run_live_maps_scrape()` - 17 edges
10. `confirm_and_send_queue_item()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `2.3. Motor do Agente WhatsApp (`app/services/whatsapp_agent.py`)` --references--> `moeda_br()`  [INFERRED]
  docs/superpowers/specs/2026-11-09-whatsapp-agent-prototype-design.md → app/services/whatsapp_agent.py
- `test_is_social_or_directory_url()` --calls--> `is_social_or_directory_url()`  [INFERRED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `test_suggest_domain_br_strips_accents_and_stopwords()` --calls--> `suggest_domain_br()`  [INFERRED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `test_check_site_availability_and_ssl_offline_domain()` --calls--> `check_site_availability_and_ssl()`  [INFERRED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `test_build_casadosdados_links()` --calls--> `build_casadosdados_links()`  [INFERRED]
  tests/test_business_discovery.py → app/services/business_discovery.py

## Import Cycles
- None detected.

## Communities (53 total, 10 thin omitted)

### Community 0 - "Site X-Ray & Tech Stack"
Cohesion: 0.07
Nodes (30): api_check_registro_br(), check_registro_br_availability(), check_site_availability_and_ssl(), _default_http_get(), discover_companies_by_cnae_and_city(), extract_hostname(), format_cnpj(), is_social_or_directory_url() (+22 more)

### Community 1 - "Google Maps Scraper Engine"
Cohesion: 0.07
Nodes (24): main(), open_browser(), collect_keywords(), contact_links(), dedupe(), enrich_emails(), work(), enrich_socials() (+16 more)

### Community 2 - "app.js"
Cohesion: 0.09
Nodes (27): ALL_LEADS, ALL_NICHES, applyQuickTab(), approvePriceFromModal(), clearAllFilters(), confirmAndSendAllReady(), confirmAndSendQueueItem(), CURRENT_LEADS (+19 more)

### Community 3 - "Site X-Ray & Tech Stack"
Cohesion: 0.11
Nodes (48): claim_next_outreach(), create_or_activate_agent_conversation(), create_price_consultation(), create_search_job(), deduplicate_existing_leads_db(), delete_agent_messages_after(), _deserialize_conversation(), _deserialize_job() (+40 more)

### Community 4 - "leads_router.py"
Cohesion: 0.17
Nodes (15): api_casadosdados_links(), api_get_executive_summary(), api_get_lead(), api_health(), api_list_jobs(), api_list_leads(), api_list_niches(), api_tool_lookup_cnpj() (+7 more)

### Community 5 - "🚀 Guia de Instalação e Uso Rápido — Painel de Busca"
Cohesion: 0.22
Nodes (8): 1. O instalador avisou que o Python não foi encontrado e o winget falhou, 2. Porta 8090 já em uso, 3. Como gerar um executável `.exe` independente?, 💻 Como Abrir no Dia a Dia, ⚙️ Dúvidas Frequentes & Resolução de Problemas, 🚀 Guia de Instalação e Uso Rápido — Painel de Busca, ⚡ Instalação em 1 Clique (Método Recomendado), 🛡️ Sistema com Auto-Cura Integrado

### Community 6 - "score_and_classify_lead"
Cohesion: 0.06
Nodes (17): score_and_classify_lead(), client(), client(), test_score_lead_for_complex_system_expansion(), test_score_lead_with_offline_website(), test_score_lead_without_website_and_free_domain(), client(), test_live_maps_scrape_piracicaba_utf8_safe() (+9 more)

### Community 7 - "maps_scraper.py"
Cohesion: 0.17
Nodes (15): build_keywords_for_job(), _clean_maps_address(), generate_sample_leads_for_niches(), geocode_city_embedded(), harvest_completed_docker_jobs_for_city(), infer_niche_slug_from_row(), normalize_whatsapp_br(), parse_csv_content_to_leads() (+7 more)

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

### Community 22 - "esc"
Cohesion: 0.25
Nodes (14): buildAgentFullDashboardHtml(), checkQuickDomain(), esc(), openManualLeadModal(), populateEmbeddedToolsFromLead(), renderAgentDashboardView(), renderAll4RightColumnScanners(), renderRegistroBrBox() (+6 more)

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

### Community 38 - "whatsapp_agent.py"
Cohesion: 0.08
Nodes (44): append_agent_message(), br_phone_variants(), get_active_conversation_by_chatid(), get_agent_conversation(), get_agent_settings(), list_agent_messages(), normalize_phone_digits(), phones_match_br() (+36 more)

### Community 39 - "agent_router.py"
Cohesion: 0.08
Nodes (31): AgentSettingsUpdate, AgentWebhookPayload, BossManualReplyRequest, ConversationControlRequest, LeadManagementUpdate, ManualLeadCreate, OutreachClaimRequest, OutreachEnqueueRequest (+23 more)

### Community 40 - "server.js"
Cohesion: 0.07
Nodes (32): express, pino, qrcode, qrcode-terminal, @whiskeysockets/baileys, dependencies, express, pino (+24 more)

### Community 41 - "outreach_generator.py"
Cohesion: 0.24
Nodes (8): build_executive_summary_report(), build_ready_report_for_lead(), generate_outreach_scripts(), process_and_save_lead(), test_generate_outreach_scripts_for_complex_system(), test_generate_outreach_scripts_for_missing_site_and_free_domain(), test_generate_outreach_scripts_humanized_tone_all_scenarios(), test_process_and_save_lead_pipeline()

### Community 42 - "2. Arquitetura Técnica e Componentes"
Cohesion: 0.18
Nodes (10): 1. Visão Geral e Objetivos, 2.1. Persistência SQLite (`app/database.py`), 2.2. Provedor Multi-IA Resiliente (`app/services/ai_provider.py`), 2.3. Motor do Agente WhatsApp (`app/services/whatsapp_agent.py`), 2.4. Micro-Bridge WhatsApp QR Code (`whatsapp_bridge/`), 2.5. Fábrica de Protótipos via IA (`app/services/prototype_generator.py`), 2.6. Rotas de API e Interface no Painel (`app/routers/agent_router.py` & `app/static/`), 2. Arquitetura Técnica e Componentes (+2 more)

### Community 43 - "api_create_and_run_job"
Cohesion: 0.22
Nodes (6): api_create_and_run_job(), build_casadosdados_links(), process_leads_batch(), _one(), test_build_casadosdados_links(), db_path()

### Community 44 - "check_scraper_engine_health"
Cohesion: 0.25
Nodes (4): api_start_engine(), check_scraper_engine_health(), list_engine_jobs(), start_scraper_engine_docker()

### Community 46 - "renderRows"
Cohesion: 0.36
Nodes (12): applyFilters(), hasNoSite(), isContacted(), labelStatus(), normStatus(), quickUpdateLeadStatus(), renderDecisionButtons(), renderDecisionButtonsHtml() (+4 more)

### Community 47 - "renderDetail"
Cohesion: 0.25
Nodes (11): cleanWhatsAppNumber(), enqueueSelectedLeads(), fmtRating(), markLeadContacted(), offerOf(), openLeadModal(), openWhatsApp(), readyReportOf() (+3 more)

### Community 48 - "api_tool_discover_companies_by_cnae"
Cohesion: 0.25
Nodes (6): api_create_manual_lead(), api_import_csv(), api_reanalyze_lead(), api_tool_discover_companies_by_cnae(), CnpjDiscoverRequest, CsvImportRequest

### Community 49 - "bindShortcuts"
Cohesion: 0.25
Nodes (9): bindShortcuts(), closeDetailOverlay(), closeLeadModal(), closeQueueModal(), goToPage(), moveSelection(), onPageSizeChange(), selectLead() (+1 more)

### Community 50 - "loadHealthAndStats"
Cohesion: 0.40
Nodes (6): buildPaginationButtons(), enqueueSingleLead(), fmtInt(), loadHealthAndStats(), renderPagination(), runSearchJob()

### Community 51 - "loadLeads"
Cohesion: 0.40
Nodes (6): closeManualModal(), loadLeads(), renderError(), runEmbeddedCnpjLookup(), submitCsvImport(), submitManualLead()

### Community 52 - "initDashboard"
Cohesion: 0.33
Nodes (6): initDashboard(), initTheme(), loadNiches(), renderNichesGrid(), renderSkeleton(), selectAllNiches()

## Knowledge Gaps
- **2 isolated node(s):** `README Painel de Busca`, `Sprint Atual`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 273 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `create_app()` connect `Site X-Ray & Tech Stack` to `score_and_classify_lead`, `agent_router.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **What connects `README Painel de Busca`, `Sprint Atual` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Site X-Ray & Tech Stack` be split into smaller, more focused modules?**
  _Cohesion score 0.07138535995160314 - nodes in this community are weakly interconnected._
- **Why does `moeda_br()` connect `whatsapp_agent.py` to `2. Arquitetura Técnica e Componentes`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Should `Google Maps Scraper Engine` be split into smaller, more focused modules?**
  _Cohesion score 0.0660377358490566 - nodes in this community are weakly interconnected._
- **Why does `2.3. Motor do Agente WhatsApp (`app/services/whatsapp_agent.py`)` connect `2. Arquitetura Técnica e Componentes` to `whatsapp_agent.py`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Should `app.js` be split into smaller, more focused modules?**
  _Cohesion score 0.0873440285204991 - nodes in this community are weakly interconnected._