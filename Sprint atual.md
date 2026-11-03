# Sprint Atual: Correção do Botão WhatsApp e Humanização dos Scripts de Abordagem

- **Projeto**: Painel de Busca (`c:\Projetos Quecine\Painel de Busca`)
- **Data de Início**: 03/11/2026 às 19:30
- **Status**: Em Andamento (30%)
- **Repositório GitHub**: `https://github.com/Gallo41/painel-de-busca.git`

---

## 🎯 Objetivo da Sprint
1. **Corrigir o botão "Chamar no WhatsApp"**:
   - Diagnosticar e resolver a ausência da função `openWhatsApp(leadId)` no JavaScript do painel.
   - Implementar `openWhatsApp` e `copyCardMessage` com sanitização inteligente de número telefônico brasileiro (prefixo 55 + DDD), abertura em nova aba e atualização automática de status para "Já chamei" (`contatado`).
   - Disponibilizar atalho direto de WhatsApp também dentro do modal de detalhes técnicos do lead.
2. **Humanizar as mensagens de abordagem**:
   - Substituir mensagens robóticas e genéricas ("Olá, equipe da...") por abordagens naturais, conversacionais e respeitosas que parecem enviadas por um humano real, aumentando taxa de resposta no WhatsApp.
   - Adaptar para cada situação: sem site próprio (com domínio livre), site fora do ar, sistemas sob medida e melhoria de site lento/mobile.

---

## 📋 Checklist de Progresso Obrigatório (Regra dos 10%)

- [x] **10%** - Abertura da Sprint no `Sprint atual.md`, espelhamento no Operador e no `task.md`
- [x] **20%** - Diagnóstico técnico detalhado da falha no botão WhatsApp e mapeamento dos pontos de quebra
- [x] **30%** - Implementação de `openWhatsApp(leadId)` no `app/static/app.js` com suporte a wa.me / api.whatsapp e atualização de status
- [ ] **40%** - Implementação de `copyCardMessage(leadId)` e botão de WhatsApp no modal do lead (`openLeadModal`)
- [ ] **50%** - Refatoração e humanização do script de abordagem para SEM_SITE e DOMINIO_LIVRE em `outreach_generator.py`
- [ ] **60%** - Humanização dos scripts de abordagem para SITE_FORA_DO_AR, OPORTUNIDADE_SISTEMA e MELHORIA_SITE
- [ ] **70%** - Alinhamento humanizado dos textos de E-mail e Instagram DM
- [ ] **80%** - Criação de testes unitários para os novos scripts humanizados e validação de scripts UI
- [ ] **90%** - Execução da suíte completa de testes (`pytest`) sem regressões
- [ ] **100%** - Atualização do grafo Graphify (`graphify update .`), fechamento da Sprint e auto-sync Git

---

## 📝 Diário de Bordo & Checkpoints Salvos (10% em 10%)
| % Concluído | Data / Hora | Descrição do Progresso / Entrega Parcial | Arquivos Modificados |
| :---: | :---: | :--- | :--- |
| **10%** | 03/11/2026 19:30 | Abertura da Sprint de correção do botão WhatsApp e humanização dos scripts de abordagem. | `Sprint atual.md`, `task.md` |
| **20%** | 03/11/2026 19:33 | Diagnóstico de causa-raiz: botões chamavam `openWhatsApp` e `copyCardMessage` inexistentes em `app.js` disparando ReferenceError. Mapeamento de sanitização e fluxo. | `Sprint atual.md`, `task.md` |
| **30%** | 03/11/2026 19:35 | Implementação de `cleanWhatsAppNumber` e `openWhatsApp(leadId, customMsg)` em `app/static/app.js`, com leitura da mensagem editada no card, abertura em nova aba e auto-status. | `app/static/app.js`, `Sprint atual.md` |

---
*Gerado e mantido automaticamente pelo protocolo de sincronismo Antigravity <-> Operador <-> Obsidian.*
