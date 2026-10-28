---
trigger: always_on
description: Regra de padronização de commit e push automático para o repositório GitHub painel-de-busca.
---

# Regra Mandatória: Commit e Sincronização Automática com GitHub

Todo agente de IA (Antigravity, OpenCode, Claudinho) e desenvolvedor atuando no projeto **Painel de Busca** deve seguir a política de auto-commit padrão:

## Repositório Oficial
- **Remote**: `origin` -> `https://github.com/Gallo41/painel-de-busca.git`
- **Branch Padrão**: `main`

## Diretrizes de Commit Automático
1. **Em cada Checkpoint de Sprint (10% a 100%)**:
   - É obrigatório commitar e sincronizar as alterações com o repositório remoto.
   - Executar:
     ```powershell
     powershell -ExecutionPolicy Bypass -File ./scripts/git-auto-sync.ps1 -Message "checkpoint: [X%] <descrição do avanço>"
     ```
     ou
     ```powershell
     git add -A
     git commit -m "checkpoint: [X%] <descrição do avanço>"
     git push origin main
     ```

2. **Ao Concluir Qualquer Tarefa, Fix ou Refatoração**:
   - Nunca encerrar uma sessão sem realizar o commit e push das alterações finais testadas.
   - O hook `post-commit` (`.githooks/post-commit`) já garante o envio automático via `git push origin HEAD` a cada commit realizado.

3. **Arquivos Proibidos de Commitar**:
   - Bases Firebird locais (`*.gdb`, `*.fdb`) e bancos SQLite de produção (`*.db`, `*.sqlite`).
   - Binários compilados (`Win32/`, `*.exe`, `*.dll`, `*.dcu`).
   - Caches do Graphify (`graphify-out/cache/`) e diretórios de teste temporários (`tests/tmp/`).
   - Credenciais reais (`.env`, `Configura.ini`).
