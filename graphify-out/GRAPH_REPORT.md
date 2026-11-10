# Graph Report - Painel de Busca  (2026-11-10)

## Corpus Check
- 65 files · ~61,386 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: .bat 5, (none) 1, .ico 1)

## Summary
- 815 nodes · 2013 edges · 53 communities (44 shown, 9 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 49 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `12d7ba68`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- business_discovery.py
- Google Maps Scraper Engine
- app.js
- generate_outreach_scripts
- maps_scraper.py
- 🚀 Guia de Instalação e Uso Rápido — Painel de Busca
- score_and_classify_lead
- test_deal_ranker.py
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
- database.py
- agent_router.py
- server.js
- leads_router.py
- 2. Arquitetura Técnica e Componentes
- process_and_save_lead
- test_maps_scraper.py
- outreach_generator.py
- renderRows
- renderDetail
- test_installer_integrity.py
- bindShortcuts
- loadHealthAndStats
- loadLeads
- initDashboard

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 44 edges
2. `get_lead()` - 22 edges
3. `get_agent_settings()` - 21 edges
4. `suggest_price()` - 21 edges
5. `generate_prototype_for_lead()` - 20 edges
6. `process_and_save_lead()` - 19 edges
7. `handle_boss_incoming_message()` - 19 edges
8. `create_app()` - 18 edges
9. `process_conversation_turn()` - 18 edges
10. `esc()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `2.3. Motor do Agente WhatsApp (`app/services/whatsapp_agent.py`)` --references--> `moeda_br()`  [INFERRED]
  docs/superpowers/specs/2026-11-09-whatsapp-agent-prototype-design.md → app/services/whatsapp_agent.py
- `test_build_casadosdados_links()` --calls--> `build_casadosdados_links()`  [INFERRED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `test_is_social_or_directory_url()` --calls--> `is_social_or_directory_url()`  [INFERRED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `test_suggest_domain_br_strips_accents_and_stopwords()` --calls--> `suggest_domain_br()`  [INFERRED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `test_check_site_availability_and_ssl_offline_domain()` --calls--> `check_site_availability_and_ssl()`  [INFERRED]
  tests/test_business_discovery.py → app/services/business_discovery.py

## Import Cycles
- None detected.

## Communities (53 total, 9 thin omitted)

### Community 0 - "business_discovery.py"
Cohesion: 0.07
Nodes (29): check_registro_br_availability(), check_site_availability_and_ssl(), _default_http_get(), extract_hostname(), format_cnpj(), is_social_or_directory_url(), lookup_cnpj_embedded(), _parse_rdap_vcard_name() (+21 more)

### Community 1 - "Google Maps Scraper Engine"
Cohesion: 0.07
Nodes (21): main(), open_browser(), collect_keywords(), contact_links(), dedupe(), enrich_emails(), work(), enrich_socials() (+13 more)

### Community 2 - "app.js"
Cohesion: 0.09
Nodes (27): ALL_LEADS, ALL_NICHES, applyQuickTab(), approvePriceFromModal(), clearAllFilters(), confirmAndSendAllReady(), confirmAndSendQueueItem(), CURRENT_LEADS (+19 more)

### Community 3 - "generate_outreach_scripts"
Cohesion: 0.17
Nodes (10): init_db(), build_ready_report_for_lead(), generate_outreach_scripts(), process_leads_batch(), _one(), db_path(), test_generate_outreach_scripts_for_complex_system(), test_generate_outreach_scripts_for_missing_site_and_free_domain() (+2 more)

### Community 4 - "maps_scraper.py"
Cohesion: 0.14
Nodes (13): api_create_and_run_job(), api_start_engine(), api_tool_maps_engine(), check_scraper_engine_health(), _clean_maps_address(), delete_engine_job(), generate_sample_leads_for_niches(), geocode_city_embedded() (+5 more)

### Community 5 - "🚀 Guia de Instalação e Uso Rápido — Painel de Busca"
Cohesion: 0.22
Nodes (8): 1. O instalador avisou que o Python não foi encontrado e o winget falhou, 2. Porta 8090 já em uso, 3. Como gerar um executável `.exe` independente?, 💻 Como Abrir no Dia a Dia, ⚙️ Dúvidas Frequentes & Resolução de Problemas, 🚀 Guia de Instalação e Uso Rápido — Painel de Busca, ⚡ Instalação em 1 Clique (Método Recomendado), 🛡️ Sistema com Auto-Cura Integrado

### Community 6 - "score_and_classify_lead"
Cohesion: 0.07
Nodes (17): purge_simulated_leads(), create_app(), client(), client(), test_ranking_endpoint_groups_by_real_segment_and_filters(), client(), test_live_maps_scrape_piracicaba_utf8_safe(), test_piracicaba_search_job_no_charmap_error_and_ready_reports() (+9 more)

### Community 7 - "test_deal_ranker.py"
Cohesion: 0.09
Nodes (46): api_leads_ranking(), _band_reais(), build_outreach_plan(), _catalog(), _cell(), compact_item(), contact_channel(), detect_segment() (+38 more)

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

### Community 38 - "database.py"
Cohesion: 0.05
Nodes (100): append_agent_message(), br_phone_variants(), claim_next_outreach(), create_or_activate_agent_conversation(), create_price_consultation(), create_search_job(), deduplicate_existing_leads_db(), delete_agent_messages_after() (+92 more)

### Community 39 - "agent_router.py"
Cohesion: 0.12
Nodes (19): AgentSettingsUpdate, AgentWebhookPayload, BossManualReplyRequest, ConversationControlRequest, LeadManagementUpdate, ManualLeadCreate, OutreachClaimRequest, OutreachEnqueueRequest (+11 more)

### Community 40 - "server.js"
Cohesion: 0.05
Nodes (51): express, pino, qrcode, qrcode-terminal, @whiskeysockets/baileys, dependencies, express, pino (+43 more)

### Community 41 - "leads_router.py"
Cohesion: 0.16
Nodes (16): api_casadosdados_links(), api_check_registro_br(), api_get_executive_summary(), api_get_lead(), api_health(), api_list_jobs(), api_list_leads(), api_list_niches() (+8 more)

### Community 42 - "2. Arquitetura Técnica e Componentes"
Cohesion: 0.15
Nodes (11): moeda_br(), 1. Visão Geral e Objetivos, 2.1. Persistência SQLite (`app/database.py`), 2.2. Provedor Multi-IA Resiliente (`app/services/ai_provider.py`), 2.3. Motor do Agente WhatsApp (`app/services/whatsapp_agent.py`), 2.4. Micro-Bridge WhatsApp QR Code (`whatsapp_bridge/`), 2.5. Fábrica de Protótipos via IA (`app/services/prototype_generator.py`), 2.6. Rotas de API e Interface no Painel (`app/routers/agent_router.py` & `app/static/`) (+3 more)

### Community 43 - "process_and_save_lead"
Cohesion: 0.17
Nodes (9): api_create_manual_lead(), api_import_csv(), api_reanalyze_lead(), api_tool_discover_companies_by_cnae(), CnpjDiscoverRequest, CsvImportRequest, build_casadosdados_links(), discover_companies_by_cnae_and_city() (+1 more)

### Community 44 - "test_maps_scraper.py"
Cohesion: 0.22
Nodes (9): build_keywords_for_job(), normalize_whatsapp_br(), parse_csv_content_to_leads(), get_niches_by_slugs(), test_build_keywords_for_job(), test_default_niches_catalog_completeness(), test_generate_sample_leads_for_niches(), test_normalize_whatsapp_br() (+1 more)

### Community 45 - "outreach_generator.py"
Cohesion: 0.26
Nodes (5): score_and_classify_lead(), build_executive_summary_report(), test_score_lead_for_complex_system_expansion(), test_score_lead_with_offline_website(), test_score_lead_without_website_and_free_domain()

### Community 46 - "renderRows"
Cohesion: 0.36
Nodes (12): applyFilters(), hasNoSite(), isContacted(), labelStatus(), normStatus(), quickUpdateLeadStatus(), renderDecisionButtons(), renderDecisionButtonsHtml() (+4 more)

### Community 47 - "renderDetail"
Cohesion: 0.25
Nodes (11): cleanWhatsAppNumber(), enqueueSelectedLeads(), fmtRating(), markLeadContacted(), offerOf(), openLeadModal(), openWhatsApp(), readyReportOf() (+3 more)

### Community 48 - "test_installer_integrity.py"
Cohesion: 0.70
Nodes (3): test_gitignore_protects_binaries_and_builds(), test_installer_assets_exist(), test_installer_scripts_contain_key_routines()

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
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 292 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `create_app()` connect `score_and_classify_lead` to `generate_outreach_scripts`, `database.py`, `test_deal_ranker.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **What connects `README Painel de Busca`, `Sprint Atual` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `business_discovery.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07474747474747474 - nodes in this community are weakly interconnected._
- **Why does `moeda_br()` connect `2. Arquitetura Técnica e Componentes` to `database.py`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Should `Google Maps Scraper Engine` be split into smaller, more focused modules?**
  _Cohesion score 0.07400555041628122 - nodes in this community are weakly interconnected._
- **Should `app.js` be split into smaller, more focused modules?**
  _Cohesion score 0.0873440285204991 - nodes in this community are weakly interconnected._
- **Should `maps_scraper.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14153846153846153 - nodes in this community are weakly interconnected._