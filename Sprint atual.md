# Sprint Atual: Dados 100% Reais do Google Maps (Docker) & Redesign UI/UX com Taste-Skill (Framed Sheet)

- **Projeto**: Painel de Busca (`c:\Projetos Quecine\Painel de Busca`)
- **Data de Início**: 31/10/2026 às 18:30
- **Status**: Em andamento (40%)
- **Repositório GitHub**: `https://github.com/Gallo41/painel-de-busca.git`

---

## 🎯 Objetivo da Sprint
1. **Dados 100% Reais**: Eliminar os leads simulados (`sim_*`) quando o motor Docker (`gmaps-scraper` na porta 8080) estiver ativo, importando as **117+ empresas reais de Piracicaba-SP** já coletadas pelo container (e aguardando a conclusão real em novas buscas) com diagnóstico real de site/Instagram/Linktree e Registro.br RDAP.
2. **Redesign UI/UX com `taste-skill` (`framed-sheet`)**: Aplicar rigorosamente a skill `design-taste-frontend` (`references/app-screens.md`, estilo `framed-sheet`, tipografia `IBM Plex Sans` + `IBM Plex Mono`, zero poluição visual, L-frame com sidebar de filtros + folha branca + visão Master-Detail com lista limpa de empresas reais à esquerda e o **Relatório Pronto + WhatsApp 1-clique** no painel lateral direito).

## Próximo passo
- Limpar leads simulados do banco SQLite e atualizar `app/services/maps_scraper.py` para ler todos os CSVs reais do container Docker `gmaps-scraper` (Marcos 20% e 30%).

---

## 📋 Checklist de Progresso Obrigatório (Regra dos 10%)

- [x] **10%** - Diagnóstico com `systematic-debugging` (localizados 117 leads reais de Piracicaba no container Docker `gmaps-scraper`) e sorteio da direção `framed-sheet` via `taste-skill` (`draw.mjs --app`)
- [x] **20%** - Atualizar `app/services/maps_scraper.py` para extrair diretamente os leads reais dos jobs concluídos no Docker `gmaps-scraper` e aguardar conclusão real sem cair em dados falsos
- [x] **30%** - Limpar todos os leads simulados (`sim_*` / `cnae_sim_*`) do banco de dados e importar o lote real de empresas de Piracicaba-SP com classificação real
- [x] **40%** - Otimizar o pipeline de Raio-X em lote (`app/routers/leads_router.py` e `app/services/outreach_generator.py`) com verificação rápida real de domínios e classificação precisa de sites reais (`instagram.com`, `linktr.ee`, `netlify.app`, etc.)
- [ ] **50%** - Reescrever `app/static/styles.css` seguindo os tokens exatos do `taste-skill` (`framed-sheet`: `IBM Plex Sans`, `IBM Plex Mono`, L-frame `#f9fbfc`, white sheet radius `16px`, KPI strip dividida por `1px`, zero emojis/gradientes)
- [ ] **60%** - Reescrever `app/static/index.html` na arquitetura `framed-sheet` (Sidebar de navegação e gerador compacto + Top Bar de busca + Folha Principal com KPI strip e Master-Detail: Tabela de Empresas Reais + Painel de Relatório Pronto)
- [ ] **70%** - Atualizar `app/static/app.js` para dinâmica Master-Detail fluida (seleção instantânea na tabela atualiza o Relatório Pronto lateral, filtros em 1 clique na sidebar, disparo WhatsApp e fila do robô)
- [ ] **80%** - Validar com `lint.mjs --app` e `inspect.mjs --app` do `taste-skill` e corrigir apontamentos visuais/estruturais
- [ ] **90%** - Atualizar e executar suíte completa `pytest` garantindo 100% dos testes passando com a nova estrutura
- [ ] **100%** - Atualizar grafo `graphify-out/`, validar servidor ao vivo em `http://127.0.0.1:8090` com os dados reais de Piracicaba e sincronizar com GitHub

---

## 📝 Diário de Bordo & Checkpoints Salvos (10% em 10%)
| % Concluído | Data / Hora | Descrição do Progresso / Entrega Parcial | Arquivos Modificados |
| :---: | :---: | :--- | :--- |
| **10%** | 31/10/2026 18:33 | Diagnóstico dos 117 leads reais de Piracicaba no Docker `gmaps-scraper` e definição da direção `framed-sheet` com `taste-skill`. | `Sprint atual.md`, `.taste-skill/direction.json` |
| **20-40%** | 31/10/2026 18:42 | Leads 100% reais: coleta dos jobs concluídos no Docker (194 empresas de Piracicaba), erro 503 se motor offline, purge de leads simulados/CNAE fabricados, Raio-X real em paralelo (12 threads, 53s para 194 leads), bullet de domínio sem variações não verificadas. | `app/services/maps_scraper.py`, `app/services/outreach_generator.py`, `app/routers/leads_router.py`, `app/database.py`, `app/main.py`, `app/models.py` |

---
*Gerado e mantido automaticamente pelo protocolo de sincronismo Antigravity <-> Operador <-> Obsidian.*

