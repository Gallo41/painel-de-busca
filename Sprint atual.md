# Sprint Atual: Deduplicação Inteligente Multi-Critério & Limpeza de Leads Duplicados

- **Projeto**: Painel de Busca (`c:\Projetos Quecine\Painel de Busca`)
- **Data de Início**: 31/10/2026 às 19:11
- **Status**: Concluído (100%)
- **Repositório GitHub**: `https://github.com/Gallo41/painel-de-busca.git`

---

## 🎯 Objetivo da Sprint
Eliminar definitivamente todas as duplicatas de empresas no Painel de Busca (como "Ello Próteses e Implantes", "Encanttá Odontologia", etc.) e blindar o banco contra novas duplicatas:
1. **Deduplicação Multi-Critério**: Reconhecer a mesma empresa por `place_id`, por `whatsapp_clean + cidade` ou por `título normalizado + cidade` (mesmo quando uma captura veio sem `place_id` ou com pontuação ligeiramente diferente).
2. **Mesclagem e Enriquecimento**: Se uma empresa já existe no banco, atualizar e enriquecer os dados (adicionando `place_id`, categoria específica, avaliações) em vez de criar um registro duplicado.
3. **Limpeza Automática no Banco**: Executar rotina de deduplicação e fusão na inicialização da aplicação, expurgando registros redundantes e consolidando os relatórios.

## Conclusão da Sprint
- Deduplicação inteligente multi-critério implementada e ativa. As 30 duplicatas existentes foram eliminadas, mantendo os registros mais ricos em dados (com place_id, categoria e avaliações). O banco agora possui 167 empresas reais únicas de Piracicaba sem nenhuma duplicata. Todos os 36 testes passando (100%), linter aprovado e sincronizado no GitHub.

---

## 📋 Checklist de Progresso Obrigatório (Regra dos 10%)

- [x] **10%** - Diagnóstico sistemático com evidência concreta da duplicação (discrepância entre chaves `pid:` e `tc:` para a mesma empresa)
- [x] **20%** - Criar função canônica de normalização de títulos (`normalize_business_title`) removendo pontuações e sufixos repetitivos
- [x] **30%** - Atualizar `upsert_lead()` com busca prévia multi-critério (match por `place_id`, `whatsapp_clean + cidade` e `título normalizado + cidade`)
- [x] **40%** - Implementar fusão e enriquecimento inteligente de dados ao atualizar empresas existentes
- [x] **50%** - Criar função de limpeza e consolidação `deduplicate_existing_leads_db()` executada na inicialização do sistema
- [x] **60%** - Executar consolidação no banco SQLite (`data/painel_busca.db`), eliminando as 30 duplicatas de Piracicaba
- [x] **70%** - Adicionar testes unitários de deduplicação idempotente em `tests/test_database.py` (36 testes passando)
- [x] **80%** - Validação de qualidade de código e linter `taste-skill` (0 erros)
- [x] **90%** - Execução da suíte completa de testes automatizados `pytest`
- [x] **100%** - Atualização de grafo `graphify update .`, validação da interface limpa em `http://127.0.0.1:8090` e sincronização com GitHub

---

## 📝 Diário de Bordo & Checkpoints Salvos (10% em 10%)
| % Concluído | Data / Hora | Descrição do Progresso / Entrega Parcial | Arquivos Modificados |
| :---: | :---: | :--- | :--- |
| **10%** | 31/10/2026 19:11 | Diagnóstico: identificadas 26 empresas duplicadas decorrentes de conflito entre chaves `pid:` (com place_id) e `tc:` (sem place_id). | `Sprint atual.md` |
| **20-60%** | 31/10/2026 19:14 | Implementadas funções `normalize_business_title()`, `_find_existing_lead_id()`, `upsert_lead()` com fusão inteligente e `deduplicate_existing_leads_db()`. 30 duplicatas expurgadas do banco ativo. | `app/database.py`, `app/main.py`, `data/painel_busca.db` |
| **70-100%** | 31/10/2026 19:16 | Adicionado teste unitário `test_multicriteria_deduplication_and_enrichment`, 36/36 testes passando, grafo atualizado e sincronizado no GitHub. | `tests/test_database.py`, `graphify-out/*`, `Sprint atual.md` |

---
*Gerado e mantido automaticamente pelo protocolo de sincronismo Antigravity <-> Operador <-> Obsidian.*
