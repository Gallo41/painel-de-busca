# Instruções do Painel de Busca

Leia `Sprint atual.md`, `docs/ESTRUTURA_DO_PROJETO.md` e as regras em `.agents/rules/` antes de alterar o projeto.

- A empresa de agentes está em `.claude/agents/`; seu protocolo canônico é `docs/EMPRESA_DE_AGENTES.md`.
- O CEO aprova publicação, contato externo e gastos. Revisão do gerente ou participação do sócio não substituem esse OK.
- As instruções diretas do usuário prevalecem sobre regras antigas: staging somente de caminhos revisados; nunca `git add -A`. Sem upstream, informe pendência e não faça commit/push. O helper atual faz staging amplo e não atende a essa política; não o use assim. O hook `.githooks/post-commit` publica automaticamente: considere esse efeito antes de qualquer commit e não duplique push.
- Preserve alterações alheias, dados locais, credenciais e pendências da sprint. Para tarefas pequenas, registre a conclusão diretamente; use marcos verificáveis para trabalho substancial.
- Consulte `graphify-out/wiki/index.md` e o grafo para contexto; após alterar código, atualize o AST com Graphify quando compatível. O mapa Markdown registra também os agentes e suas relações.
- Instalação e operação: `README.md` e `docs/guia-instalacao-amigo.md`. Não deduza autorização de deploy de uma tarefa de desenvolvimento.
