# Wiki de Arquitetura — Painel de Busca (`graphify-out/wiki/index.md`)

Este índice unifica o contexto arquitetural para **Antigravity, Claudinho, OpenCode, Codex e Obsidian**.

## 1. Visão Geral e Repositório
- **Projeto**: Painel de Busca, Raio-X das 8 Ferramentas e Prospecção de Leads
- **Diretório Local**: `c:\Projetos Quecine\Painel de Busca`
- **Repositório GitHub**: `https://github.com/Gallo41/painel-de-busca.git`
- **Grafo Completo**: `graphify-out/graph.json` | `graphify-out/GRAPH_REPORT.md` | `graphify-out/graph.html` (274 nós, 697 arestas, 14 comunidades)

## 2. Módulos Principais (God Nodes)
1. **Persistência SQLite (`app/database.py`)**:
   - `get_connection()`, `init_db()`, `upsert_niches()`, `create_search_job()`, `upsert_lead()`, `update_lead_xray_and_score()`, `enqueue_outreach()`, `claim_next_outreach()`, `update_outreach_status()`.
2. **Integração Google Maps Scraper (`app/services/maps_scraper.py` + `scripts/scrape.py`)**:
   - Conecta ao container Docker `gosom/google-maps-scraper` (`http://localhost:8080`) e executa geocoding, grid, extração de e-mails profundos e redes sociais (`instagram`, `facebook`, `linkedin`).
   - Possui modo de simulação realista (`generate_sample_leads_for_niches`) e importador CSV (`parse_csv_content_to_leads`).
3. **Descoberta de Negócios (`app/services/business_discovery.py`)**:
   - `suggest_domain_br()` + `check_registro_br_availability()`: consulta oficial RDAP (`https://rdap.registro.br/domain/<slug>.com.br`).
   - `check_site_availability_and_ssl()`: equivalente ao `downforeveryoneorjustme.com` + checagem HTTPS/SSL.
   - `build_casadosdados_links()`: filtros estruturados por CNAE + Cidade para `casadosdados.com.br`.
4. **Raio-X do Site Atual (`app/services/site_xray.py`)**:
   - `detect_cms_and_tech_stack()`: equivalente local ao `builtwith.com`, `wappalyzer.com` e `whatcms.org` + detecção de necessidade de **Sistemas Mais Complexos**.
   - `check_wayback_machine()`: consulta API oficial do `web.archive.org`.
   - `run_full_xray_for_lead()`: orquestra todas as 8 ferramentas.
5. **Lead Scoring & Gerador de Abordagens (`app/services/lead_scorer.py` & `app/services/outreach_generator.py`)**:
   - `score_and_classify_lead()`: calcula score 0–100 e classifica em `SEM_SITE`, `DOMINIO_LIVRE`, `SITE_FORA_DO_AR`, `OPORTUNIDADE_SISTEMA` ou `SITE_AMADOR_ANTIGO`.
   - `generate_outreach_scripts()` & `process_and_save_lead()`: cria mensagens prontas para WhatsApp (link 1-clique `wa.me`), E-mail e Instagram DM + `automation_payload`.
6. **API REST & Automação Futura (`app/main.py`, `app/routers/leads_router.py`, `app/routers/outreach_router.py`)**:
   - Endpoints para o Dashboard e fila atômica `/api/outreach/enqueue`, `/api/outreach/claim`, `/api/outreach/{id}/status` para futuros bots de WhatsApp/n8n.
