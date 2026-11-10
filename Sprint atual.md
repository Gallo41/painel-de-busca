# Sprint Atual: Agente WhatsApp (Skill Barbearia), Consulta de Preço no Chefe e Protótipo Automático por IA

- **Projeto**: Painel de Busca (`c:\Projetos Quecine\Painel de Busca`)
- **Data de Início**: 09/11/2026 às 21:16
- **Status**: Em andamento (10%)
- **Repositório GitHub**: `https://github.com/Gallo41/painel-de-busca.git`

---

## 🎯 Objetivo da Sprint
Implementar o ecossistema completo de negociação ativa via WhatsApp baseado na skill `agente-whatsapp` (`gfrabelo/agente-barbearia`), integrado à fila do Painel de Busca:
1. **Confirmação na Fila + Modo Teste Seguro**: Ao confirmar um lead na fila, envia a 1ª mensagem e autoriza a negociação. Inicia em **Modo Teste** enviando para `+55 19 99610-9028` (`5519996109028`), com chave no Painel para liberar disparos automáticos aos clientes reais após aprovação.
2. **Atendimento Focado em Resultado + Handoff Humano (90%) + Trava Anti-Fiscal**: Convence o cliente do valor de uma Landing Page ou Sistema sob medida (proibindo escopo fiscal/tributário) e pausa automaticamente quando o humano assume a conversa (`fromMe && !wasSentByApi` ou botão no Painel).
3. **Ponte de Preço com o Chefe (`+551999958516`)**: Informa faixa inicial de referência se o cliente insistir e envia consulta de preço com sugestão para `+551999958516`, repassando a proposta assim que o Chefe responder.
4. **Protótipo Automático por IA (`C:\Projetos Soft\Painel\chave.env`)**: Ao fechar negócio, gera automaticamente o protótipo navegável para o lead usando as chaves configuradas, disponibiliza preview no Painel e avisa o Chefe no `+551999958516`.

---

## 📋 Checklist de Progresso Obrigatório (Regra dos 10%)

- [x] **10%** - Especificação arquitetural (`docs/superpowers/specs/`), abertura da Sprint no `Sprint atual.md`, Operador e `task.md`
- [ ] **20%** - Evolução do banco SQLite (`app/database.py` e `app/models.py`): tabelas de configurações, conversas, consultas de preço e protótipos
- [ ] **30%** - Provedor Multi-IA (`app/services/ai_provider.py`) lendo `C:\Projetos Soft\Painel\chave.env` (OpenRouter, NVIDIA NIM e Gemini) com fallback resiliente
- [ ] **40%** - Motor do Agente WhatsApp (`app/services/whatsapp_agent.py`): port das 7 cicatrizes da skill `agente-barbearia`, trava anti-fiscal e handoff humano
- [ ] **50%** - Ponte de Consulta de Preço em Tempo Real com o Chefe (`+551999958516`) e processamento da resposta do Chefe
- [ ] **60%** - Fábrica Automática de Protótipos via IA (`app/services/prototype_generator.py`) ao fechar negócio + aviso no `+551999958516`
- [ ] **70%** - Rotas de API (`app/routers/agent_router.py` e `app/routers/outreach_router.py`): confirmação na fila, webhook, handoff e preview de protótipo
- [ ] **80%** - Micro-Bridge Node.js WhatsApp QR Code (`whatsapp_bridge/`) + Central do Agente e Fila interativa no Painel (`index.html`, `app.js`, `styles.css`)
- [ ] **90%** - Suíte de testes automatizados (`tests/test_whatsapp_agent.py`) cobrindo fila, modo teste, consulta de preço, bloqueio fiscal, handoff e protótipo
- [ ] **100%** - Execução completa do `pytest`, atualização do grafo Graphify (`graphify update .`) e sincronização final no GitHub

---

## 📝 Diário de Bordo & Checkpoints Salvos (10% em 10%)
| % Concluído | Data / Hora | Descrição do Progresso / Entrega Parcial | Arquivos Modificados |
| :---: | :---: | :--- | :--- |
| **10%** | 09/11/2026 21:16 | Especificação arquitetural criada e abertura da Sprint em 10 marcos sincronizada com Operador e `task.md`. | `docs/superpowers/specs/2026-11-09-whatsapp-agent-prototype-design.md`, `Sprint atual.md`, `task.md` |

---
*Gerado e mantido automaticamente pelo protocolo de sincronismo Antigravity <-> Operador <-> Obsidian.*
