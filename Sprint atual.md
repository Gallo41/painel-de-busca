# Sprint Atual: Ajuste de Densidade e Redução da Quantidade de Sites por Tela

- **Projeto**: Painel de Busca (`c:\Projetos Quecine\Painel de Busca`)
- **Data de Início**: 01/11/2026 às 20:59
- **Status**: Em Andamento (10%)
- **Repositório GitHub**: `https://github.com/Gallo41/painel-de-busca.git`

---

## 🎯 Objetivo da Sprint
Reduzir a quantidade de empresas/sites exibidos por tela na tabela de recomendações para que a visualização fique enxuta, sem exigir rolagem vertical e adaptando-se perfeitamente à altura da tela e da Central de Contato:
1. **Redução da Quantidade Padrão**: Reduzir o padrão de 10 para 5 itens por página.
2. **Opções Mais Enxutas**: Atualizar o seletor com as opções `5`, `8`, `10`, `15` e `20`.
3. **Persistência de Preferência**: Salvar a preferência do usuário no `localStorage` para que a escolha seja lembrada nos próximos acessos.

---

## 📋 Checklist de Progresso Obrigatório (Regra dos 10%)

- [x] **10%** - Diagnóstico do ajuste de densidade (definição do novo padrão de 5 itens por tela e opções mais enxutas 5, 8, 10, 15, 20)
- [ ] **20%** - Atualização do markup HTML do seletor em `index.html` com padrão de 5 itens
- [ ] **30%** - Atualização do `DEFAULT_PAGE_SIZE = 5` no `app.js`
- [ ] **40%** - Implementação de persistência local da preferência no `localStorage` (`painel_page_size`)
- [ ] **50%** - Ajuste fino de altura/espaçamento nas linhas da tabela para visualização compacta
- [ ] **60%** - Sincronização do seletor na inicialização (`initDashboard` recupera do `localStorage`)
- [ ] **70%** - Validação de navegação de teclado e elipses numéricas com 5 itens por página
- [ ] **80%** - Verificação de compatibilidade mobile e responsividade
- [ ] **90%** - Testes automatizados no `pytest` cobrindo o novo padrão e seletor
- [ ] **100%** - Validação no servidor ativo (`http://127.0.0.1:8090`), `graphify update .` e sincronização com GitHub

---

## 📝 Diário de Bordo & Checkpoints Salvos (10% em 10%)
| % Concluído | Data / Hora | Descrição do Progresso / Entrega Parcial | Arquivos Modificados |
| :---: | :---: | :--- | :--- |
| **10%** | 01/11/2026 20:59 | Diagnóstico: identificado que 10 itens ainda demandam rolagem vertical; planejado novo padrão de 5 itens e opções 5, 8, 10, 15, 20 com persistência local. | `Sprint atual.md`, `task.md` |

---
*Gerado e mantido automaticamente pelo protocolo de sincronismo Antigravity <-> Operador <-> Obsidian.*
