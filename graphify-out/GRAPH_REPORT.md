# Graph Report - Painel de Busca  (2026-10-31)

## Corpus Check
- Corpus is ~26,895 words - fits in a single context window. You may not need a graph.

## Summary
- 373 nodes · 888 edges · 22 communities (14 shown, 8 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Cluster 0
- Cluster 1
- Cluster 2
- Cluster 3
- Cluster 4
- Cluster 5
- Cluster 6
- Cluster 7
- Cluster 8
- Cluster 9
- Cluster 10
- Cluster 11
- Cluster 12
- Cluster 13
- Cluster 18
- Cluster 19
- Cluster 20
- Cluster 21

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 21 edges
2. `process_and_save_lead()` - 19 edges
3. `run_full_xray_for_lead()` - 17 edges
4. `check_registro_br_availability()` - 15 edges
5. `main()` - 15 edges
6. `get_lead()` - 14 edges
7. `suggest_domain_br()` - 14 edges
8. `lookup_cnpj_embedded()` - 14 edges
9. `run_live_maps_scrape()` - 14 edges
10. `api_create_and_run_job()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `Repositório Oficial` --references--> `main()`  [INFERRED]
  .agents/rules/git-auto-commit.md → scripts/scrape.py
- `test_process_and_save_lead_pipeline()` --calls--> `init_db()`  [EXTRACTED]
  tests/test_outreach_generator.py → app/database.py
- `test_is_social_or_directory_url()` --calls--> `is_social_or_directory_url()`  [EXTRACTED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `test_suggest_domain_br_strips_accents_and_stopwords()` --calls--> `suggest_domain_br()`  [EXTRACTED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `test_check_site_availability_and_ssl_offline_domain()` --calls--> `check_site_availability_and_ssl()`  [EXTRACTED]
  tests/test_business_discovery.py → app/services/business_discovery.py

## Import Cycles
- None detected.

## Communities (22 total, 8 thin omitted)

### Community 0 - "Cluster 0"
Cohesion: 0.08
Nodes (31): build_casadosdados_links(), check_registro_br_availability(), check_site_availability_and_ssl(), _default_http_get(), discover_companies_by_cnae_and_city(), extract_hostname(), format_cnpj(), is_social_or_directory_url() (+23 more)

### Community 1 - "Cluster 1"
Cohesion: 0.07
Nodes (24): Diretrizes de Commit Automático, Regra Mandatória: Commit e Sincronização Automática com GitHub, Repositório Oficial, api_export_outreach_ready(), run_live_maps_scrape(), collect_keywords(), contact_links(), dedupe() (+16 more)

### Community 2 - "Cluster 2"
Cohesion: 0.09
Nodes (35): ALL_NICHES, checkQuickDomain(), closeManualModal(), CURRENT_LEADS, enqueueSelectedLeads(), enqueueSingleLead(), initDashboard(), inspectLeadInEmbeddedTools() (+27 more)

### Community 3 - "Cluster 3"
Cohesion: 0.19
Nodes (28): claim_next_outreach(), create_search_job(), _deserialize_job(), _deserialize_lead(), _deserialize_outreach(), enqueue_outreach(), get_connection(), get_dashboard_stats() (+20 more)

### Community 4 - "Cluster 4"
Cohesion: 0.12
Nodes (22): api_casadosdados_links(), api_check_registro_br(), api_create_and_run_job(), api_create_manual_lead(), api_get_lead(), api_health(), api_import_csv(), api_list_jobs() (+14 more)

### Community 5 - "Cluster 5"
Cohesion: 0.14
Nodes (15): build_keywords_for_job(), check_scraper_engine_health(), delete_engine_job(), generate_sample_leads_for_niches(), geocode_city_embedded(), list_engine_jobs(), normalize_whatsapp_br(), parse_csv_content_to_leads() (+7 more)

### Community 6 - "Cluster 6"
Cohesion: 0.11
Nodes (3): create_app(), client(), client()

### Community 7 - "Cluster 7"
Cohesion: 0.15
Nodes (11): LeadManagementUpdate, ManualLeadCreate, OutreachClaimRequest, OutreachEnqueueRequest, OutreachStatusUpdate, SearchJobRequest, api_update_lead(), api_claim_next_outreach() (+3 more)

### Community 8 - "Cluster 8"
Cohesion: 0.19
Nodes (9): score_and_classify_lead(), generate_outreach_scripts(), process_and_save_lead(), test_score_lead_for_complex_system_expansion(), test_score_lead_with_offline_website(), test_score_lead_without_website_and_free_domain(), test_generate_outreach_scripts_for_complex_system(), test_generate_outreach_scripts_for_missing_site_and_free_domain() (+1 more)

### Community 9 - "Cluster 9"
Cohesion: 0.14
Nodes (13): Global Constraints, Painel de Busca & Prospecção de Leads Implementation Plan, Review Focus, Task 10 (100%): Grafo de Conhecimento Graphify (`graphify-out/`), Documentação (`README.md`) e Validação Final, Task 1 (10%): Onboarding Padrão Delbor, Repositório GitHub, Spec e Plano, Task 2 (20%): Camada de Banco de Dados SQLite e Modelos (`app/database.py`), Task 3 (30%): Catálogo de Nichos & Integração com `google-maps-scraper` (`app/services/maps_scraper.py`), Task 4 (40%): Módulo "Achar o Negócio" — Registro.br RDAP, Health Check e Casa dos Dados (`app/services/business_discovery.py`) (+5 more)

### Community 10 - "Cluster 10"
Cohesion: 0.22
Nodes (8): 1. Iniciar o Painel Web, 2. (Opcional) Subir o Motor Docker do Google Maps Scraper, 🛠️ As 8 Ferramentas Integradas no Motor, 🤖 Base Pré-Pronta para o Projeto Futuro de Automação de Contato, Coluna 1 — Achar o Negócio (`app/services/business_discovery.py` + `maps_scraper.py`), Coluna 2 — Raio-X do Site Atual (`app/services/site_xray.py`), 🚀 Como Usar no Dia a Dia, Painel de Busca, Raio-X & Prospecção de Leads (Freelancers)

### Community 11 - "Cluster 11"
Cohesion: 0.25
Nodes (7): 1. Visão Geral e Objetivo, 2. Arquitetura do Sistema, 3. Modelo de Dados (SQLite), 4. Tratamento de Erros e Limites, Coluna 1 — Achar o Negócio (`business_discovery`), Coluna 2 — Raio-X do Site Atual (`site_xray`), Especificação Arquitetural — Painel de Busca, Raio-X e Prospecção de Leads

### Community 12 - "Cluster 12"
Cohesion: 0.33
Nodes (5): 1. Registro Obrigatório no Início da Tarefa / Sprint, 2. Checkpoint Incremental de 10 em 10% (Salvamento Seguro), 3. Economia de Tokens com Graphify e Obsidian, 4. Sincronismo Antigravity <-> Claudinho / OpenCode, Regra Mandatória: Sprint, Checkpoint 10% e Sincronismo com Obsidian

### Community 13 - "Cluster 13"
Cohesion: 0.33
Nodes (5): 📋 Checklist de Progresso Obrigatório (Regra dos 10%), 📝 Diário de Bordo & Checkpoints Salvos (10% em 10%), 🎯 Objetivo da Sprint, Próximo passo, Sprint Atual: Embutir as 8 Ferramentas Nativamente no Painel (Zero Links Externos) & Motor Docker Ativo

## Knowledge Gaps
- **4 isolated node(s):** `Plan Painel de Busca`, `README Painel de Busca`, `Spec Painel de Busca`, `Sprint Atual`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 132 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_live_maps_scrape()` connect `Cluster 1` to `Cluster 4`, `Cluster 5`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **What connects `Plan Painel de Busca`, `README Painel de Busca`, `Spec Painel de Busca` to the rest of the system?**
  _4 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Cluster 0` be split into smaller, more focused modules?**
  _Cohesion score 0.0807909604519774 - nodes in this community are weakly interconnected._
- **Why does `process_and_save_lead()` connect `Cluster 8` to `Cluster 0`, `Cluster 3`, `Cluster 4`, `Cluster 5`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Should `Cluster 1` be split into smaller, more focused modules?**
  _Cohesion score 0.0726950354609929 - nodes in this community are weakly interconnected._
- **Why does `main()` connect `Cluster 1` to `Cluster 3`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Should `Cluster 2` be split into smaller, more focused modules?**
  _Cohesion score 0.09302325581395349 - nodes in this community are weakly interconnected._