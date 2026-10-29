# Graph Report - Painel de Busca  (2026-10-29)

## Corpus Check
- Corpus is ~20,894 words - fits in a single context window. You may not need a graph.

## Summary
- 274 nodes · 697 edges · 14 communities (9 shown, 5 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Site X-Ray & Tech Stack
- Google Maps Scraper Engine
- Business Discovery & RDAP
- Site X-Ray & Tech Stack
- SQLite Persistence & Lead Scoring
- Outreach Scripts & Queue
- Outreach Scripts & Queue
- Outreach Scripts & Queue
- Cluster 8: Implementation Plan 10-S

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 21 edges
2. `process_and_save_lead()` - 17 edges
3. `get_lead()` - 14 edges
4. `run_live_maps_scrape()` - 14 edges
5. `run_full_xray_for_lead()` - 14 edges
6. `main()` - 14 edges
7. `api_create_and_run_job()` - 13 edges
8. `is_social_or_directory_url()` - 12 edges
9. `check_registro_br_availability()` - 12 edges
10. `suggest_domain_br()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `test_normalize_whatsapp_br()` --calls--> `normalize_whatsapp_br()`  [EXTRACTED]
  tests/test_maps_scraper.py → app/services/maps_scraper.py
- `test_is_social_or_directory_url()` --calls--> `is_social_or_directory_url()`  [EXTRACTED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `test_suggest_domain_br_strips_accents_and_stopwords()` --calls--> `suggest_domain_br()`  [EXTRACTED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `test_check_site_availability_and_ssl_offline_domain()` --calls--> `check_site_availability_and_ssl()`  [EXTRACTED]
  tests/test_business_discovery.py → app/services/business_discovery.py
- `test_build_casadosdados_links()` --calls--> `build_casadosdados_links()`  [EXTRACTED]
  tests/test_business_discovery.py → app/services/business_discovery.py

## Import Cycles
- None detected.

## Communities (14 total, 5 thin omitted)

### Community 0 - "Site X-Ray & Tech Stack"
Cohesion: 0.10
Nodes (23): build_casadosdados_links(), check_registro_br_availability(), check_site_availability_and_ssl(), _default_http_get(), extract_hostname(), is_social_or_directory_url(), _strip_accents(), suggest_domain_br() (+15 more)

### Community 1 - "Google Maps Scraper Engine"
Cohesion: 0.09
Nodes (20): run_live_maps_scrape(), collect_keywords(), contact_links(), dedupe(), enrich_emails(), work(), enrich_socials(), work() (+12 more)

### Community 2 - "Business Discovery & RDAP"
Cohesion: 0.11
Nodes (25): api_casadosdados_links(), api_check_registro_br(), api_create_and_run_job(), api_create_manual_lead(), api_get_lead(), api_health(), api_import_csv(), api_list_jobs() (+17 more)

### Community 3 - "Site X-Ray & Tech Stack"
Cohesion: 0.22
Nodes (26): claim_next_outreach(), create_search_job(), _deserialize_job(), _deserialize_lead(), _deserialize_outreach(), enqueue_outreach(), get_connection(), get_dashboard_stats() (+18 more)

### Community 4 - "SQLite Persistence & Lead Scoring"
Cohesion: 0.10
Nodes (21): ALL_NICHES, closeManualModal(), CURRENT_LEADS, enqueueSelectedLeads(), enqueueSingleLead(), initDashboard(), loadHealthAndStats(), loadLeads() (+13 more)

### Community 5 - "Outreach Scripts & Queue"
Cohesion: 0.12
Nodes (11): LeadManagementUpdate, ManualLeadCreate, OutreachClaimRequest, OutreachEnqueueRequest, OutreachStatusUpdate, SearchJobRequest, api_claim_next_outreach(), api_enqueue_outreach() (+3 more)

### Community 6 - "Outreach Scripts & Queue"
Cohesion: 0.15
Nodes (12): init_db(), score_and_classify_lead(), normalize_whatsapp_br(), generate_outreach_scripts(), process_and_save_lead(), db_path(), test_score_lead_for_complex_system_expansion(), test_score_lead_with_offline_website() (+4 more)

### Community 7 - "Outreach Scripts & Queue"
Cohesion: 0.17
Nodes (3): create_app(), client(), client()

### Community 8 - "Cluster 8: Implementation Plan 10-S"
Cohesion: 0.50
Nodes (4): Implementation Plan 10-Step Sprint, README & 8 Ferramentas de Raio-X, Painel de Busca Architectural Spec, Sprint Atual Delbor (10% Checkpoints)

## Knowledge Gaps
- **2 isolated node(s):** `Sprint Atual Delbor (10% Checkpoints)`, `README & 8 Ferramentas de Raio-X`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 80 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_live_maps_scrape()` connect `Google Maps Scraper Engine` to `Business Discovery & RDAP`, `Outreach Scripts & Queue`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **What connects `Sprint Atual Delbor (10% Checkpoints)`, `README & 8 Ferramentas de Raio-X` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Site X-Ray & Tech Stack` be split into smaller, more focused modules?**
  _Cohesion score 0.09696969696969697 - nodes in this community are weakly interconnected._
- **Why does `process_and_save_lead()` connect `Outreach Scripts & Queue` to `Site X-Ray & Tech Stack`, `Business Discovery & RDAP`, `Site X-Ray & Tech Stack`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Should `Google Maps Scraper Engine` be split into smaller, more focused modules?**
  _Cohesion score 0.08710801393728224 - nodes in this community are weakly interconnected._
- **Why does `check_registro_br_availability()` connect `Site X-Ray & Tech Stack` to `Business Discovery & RDAP`, `Site X-Ray & Tech Stack`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Should `Business Discovery & RDAP` be split into smaller, more focused modules?**
  _Cohesion score 0.1141025641025641 - nodes in this community are weakly interconnected._