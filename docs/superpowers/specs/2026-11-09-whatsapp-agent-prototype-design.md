# Especificação de Arquitetura: Agente de Negociação WhatsApp, Ponte de Preço com Chefe e Gerador de Protótipos IA

- **Data**: 09/11/2026
- **Projeto**: Painel de Busca (`c:\Projetos Quecine\Painel de Busca`)
- **Base de Referência**: Skill `agente-whatsapp` (`gfrabelo/agente-barbearia`)

---

## 1. Visão Geral e Objetivos

Implementar no **Painel de Busca** o ciclo completo de abordagem ativa, pré-atendimento/negociação no WhatsApp, consulta de preço em tempo real com o responsável (`+551999958516`), interferência humana transparente (90% dos casos de fechamento) e geração automática de protótipos/projetos web via IA ao fechar negócio.

### Regras de Ouro do Negócio
1. **Disparo mediante Confirmação na Fila**: O usuário analisa os leads trazidos pela busca e os envia para a fila (`outreach_queue`). Somente ao **confirmar/autorizar o disparo na fila**, a 1ª mensagem é enviada e o agente é autorizado a negociar com aquele lead.
2. **Modo de Teste (Sandbox) vs. Produção**:
   - **Número do Chefe (Avisos, Consultas de Preço e Aprovação)**: `+551999958516` (`551999958516`).
   - **Número de Cliente de Teste**: `+55 19 99610-9028` (`5519996109028`).
   - Enquanto o sistema estiver em **Modo Teste** (`test_mode = true`, padrão inicial), qualquer disparo confirmado na fila redireciona a conversa para o número de teste (`5519996109028`) carregando o contexto real da empresa selecionada.
   - Quando o usuário aprovar e alternar para **Modo Produção** no Painel, os disparos confirmados na fila passam a enviar para o WhatsApp real do lead.
3. **Venda Focada em Resultado e Escopo Flexível (LP ou Além)**:
   - O agente utiliza o diagnóstico do Raio-X do lead (falta de site, domínio `.com.br` livre, dependência apenas de Instagram, lentidão ou falta de sistema) para convencer o cliente do **resultado comercial** de uma Landing Page de alta conversão ou de um sistema sob medida (agendamento, área de cliente, catálogo, painel administrativo).
4. **Proibição Estrita de Escopo Fiscal**:
   - O agente **nunca** promete, aceita ou inclui módulos fiscais (NF-e, NFC-e, NFS-e, SAT, cupom fiscal, apuração de impostos ou contabilidade). Caso o cliente solicite, o agente contorna com naturalidade explicando que o foco é captação de clientes, presença digital e gestão operacional/comercial sem responsabilidade tributária.
5. **Ponte de Preço com o Chefe (`+551999958516`)**:
   - Se o cliente insistir em valores antes do fechamento, o agente pode informar uma **faixa inicial de referência** tabelada no código (formatada em `R$` pelo código, nunca inventada pela IA).
   - Em paralelo, o agente aciona a ferramenta `consultar_preco_chefe`, enviando um WhatsApp para `+551999958516` com o ID da conversa/lead, resumo do que o cliente pediu, faixa base e **sugestão de preço do agente**.
   - Quando o Chefe (`+551999958516`) responde no WhatsApp (ex.: `#12 faz R$ 1.400 em 3x`), o sistema vincula a resposta ao lead e orienta o agente a apresentar a proposta aprovada ao cliente.
6. **Handoff Humano Automático (90% dos casos)**:
   - Se o humano enviar qualquer mensagem manualmente pelo aparelho na conversa do cliente (`fromMe && !wasSentByApi`) ou clicar em **"Assumir / Pausar Agente"** no Painel, o agente silencia imediatamente naquela conversa para não atropelar o fechamento humano.
7. **Fábrica Automática de Protótipos via IA (`C:\Projetos Soft\Painel\chave.env`)**:
   - Ao fechar acordo na conversa (ou mediante acionamento no Painel/WhatsApp), o sistema compila o briefing completo (dados do lead + Raio-X + requisitos pedidos pelo cliente no chat) e utiliza as chaves de `C:\Projetos Soft\Painel\chave.env` (NVIDIA NIM / OpenRouter / Gemini) para gerar um **protótipo/projeto navegável completo** (`exports/prototipos/lead_<id>/index.html`).
   - O protótipo fica disponível para preview imediato no Painel (`/api/agent/prototypes/{lead_id}/preview`) e o sistema envia um aviso para o Chefe no `+551999958516` para revisão antes do envio ao cliente.

---

## 2. Arquitetura Técnica e Componentes

### 2.1. Persistência SQLite (`app/database.py`)
Novas tabelas integradas ao banco `painel_busca.db`:
- `agent_settings`:
  - `id` (PK = 1), `test_mode` (bool, default `1`), `boss_phone` (`551999958516`), `test_client_phone` (`5519996109028`), `attendant_name` (`Leo`), `company_name` (`Estúdio Digital`), `debounce_seconds` (`6.0`), `pause_minutes_on_human` (`60`), `updated_at`.
- `agent_conversations`:
  - `id`, `lead_id`, `queue_id`, `chatid` (telefone normalizado do interlocutor no WhatsApp), `real_lead_phone`, `is_test_session`, `status` (`active`, `waiting_boss_price`, `paused_by_human`, `closed_won`, `closed_lost`), `paused_until`, `pause_reason`, `collected_requirements_json`, `suggested_price_cents`, `approved_price_text`, `turn_version`, `created_at`, `updated_at`.
- `agent_messages`:
  - `id`, `conversation_id`, `role` (`user`, `model`, `system`, `boss`), `direction` (`inbound`, `outbound`), `content`, `external_message_id`, `tool_calls_json`, `created_at`.
- `price_consultations`:
  - `id`, `conversation_id`, `lead_id`, `client_summary`, `scope_type`, `suggested_price_cents`, `price_range_text`, `boss_reply_text`, `status` (`pending`, `approved`, `superseded`), `created_at`, `responded_at`.
- `lead_prototypes`:
  - `id`, `lead_id`, `conversation_id`, `scope_type`, `briefing_json`, `html_content`, `output_path`, `ai_provider_used`, `status` (`generating`, `ready`, `approved`, `sent_to_client`, `failed`), `created_at`, `updated_at`.

### 2.2. Provedor Multi-IA Resiliente (`app/services/ai_provider.py`)
- Lê automaticamente `C:\Projetos Soft\Painel\chave.env` extraindo:
  - Chaves NVIDIA NIM (`nvapi-...`) -> endpoint `https://integrate.api.nvidia.com/v1/chat/completions`
  - Chaves OpenRouter (`sk-or-v1-...`) -> endpoint `https://openrouter.ai/api/v1/chat/completions`
  - Chave Google Gemini (`GEMINI_API_KEY` / `AIza...`) -> Google GenAI / REST compatível
- Possui fallback inteligente e determinístico caso a rede ou cota oscile, garantindo que o agente nunca deixe uma conversa ou geração de protótipo quebrar.

### 2.3. Motor do Agente WhatsApp (`app/services/whatsapp_agent.py`)
Implementa as **7 Cicatrizes de Produção** da skill `agente-whatsapp`:
1. **Resposta estrita no `chatid`** (ignorando `@lid` em `sender`).
2. **Agrupamento (Debounce) por conversa**: janela configurável (6s em produção, ajustável para testes) que reinicia a cada mensagem recebida na mesma conversa e concatena com `\n`.
3. **Anti-Resposta-Velha (`turn_version` + checagem pós-modelo)**: se o humano assumiu ou o cliente enviou nova mensagem enquanto o modelo gerava a resposta, descarta o turno antigo.
4. **Detecção de Handoff Humano (`fromMe && !wasSentByApi`)**: pausa a conversa imediatamente por `pause_minutes_on_human` minutos e cancela qualquer buffer pendente.
5. **Formatação de Moeda no Código (`moeda_br()`)**: valores financeiros vêm sempre formatados pelo Python (`R$ 1.200 a R$ 2.500`), nunca calculados livremente pelo modelo.
6. **Retorno de Tools com campo `instrucao`**: toda ferramenta chamada pelo agente devolve diretrizes imediatas (ex.: proibição fiscal, faixa de referência e aviso de consulta enviada ao chefe).
7. **Poda segura de histórico e sanitização de texto para WhatsApp**: máximo de 2 frases curtas por mensagem, sem listas markdown ou texto robótico corporativo.

### 2.4. Micro-Bridge WhatsApp QR Code (`whatsapp_bridge/`)
- Serviço Node.js enxuto baseado em `@whiskeysockets/baileys` + `express` + `qrcode`:
  - Mantém sessão autenticada em `whatsapp_bridge/auth_info/`.
  - Expõe `GET /status` (retorna estado de conexão, número conectado e imagem Base64 do QR Code atual para exibição no Painel).
  - Expõe contrato 100% compatível com UAZAPI (`POST /send/text`, `POST /message/markread`, `POST /message/presence`, `POST /instance/presence`).
  - Dispara webhooks de mensagens recebidas/enviadas para `POST http://127.0.0.1:8090/api/agent/webhook`.

### 2.5. Fábrica de Protótipos via IA (`app/services/prototype_generator.py`)
- Compila os dados do lead, diagnóstico do Raio-X e requisitos levantados na conversa.
- Aciona o `ai_provider.py` para sintetizar um protótipo web completo (HTML5 + TailwindCSS + JavaScript responsivo, com copy persuasiva real da empresa, seção de serviços/benefícios, prova social e CTA integrado ao WhatsApp da empresa, **sem nenhum item fiscal**).
- Salva em `exports/prototipos/lead_<id>/index.html`, registra em `lead_prototypes` e notifica o Chefe (`+551999958516`) com o link de preview no Painel.

### 2.6. Rotas de API e Interface no Painel (`app/routers/agent_router.py` & `app/static/`)
- `GET /api/agent/settings` & `PUT /api/agent/settings`: leitura e atualização de Modo Teste/Produção, número do Chefe (`+551999958516`) e número de Teste (`+5519996109028`).
- `GET /api/agent/bridge/status`: status do WhatsApp e QR Code para o Painel.
- `POST /api/outreach/{queue_id}/confirm-send`: confirma o item na fila, dispara a 1ª mensagem via WhatsApp (redirecionando para `+5519996109028` se `test_mode=True`) e cria a conversa ativa do agente.
- `POST /api/agent/webhook`: recebe eventos de mensagens do Bridge WhatsApp / UAZAPI (clientes, intervenções humanas `fromMe` e respostas de preço do Chefe `+551999958516`).
- `GET /api/agent/conversations` & `POST /api/agent/conversations/{id}/pause` / `resume`: visualização do chat em tempo real no Painel e botão para assumir/retomar conversa.
- `POST /api/agent/leads/{lead_id}/generate-prototype` & `GET /api/agent/prototypes/{lead_id}/preview`: geração e visualização ao vivo do protótipo gerado pela IA.
