# Sprint Atual: Embutir as 8 Ferramentas Nativamente no Painel (Zero Links Externos) & Motor Docker Ativo

- **Projeto**: Painel de Busca (`c:\Projetos Quecine\Painel de Busca`)
- **Data de Início**: 29/10/2026 às 19:45
- **Status**: Em andamento (20%)
- **Repositório GitHub**: `https://github.com/Gallo41/painel-de-busca.git`

---

## 🎯 Objetivo da Sprint
Transformar os 8 cards das ferramentas (`google.com/maps`, `casadosdados.com.br`, `registro.br`, `downforeveryoneorjustme.com`, `builtwith.com`, `wappalyzer.com`, `whatcms.org`, `web.archive.org`) em **módulos 100% embutidos e executáveis dentro do próprio sistema** (sem links externos que tiram o usuário da tela) e colocar o container Docker `gmaps-scraper` (`gosom/google-maps-scraper:v1.18.1`) em execução ativa na porta `127.0.0.1:8080`.

## Próximo passo
- Embutir Módulo 2 (Consulta & Descoberta de CNPJ e Empresas Recém-Abertas por CNAE/Cidade — nativo no painel, substituindo links para `casadosdados.com.br`).

---

## 📋 Checklist de Progresso Obrigatório (Regra dos 10%)

- [x] **10%** - Planejamento da Sprint 2 e disparo do `docker compose up -d` para baixar e subir o motor `gosom/google-maps-scraper:v1.18.1` (`gmaps-scraper` em `127.0.0.1:8080`)
- [x] **20%** - Embutir **Módulo 1 (Google Maps Engine)** no backend: listagem de jobs do container Docker, status real e geocoding Nominatim integrado
- [ ] **30%** - Embutir **Módulo 2 (Consulta & Descoberta CNPJ / Empresas — estilo Casa dos Dados)**: integração direta com API CNPJ (`BrasilAPI`) trazendo Razão Social, Fantasia, Data de Abertura, CNAE, Sócios, Telefone, E-mail e botão de converter em Lead
- [ ] **40%** - Embutir **Módulo 3 (Scanner RDAP Registro.br Completo)**: extração de status (`LIVRE`/`REGISTRADO`), titular, CNPJ do dono, datas de criação/expiração, servidores DNS e gerador de 3 variações `.com.br` alternativas
- [ ] **50%** - Embutir **Módulo 4 (Monitor HTTP / DNS / SSL — DownForEveryone)**: resolução de IP (`socket`), inspeção de certificado SSL/TLS (`ssl`), código HTTP, tempo de resposta em `ms` e status real
- [ ] **60%** - Embutir **Módulos 5, 6 e 7 (Scanner Profundo BuiltWith + Wappalyzer + WhatCMS)**: detecção detalhada de CMS/versão, plugins (Elementor, WooCommerce), frameworks JS/CSS, servidor/CDN, pixels de tráfego, widgets de atendimento e diagnóstico de sistemas
- [ ] **70%** - Embutir **Módulo 8 (Scanner Histórico Web Archive CDX + Availability)**: histórico de snapshots (`web.archive.org/cdx/search/cdx`), primeira e última captura, total de alterações e dias sem atualização
- [ ] **80%** - Criar endpoints REST unificados (`/api/tools/*`) para execução embutida individual ou em lote das 8 ferramentas + testes (`tests/test_embedded_tools.py`)
- [ ] **90%** - Atualizar Dashboard (`index.html` e `app.js`): remover links clicáveis externos e embutir o Painel Interativo de Execução e Resultados das 8 Ferramentas dentro da própria interface
- [ ] **100%** - Validar container Docker `gmaps-scraper` ativo em `localhost:8080`, rodar 100% da suíte `pytest`, atualizar o grafo `graphify-out/` e sincronizar com GitHub

---

## 📝 Diário de Bordo & Checkpoints Salvos (10% em 10%)
| % Concluído | Data / Hora | Descrição do Progresso / Entrega Parcial | Arquivos Modificados |
| :---: | :---: | :--- | :--- |
| **10%** | 29/10/2026 19:45 | Início da Sprint 2 e disparo do `docker compose up -d` para o container `gmaps-scraper` (`gosom/google-maps-scraper:v1.18.1`). | `Sprint atual.md`, `task.md`, `docker-compose.yml` |
| **20%** | 29/10/2026 19:50 | Container Docker `gmaps-scraper` ativo em `127.0.0.1:8080` e Módulo 1 (Google Maps Engine Control + Geocoding Nominatim + Grid) embutido em `app/services/maps_scraper.py`. | `app/services/maps_scraper.py`, `Sprint atual.md`, `task.md` |

---
*Gerado e mantido automaticamente pelo protocolo de sincronismo Antigravity <-> Operador <-> Obsidian.*
