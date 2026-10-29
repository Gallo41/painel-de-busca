# Painel de Busca, Raio-X & Prospecção de Leads (Freelancers)

Sistema web local desenvolvido para você e seu sócio encontrarem clientes reais para **Criação de Sites/Landing Pages**, **Reforma/Modernização de Sites** e **Sistemas Web Sob Medida (Mais Complexos)**.

Integra nativamente a skill **`google-maps-scraper`** (`Mahanaicoach/google-maps-scraper-kit` + Docker `gosom/google-maps-scraper`) com as **8 ferramentas de prospecção e raio-x** da metodologia de vendas local e deixa uma **API + Fila de Outreach pré-pronta** para o projeto futuro de automação de contato.

---

## 🛠️ As 8 Ferramentas Integradas no Motor

### Coluna 1 — Achar o Negócio (`app/services/business_discovery.py` + `maps_scraper.py`)
1. **`google.com/maps`**: Filtra os nichos selecionados por cidade, extrai telefone, WhatsApp, e-mail, endereço, nota, quantidade de avaliações e redes sociais (`scripts/scrape.py`).
2. **`casadosdados.com.br`**: Gera filtros automáticos de CNAE + Cidade para buscar empresas recém-abertas antes da concorrência.
3. **`registro.br`**: Consulta oficial via protocolo **RDAP** (`https://rdap.registro.br/domain/<slug>.com.br`) para descobrir se o domínio `.com.br` com o nome da empresa está **livre para registro**.
4. **`downforeveryoneorjustme.com`**: Health check HTTP/HTTPS e SSL em tempo real que identifica se o site cadastrado no Maps está **fora do ar** ou inseguro.

### Coluna 2 — Raio-X do Site Atual (`app/services/site_xray.py`)
5. **`builtwith.com`**: Identifica servidor, CDN, Google Analytics, Google Tag Manager, Meta Pixel e widgets de WhatsApp.
6. **`wappalyzer.com`**: Lê frameworks (React/Next.js, Bootstrap, Tailwind, jQuery) e responsividade mobile (`viewport`).
7. **`whatcms.org`**: Descobre se é **WordPress**, **Wix**, **Squarespace**, **Shopify**, **Webflow**, **Linktree/Bio** ou **HTML Estático**, além de detectar **Oportunidade de Sistema Complexo** (empresas com muitas avaliações sem agendamento online, portal do cliente ou catálogo).
8. **`web.archive.org`**: Consulta a API oficial do **Wayback Machine** para checar a idade do site e há quanto tempo ninguém mexe nele.

---

## 🚀 Como Usar no Dia a Dia

### 1. Iniciar o Painel Web
Basta clicar duas vezes em **`iniciar_painel.bat`** ou rodar no terminal:
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8090 --reload
```
Acesse: **`http://localhost:8090`** (Documentação interativa da API: **`http://localhost:8090/docs`**).

### 2. (Opcional) Subir o Motor Docker do Google Maps Scraper
Para buscas ao vivo ilimitadas no Google Maps via container local:
```powershell
docker compose up -d
```
*(Mesmo com o Docker desligado, o painel funciona com o modo de Simulação Local, Importação de CSV do `scripts/scrape.py` e Cadastro Manual com Raio-X ao vivo).*

---

## 🤖 Base Pré-Pronta para o Projeto Futuro de Automação de Contato

O projeto já possui a tabela `outreach_queue` no SQLite e endpoints REST prontos para você plugar seu futuro bot (Evolution API / WhatsApp, WPPConnect, n8n ou Worker Python):

- **`POST /api/outreach/enqueue`**: Enfileira leads selecionados com o script já personalizado pela dor detectada no Raio-X.
- **`GET /api/outreach/queue`**: Lista os disparos prontos (`ready`), em envio (`sending`), enviados (`sent`) ou respondidos (`replied`).
- **`POST /api/outreach/claim`**: Reserva atomicamente o próximo lead da fila para o bot disparar.
- **`PATCH /api/outreach/{queue_id}/status`**: Webhook para o bot marcar como enviado/respondido (atualiza automaticamente o status do lead no funil).
- **`GET /api/outreach/export?format=csv`**: Exporta a planilha completa com scripts e links `wa.me`.
