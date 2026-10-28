# Painel de Busca & Prospecção de Leads Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task following the Delbor 10% Checkpoint Protocol. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir um Painel Web Local completo (FastAPI + SQLite + Raio-X das 8 ferramentas + Gerador de Scripts de Abordagem + API de Outreach futura) integrado à skill `google-maps-scraper`.

**Architecture:** Backend modular em Python (FastAPI) com persistência em SQLite (`app/database.py`), serviços desacoplados para Scraping do Google Maps (`maps_scraper.py`), Descoberta de Negócios (`business_discovery.py` com RDAP Registro.br, Health Check e Casa dos Dados), Raio-X Tecnológico (`site_xray.py` com detector de CMS/Stack, Wayback Machine e potencial para Sistemas Complexos), Lead Scoring (`lead_scorer.py`), Gerador de Mensagens (`outreach_generator.py`) e API REST para automação futura de disparo (`outreach_api.py`), servindo um Dashboard SPA moderno.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, SQLite3, Httpx/Urllib, Pytest, HTML5 + TailwindCSS + Vanilla JS, Docker (`gosom/google-maps-scraper`), Graphify.

**Spec:** `docs/superpowers/specs/2026-10-28-painel-de-busca-design.md`

## Global Constraints

- **Python**: Compatível com Python 3.11+ no Windows, utilizando biblioteca padrão sempre que possível + `fastapi`, `uvicorn`, `pydantic`, `pytest`, `httpx`.
- **Integração com Skill**: Utilizar o script e formato da skill `google-maps-scraper` (`scripts/scrape.py` + Docker em `http://localhost:8080`).
- **Protocolo Delbor**: Checkpoints obrigatórios de 10% em 10% sincronizados em `Sprint atual.md`, `C:\Projetos Soft\Operador\Projetos\Painel de Busca\Sprint atual.md` e GitHub (`https://github.com/Gallo41/painel-de-busca.git`).
- **Graphify**: Gerar e atualizar o grafo de conhecimento em `graphify-out/` (`graph.json`, `GRAPH_REPORT.md`, `graph.html`).

## Review Focus

- **Sites com URL de Rede Social no campo Website**: Muitos negócios colocam `instagram.com/...`, `facebook.com/...`, `wa.me/...` ou `linktr.ee/...` como "site" no Google Maps; o sistema deve classificá-los como `is_social_only_url = True` (oportunidade de criação de site próprio) e não como site institucional próprio.
- **Geração de Slug `.com.br` Limpo para o Registro.br**: Nomes de empresas no Google Maps possuem acentos, sufixos ("LTDA", "ME", "Clínica Odontológica - Dr. Fulano | Centro"); o gerador de domínio sugerido deve limpar acentos, stopwords empresariais e caracteres especiais antes de consultar `https://rdap.registro.br/domain/<slug>.com.br`.
- **Normalização de Telefone Brasileiro para WhatsApp (`wa.me`)**: Telefones vêm como `(11) 98765-4321`, `+55 11 3456-7890` ou `11987654321`; o higienizador deve produzir `55DDDNUMERO` válido para o link de 1-clique do WhatsApp.
- **Resiliência a Timeouts de Rede no Raio-X**: Sites fora do ar, SSL inválido ou indisponibilidade temporária do `web.archive.org` não podem lançar exceção não tratada; devem preencher o diagnóstico (`site_in_air = False` / `ssl_error`) e prosseguir.
- **Idempotência na Fila de Outreach (`outreach_queue`)**: Adicionar o mesmo lead para o mesmo canal na fila futura de automação não deve duplicar disparos pendentes.

---

### Task 1 (10%): Onboarding Padrão Delbor, Repositório GitHub, Spec e Plano
**Files:**
- Create: `.gitignore`, `.agents/rules/git-auto-commit.md`, `.agents/rules/graphify.md`, `.agents/rules/sprint-checkpoint.md`
- Create: `.githooks/post-commit`, `scripts/git-auto-sync.ps1`, `scripts/git-auto-sync.bat`
- Create: `docs/superpowers/specs/2026-10-28-painel-de-busca-design.md`, `docs/superpowers/plans/2026-10-28-painel-de-busca.md`
- Create: `Sprint atual.md`, `C:\Projetos Soft\Operador\Projetos\Painel de Busca\Sprint atual.md`, `C:\Projetos Soft\Operador\Projetos\Painel de Busca\Painel de Busca.md`

### Task 2 (20%): Camada de Banco de Dados SQLite e Modelos (`app/database.py`)
**Files:**
- Create: `app/__init__.py`, `app/database.py`, `app/models.py`
- Test: `tests/test_database.py`

### Task 3 (30%): Catálogo de Nichos & Integração com `google-maps-scraper` (`app/services/maps_scraper.py`)
**Files:**
- Create: `docker-compose.yml`, `scripts/scrape.py`, `app/services/niches_catalog.py`, `app/services/maps_scraper.py`
- Test: `tests/test_maps_scraper.py`

### Task 4 (40%): Módulo "Achar o Negócio" — Registro.br RDAP, Health Check e Casa dos Dados (`app/services/business_discovery.py`)
**Files:**
- Create: `app/services/business_discovery.py`
- Test: `tests/test_business_discovery.py`

### Task 5 (50%): Módulo "Raio-X do Site Atual" — Tech/CMS Detector, Sistemas Complexos e Web Archive (`app/services/site_xray.py`)
**Files:**
- Create: `app/services/site_xray.py`
- Test: `tests/test_site_xray.py`

### Task 6 (60%): Motor de Lead Scoring (0–100) e Classificador de Oportunidade (`app/services/lead_scorer.py`)
**Files:**
- Create: `app/services/lead_scorer.py`
- Test: `tests/test_lead_scorer.py`

### Task 7 (70%): Gerador Automático de Scripts de Abordagem e Links de Contato 1-Clique (`app/services/outreach_generator.py`)
**Files:**
- Create: `app/services/outreach_generator.py`
- Test: `tests/test_outreach_generator.py`

### Task 8 (80%): API REST Completa + Fila/Webhooks Pré-Prontos para Automação Futura (`app/main.py`, `app/routers/`)
**Files:**
- Create: `app/main.py`, `app/routers/leads_router.py`, `app/routers/outreach_router.py`
- Test: `tests/test_api.py`

### Task 9 (90%): Dashboard Web Local (Seletor de Nichos, Tabela Raio-X, Modal das 8 Ferramentas e Central de Contato)
**Files:**
- Create: `app/static/index.html`, `app/static/styles.css`, `app/static/app.js`
- Test: `tests/test_dashboard_ui.py`

### Task 10 (100%): Grafo de Conhecimento Graphify (`graphify-out/`), Documentação (`README.md`) e Validação Final
**Files:**
- Create: `README.md`, `requirements.txt`, `iniciar_painel.bat`
- Create: `graphify-out/graph.json`, `graphify-out/GRAPH_REPORT.md`, `graphify-out/graph.html`
