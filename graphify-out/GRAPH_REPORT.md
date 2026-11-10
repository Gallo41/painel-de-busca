# Graph Report - Painel de Busca  (2026-11-10)

## Corpus Check
- 62 files · ~57,525 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: .bat 5, (none) 1, .ico 1)

## Summary
- 752 nodes · 1803 edges · 51 communities (42 shown, 9 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 48 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `296f0b1d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_full_xray_for_lead
- Google Maps Scraper Engine
- app.js
- Site X-Ray & Tech Stack
- leads_router.py
- 🚀 Guia de Instalação e Uso Rápido — Painel de Busca
- score_and_classify_lead
- business_discovery.py
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
- os
- 2. Arquitetura Técnica e Componentes
- outreach_generator.py
- build_casadosdados_links
- renderRows
- renderDetail
- bindShortcuts
- loadHealthAndStats
- loadLeads
- initDashboard

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 44 edges
2. `get_lead()` - 22 edges
3. `get_agent_settings()` - 21 edges
4. `generate_prototype_for_lead()` - 20 edges
5. `process_and_save_lead()` - 19 edges
6. `handle_boss_incoming_message()` - 19 edges
7. `process_conversation_turn()` - 18 edges
8. `esc()` - 18 edges
9. `_now_iso()` - 17 edges
10. `run_live_maps_scrape()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `2.3. Motor do Agente WhatsApp (`app/services/whatsapp_agent.py`)` --references--> `moeda_br()`  [INFERRED]
  docs/superpowers/specs/2026-11-09-whatsapp-agent-prototype-design.md → app/services/whatsapp_agent.py
- `test_is_social_or_directory_url()` --calls--> `is_social_or_directory_url()`  [INFERRED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `test_suggest_domain_br_strips_accents_and_stopwords()` --calls--> `suggest_domain_br()`  [INFERRED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `test_check_site_availability_and_ssl_offline_domain()` --calls--> `check_site_availability_and_ssl()`  [INFERRED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `test_check_registro_br_availability_with_mock()` --calls--> `check_registro_br_availability()`  [INFERRED]
  tests/test_business_discovery.py → app/services/business_discovery.py

## Import Cycles
- None detected.

## Communities (51 total, 9 thin omitted)

### Community 0 - "run_full_xray_for_lead"
Cohesion: 0.14
Nodes (14): check_site_availability_and_ssl(), extract_hostname(), is_social_or_directory_url(), build_external_xray_links(), check_wayback_machine(), _default_wayback_get(), detect_cms_and_tech_stack(), run_embedded_site_xray_by_url() (+6 more)

### Community 1 - "Google Maps Scraper Engine"
Cohesion: 0.05
Nodes (38): build_keywords_for_job(), check_scraper_engine_health(), _clean_maps_address(), delete_engine_job(), generate_sample_leads_for_niches(), geocode_city_embedded(), harvest_completed_docker_jobs_for_city(), infer_niche_slug_from_row() (+30 more)

### Community 2 - "app.js"
Cohesion: 0.09
Nodes (27): ALL_LEADS, ALL_NICHES, applyQuickTab(), approvePriceFromModal(), clearAllFilters(), confirmAndSendAllReady(), confirmAndSendQueueItem(), CURRENT_LEADS (+19 more)

### Community 3 - "Site X-Ray & Tech Stack"
Cohesion: 0.10
Nodes (52): append_agent_message(), br_phone_variants(), claim_next_outreach(), create_or_activate_agent_conversation(), create_price_consultation(), create_search_job(), deduplicate_existing_leads_db(), delete_agent_messages_after() (+44 more)

### Community 4 - "leads_router.py"
Cohesion: 0.10
Nodes (25): api_check_registro_br(), api_create_and_run_job(), api_create_manual_lead(), api_get_executive_summary(), api_get_lead(), api_health(), api_import_csv(), api_list_jobs() (+17 more)

### Community 5 - "🚀 Guia de Instalação e Uso Rápido — Painel de Busca"
Cohesion: 0.22
Nodes (8): 1. O instalador avisou que o Python não foi encontrado e o winget falhou, 2. Porta 8090 já em uso, 3. Como gerar um executável `.exe` independente?, 💻 Como Abrir no Dia a Dia, ⚙️ Dúvidas Frequentes & Resolução de Problemas, 🚀 Guia de Instalação e Uso Rápido — Painel de Busca, ⚡ Instalação em 1 Clique (Método Recomendado), 🛡️ Sistema com Auto-Cura Integrado

### Community 6 - "score_and_classify_lead"
Cohesion: 0.08
Nodes (17): score_and_classify_lead(), client(), test_score_lead_for_complex_system_expansion(), test_score_lead_with_offline_website(), test_score_lead_without_website_and_free_domain(), client(), test_live_maps_scrape_piracicaba_utf8_safe(), test_piracicaba_search_job_no_charmap_error_and_ready_reports() (+9 more)

### Community 7 - "business_discovery.py"
Cohesion: 0.17
Nodes (11): check_registro_br_availability(), _default_http_get(), discover_companies_by_cnae_and_city(), format_cnpj(), lookup_cnpj_embedded(), _parse_rdap_vcard_name(), _resolve_dns_and_ssl_embedded(), _strip_accents() (+3 more)

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
Nodes (40): get_agent_conversation(), get_agent_settings(), list_agent_messages(), normalize_phone_digits(), phones_match_br(), update_agent_conversation(), api_get_conversation_detail(), _call_gemini_native() (+32 more)

### Community 39 - "agent_router.py"
Cohesion: 0.07
Nodes (33): AgentSettingsUpdate, AgentWebhookPayload, BossManualReplyRequest, ConversationControlRequest, LeadManagementUpdate, ManualLeadCreate, OutreachClaimRequest, OutreachEnqueueRequest (+25 more)

### Community 40 - "server.js"
Cohesion: 0.06
Nodes (48): express, pino, qrcode, qrcode-terminal, @whiskeysockets/baileys, dependencies, express, pino (+40 more)

### Community 41 - "os"
Cohesion: 0.15
Nodes (6): main(), open_browser(), client(), test_gitignore_protects_binaries_and_builds(), test_installer_assets_exist(), test_installer_scripts_contain_key_routines()

### Community 42 - "2. Arquitetura Técnica e Componentes"
Cohesion: 0.18
Nodes (10): 1. Visão Geral e Objetivos, 2.1. Persistência SQLite (`app/database.py`), 2.2. Provedor Multi-IA Resiliente (`app/services/ai_provider.py`), 2.3. Motor do Agente WhatsApp (`app/services/whatsapp_agent.py`), 2.4. Micro-Bridge WhatsApp QR Code (`whatsapp_bridge/`), 2.5. Fábrica de Protótipos via IA (`app/services/prototype_generator.py`), 2.6. Rotas de API e Interface no Painel (`app/routers/agent_router.py` & `app/static/`), 2. Arquitetura Técnica e Componentes (+2 more)

### Community 43 - "outreach_generator.py"
Cohesion: 0.23
Nodes (9): build_ready_report_for_lead(), generate_outreach_scripts(), process_and_save_lead(), process_leads_batch(), _one(), test_generate_outreach_scripts_for_complex_system(), test_generate_outreach_scripts_for_missing_site_and_free_domain(), test_generate_outreach_scripts_humanized_tone_all_scenarios() (+1 more)

### Community 44 - "build_casadosdados_links"
Cohesion: 0.18
Nodes (7): api_casadosdados_links(), build_casadosdados_links(), test_build_casadosdados_links(), test_check_registro_br_availability_with_mock(), test_check_site_availability_and_ssl_offline_domain(), test_is_social_or_directory_url(), test_suggest_domain_br_strips_accents_and_stopwords()

### Community 46 - "renderRows"
Cohesion: 0.36
Nodes (12): applyFilters(), hasNoSite(), isContacted(), labelStatus(), normStatus(), quickUpdateLeadStatus(), renderDecisionButtons(), renderDecisionButtonsHtml() (+4 more)

### Community 47 - "renderDetail"
Cohesion: 0.25
Nodes (11): cleanWhatsAppNumber(), enqueueSelectedLeads(), fmtRating(), markLeadContacted(), offerOf(), openLeadModal(), openWhatsApp(), readyReportOf() (+3 more)

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
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 280 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `create_app()` connect `Site X-Ray & Tech Stack` to `os`, `score_and_classify_lead`, `agent_router.py`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **What connects `README Painel de Busca`, `Sprint Atual` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `run_full_xray_for_lead` be split into smaller, more focused modules?**
  _Cohesion score 0.13538461538461538 - nodes in this community are weakly interconnected._
- **Why does `moeda_br()` connect `whatsapp_agent.py` to `2. Arquitetura Técnica e Componentes`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Should `Google Maps Scraper Engine` be split into smaller, more focused modules?**
  _Cohesion score 0.05405405405405406 - nodes in this community are weakly interconnected._
- **Why does `2.3. Motor do Agente WhatsApp (`app/services/whatsapp_agent.py`)` connect `2. Arquitetura Técnica e Componentes` to `whatsapp_agent.py`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Should `app.js` be split into smaller, more focused modules?**
  _Cohesion score 0.0873440285204991 - nodes in this community are weakly interconnected._