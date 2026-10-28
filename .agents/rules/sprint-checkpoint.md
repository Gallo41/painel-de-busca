---
trigger: always_on
description: Regra mandatória de Sprint, Checkpoint de 10 em 10% e Sincronismo com Obsidian e Claudinho.
---

# Regra Mandatória: Sprint, Checkpoint 10% e Sincronismo com Obsidian

Esta regra deve ser rigorosamente seguida em todas as tarefas no ambiente Antigravity, OpenCode e Claudinho.

## 1. Registro Obrigatório no Início da Tarefa / Sprint
Ao iniciar qualquer tarefa, funcionalidade, refatoração ou correção de bug:
- Localizar a ficha do projeto em `C:\Projetos Soft\Operador\Projetos\Painel de Busca\`.
- Criar ou atualizar o arquivo `Sprint atual.md` registrando:
  - **Objetivo da Sprint / Tarefa**.
  - **Checklist detalhado com 10 marcos (10% a 100%)**.
  - **Arquivos alvo**.
- No Antigravity, manter o artefato `task.md` perfeitamente alinhado com o `Sprint atual.md`.

## 2. Checkpoint Incremental de 10 em 10% (Salvamento Seguro)
Para garantir que nenhum código ou raciocínio seja perdido:
- A cada 10% de progresso concluído (10%, 20%, 30%, 40%, 50%, 60%, 70%, 80%, 90%, 100%):
  - Marcar o marco no `Sprint atual.md` (raiz do projeto e pasta central do Operador).
  - Garantir que os arquivos modificados estejam salvos, compilando/executando e sem pendências quebradas.
  - Atualizar o checklist do `task.md`.
  - **Commit & Push Automático Obrigatório**: Realizar commit e push imediato para o repositório remoto (`https://github.com/Gallo41/painel-de-busca.git`) via `powershell -ExecutionPolicy Bypass -File ./scripts/git-auto-sync.ps1 -Message "checkpoint: [X%] <descrição>"` ou `git commit -m "..." && git push origin main`.

## 3. Economia de Tokens com Graphify e Obsidian
- Antes de inspecionar diretórios ou arquivos grandes:
  1. Consultar a ficha do projeto em `C:\Projetos Soft\Operador\Projetos\Painel de Busca\Painel de Busca.md`.
  2. Consultar o grafo de conhecimento `graphify-out/` (via `graphify query "<pergunta>"` ou visualizador).
  3. Carregar apenas os blocos de código estritamente necessários.
- Ao concluir modificações de código, executar `graphify update .` (extração AST local sem custo de API) para manter a memória do projeto atualizada.

## 4. Sincronismo Antigravity <-> Claudinho / OpenCode
- O repositório central de verdade dos projetos é `C:\Projetos Soft\Operador\Projetos\`.
- O painel nativo Claudinho lê este mesmo diretório para listar projetos e status de sprints.
- Qualquer alteração feita aqui reflete de imediato no Claudinho, e qualquer ação no Claudinho é sincronizada aqui.
