# 🚀 Guia de Instalação e Uso Rápido — Painel de Busca

Este guia foi feito especialmente para você ou seu sócio começarem a usar o **Painel de Busca, Raio-X & Prospecção de Leads** no Windows em menos de 2 minutos.

---

## ⚡ Instalação em 1 Clique (Método Recomendado)

1. Baixe o projeto (via Git Clone ou baixando o arquivo ZIP do GitHub e extraindo numa pasta do seu computador).
2. Abra a pasta do projeto e dê **dois cliques** em:
   ```cmd
   INSTALAR_PAINEL.bat
   ```
3. O instalador inteligente cuidará de tudo:
   - ✅ Verifica e instala o Python se necessário (via Windows Package Manager).
   - ✅ Cria o ambiente isolado virtual (`.venv`) para não bagunçar nada no seu PC.
   - ✅ Instala todas as dependências (FastAPI, Uvicorn, Pydantic, HTTPX).
   - ✅ Cria as pastas locais de banco de dados e exportações.
   - ✅ **Gera um atalho direto na sua Área de Trabalho** com o ícone do Painel de Busca!

---

## 💻 Como Abrir no Dia a Dia

Depois de instalado, você nunca mais precisa configurar nada. Sempre que for trabalhar na prospecção de clientes:

- **Pelo Desktop**: Dê dois cliques no ícone **`Painel de Busca`** na sua Área de Trabalho.
- **Pela Pasta**: Dê dois cliques em **`iniciar_painel.bat`**.

O painel abrirá automaticamente no seu navegador em:
👉 **`http://localhost:8090`**

*(A documentação interativa da API também fica disponível em `http://localhost:8090/docs`).*

> [!NOTE]
> Deixe a janela do terminal aberta enquanto estiver prospectando. Para encerrar o sistema, basta fechar a janela ou apertar `Ctrl + C`.

---

## 🛡️ Sistema com Auto-Cura Integrado

Se você esquecer de rodar o instalador e der dois cliques direto em `iniciar_painel.bat`, não se preocupe:
O sistema detecta automaticamente que as dependências ou o ambiente ainda não foram configurados e executa o assistente de instalação sozinho, sem fechar nem dar erro!

---

## ⚙️ Dúvidas Frequentes & Resolução de Problemas

### 1. O instalador avisou que o Python não foi encontrado e o winget falhou
1. Entre no site oficial: [python.org/downloads](https://www.python.org/downloads/)
2. Baixe o instalador mais recente para Windows.
3. **MUITO IMPORTANTE**: Na primeiríssima tela do instalador, marque a caixinha:
   - **`[X] Add python.exe to PATH`** (Adicionar Python às variáveis de ambiente).
4. Clique em **Install Now**.
5. Quando concluir, volte na pasta do Painel e dê dois cliques em `INSTALAR_PAINEL.bat`.

### 2. Porta 8090 já em uso
Se a porta 8090 estiver ocupada por outro programa ou uma instância anterior:
1. Abra o Gerenciador de Tarefas (`Ctrl + Shift + Esc`).
2. Finalize processos `python.exe` antigos ou reinicie a máquina.

### 3. Como gerar um executável `.exe` independente?
Se preferir rodar como um programa compilado:
1. Dê dois cliques em `scripts\compilar_exe.bat`.
2. O executável será gerado em `dist\PainelDeBusca\PainelDeBusca.exe`.
3. Um atalho `Painel de Busca (EXE)` será criado na sua Área de Trabalho.
