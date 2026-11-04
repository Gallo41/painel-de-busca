# Empresa de agentes do Painel de Busca

## Finalidade e estado real

O CEO define a ideia e aprova; o sócio participa da operação e acompanha os clientes. O gerente-geral coordena especialistas entre os dois responsáveis e os futuros clientes encontrados pelo painel. A oferta é criação de sites, modernização e sistemas sob medida.

Os 12 arquivos em `.claude/agents/` contêm nome e descrição no cabeçalho YAML e instruções em português. São definições de papéis, não um motor autônomo. Esta entrega não conecta modelos, não adiciona agentes à interface do painel, não ativa disparos e não implementa bloqueio técnico de aprovação na API. As regras abaixo são operacionais; uma futura automação precisará implementá-las e testá-las no servidor.

## Como começar

Em um ambiente que suporte agentes de projeto em `.claude/agents/`, solicite o gerente-geral pelo nome. Verifique no ambiente se ele foi carregado; a descoberta automática não foi testada aqui. Em outras IAs, forneça o arquivo do papel, este guia e o contexto mínimo da tarefa; o diretório por si só não configura Codex, Gemini ou DeepSeek.

Exemplo de pedido:

> gerente-geral: analise os leads que eu selecionar no painel. Organize a pesquisa, prepare um protótipo editável para cada lead aprovado para desenvolvimento e entregue os textos de abordagem para eu revisar. Informe custos desconhecidos e não publique nem envie nada. Meu sócio cuidará dos leads que eu atribuir a ele.

Informe IDs reais dos leads e responsável humano. Se ainda não houver seleção, o pesquisador pode propor uma lista fundamentada para revisão. Não extraia toda a base sem necessidade.

## Fluxo de trabalho

1. **Pedido e triagem:** gerente-geral recebe a ideia, consulta contexto e define escopo e critérios de aceite.
2. **Pesquisa:** pesquisador confirma dados do lead, problema observado e oportunidade; distingue hipóteses de fatos.
3. **Viabilidade:** contador estima custos com premissas explícitas; analista identifica métricas e dados faltantes.
4. **Protótipo local:** desenvolvedor constrói em passos pequenos com web-designer e copywriter. O CEO recebe instruções para editar.
5. **Revisão:** testador e dev-seguranca verificam o escopo; desenvolvedor corrige; gerente confere evidências e expõe pendências.
6. **Aprovação do CEO:** apresenta-se a versão concreta, com escopo, destino, custo e riscos conhecidos. Alteração relevante exige nova aprovação.
7. **Comercial:** vendedor prepara abordagem somente para protótipos revisados; gestor-de-trafego prepara campanhas quando solicitado. Enviar, publicar e gastar são aprovações separadas de aprovar o protótipo.
8. **Atendimento e aprendizagem:** atendente prepara respostas baseadas no contratado; analista acompanha dados reais e recomenda melhorias.

Não é obrigatório acionar os 12 agentes em toda tarefa. Distribua trabalho independente e evite dois agentes editando o mesmo arquivo. Se a ferramenta não permitir delegação, registre repasses pendentes em vez de alegar trabalho executado.

## Responsabilidades

| Agente | Entrega principal | Repasse principal |
| --- | --- | --- |
| gerente-geral | Pacote revisado e decisões pendentes | CEO e sócio |
| pesquisador | Briefing com fontes por lead | Desenvolvedor e copywriter |
| desenvolvedor | Protótipo editável e instruções | Testador e dev-seguranca |
| web-designer | Telas responsivas e revisão visual | Desenvolvedor |
| copywriter | Textos sustentados pela oferta real | Designer, vendedor e tráfego |
| gestor-de-trafego | Campanhas em rascunho e plano de medição | Gerente e CEO |
| vendedor | Abordagens e follow-ups vinculados ao protótipo | Gerente e responsável pelo lead |
| contador | Memória de cálculo, preço e margem | Gerente e CEO |
| analista | Indicadores e recomendações fundamentadas | Gerente e contador |
| testador | Defeitos reproduzíveis e evidências de reteste | Desenvolvedor e gerente |
| dev-seguranca | Achados, correções e riscos residuais | Desenvolvedor e gerente |
| atendente | Respostas propostas e encaminhamentos | Gerente e responsável pelo cliente |

## Registro mínimo de tarefa e repasse

Use este modelo no registro de trabalho autorizado, sem versionar dados pessoais de clientes:

```text
Tarefa / ID do lead:
Responsável humano: CEO ou sócio designado
Objetivo e critérios de aceite:
Agente responsável / próximo agente:
Fatos e fontes (arquivo ou URL e data):
Hipóteses e informações faltantes:
Entrega e versão/caminho:
Verificações executadas e evidências:
Falhas / limitações / perguntas:
Estado: rascunho | em revisão | bloqueado | aguardando CEO | aprovado | executado
Aprovação: autor, data, ação, versão, destino/canal e limite de gasto (se houver)
Evidência de execução, quando autorizada:
Próximo passo:
```

Esses estados são uma convenção documental, não novos campos no banco. Aprovação não equivale a execução; somente registre enviado/publicado com evidência. Não presuma que `ready` na fila significa aprovado. A autorização de uma versão não vale para outra mensagem, outro destinatário ou aumento de orçamento. Em conflito entre orientações dos sócios, o gerente pede decisão ao CEO.

## Gemini, DeepSeek e outras IAs

Podem apoiar por repasse manual: enviar o papel específico, briefing anonimizado, referências necessárias e formato esperado de resposta. Receber o resultado como proposta não verificada e submetê-lo à mesma revisão. Não enviar banco, credenciais, conversas privadas ou listas de leads a provedores externos sem autorização específica. Não é necessário configurar chaves para usar estes arquivos.

Integração futura por API deve ser uma tarefa separada, com provedor e limites de custo escolhidos, armazenamento seguro de chaves, controle de acesso, registro de aprovação no servidor, prevenção de duplicidade e botão de interrupção. Este documento não afirma que esses mecanismos existem.

## Skills e qualidade

Escolha skills disponíveis conforme o trabalho: pesquisa de leads (`google-maps-scraper`), design (`frontend-design` e orientações de acessibilidade), teste exploratório (`dogfood`), revisão de segurança (`security-audit`) e verificação antes da conclusão. Leia a skill antes de aplicar e registre limitações. A existência de uma skill não comprova integração nem execução e não autoriza publicação ou contato externo.
