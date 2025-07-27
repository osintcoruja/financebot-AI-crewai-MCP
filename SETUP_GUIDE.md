# Guia de Instalação do Financebot

Este guia irá ajudá-lo a configurar e rodar o aplicativo Financebot.

## Pré-requisitos

1. **Python 3.8+**
2. **Node.js (v14 LTS ou superior)**
   - Baixe e instale em https://nodejs.org/en/
3. **uv** (gerenciador de pacotes Python)
   - Instale via pip:
     ```bash
     pip install uv
     ```
   - Ou via curl (Linux/macOS):
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```

## Passos de Instalação

### 1. Clone o repositório (se ainda não fez)

```bash
git clone <url-do-repositorio>
cd financebot_3
```

### 2. Instale as dependências Python

```bash
uv sync
```

### 3. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Obrigatório: Chave da OpenAI
OPENAI_API_KEY=sua_chave_openai_aqui

# Opcional: Token do Supabase (se for usar o MCP do Supabase)
SUPABASE_ACCESS_TOKEN=seu_token_supabase_aqui
```

### 4. Instale as dependências dos servidores MCP

#### Para YFinance (dados financeiros):
```bash
uvx install yfmcp@latest
```

#### Para Supabase (banco de dados):
```bash
npm install -g @supabase/mcp-server-supabase@latest
# Ou via npx (sem instalação global):
npx @supabase/mcp-server-supabase@latest
```

## Rodando a Aplicação

### Opção 1: Executar via main.py (Recomendado)

1. Execute o aplicativo principal:
```bash
python main.py
```
2. Escolha uma das opções:
   - **Opção 1**: Executar servidor MCP (`uv run src/mcp_server.py`)
   - **Opção 2**: Executar interface web (`streamlit run src/app.py`)
   - **Opção 3**: Ver instruções para executar ambos

### Opção 2: Executar comandos diretamente

#### Para o servidor MCP:
```bash
uv run src/mcp_server.py
```

#### Para a interface web:
```bash
streamlit run src/app.py
```

### Opção 3: Executar ambos simultaneamente

Para usar o sistema completo, você precisará de dois terminais:

**Terminal 1 (Servidor MCP):**
```bash
uv run src/mcp_server.py
```

**Terminal 2 (Interface Web):**
```bash
streamlit run src/app.py
```

### Como funciona:

- O `main.py` executa os comandos diretamente
- Você vê os logs nativos de cada componente
- Para usar o sistema completo, execute MCP e Streamlit em terminais separados
- A interface web será aberta em `http://localhost:8501`

## Solução de Problemas

### Problemas Comuns

1. **Timeout de conexão com MCP**
   - O app agora lida melhor com ausência dos servidores MCP
   - Você verá uma mensagem amigável se os servidores não estiverem disponíveis

2. **Chave da OpenAI ausente**
   - Certifique-se de ter uma chave válida no arquivo `.env`
   - Obtenha em: https://platform.openai.com/api-keys

3. **Token do Supabase**
   - Só é necessário se for usar recursos de banco de dados
   - Pegue no painel do seu projeto Supabase

### Logs e Encoding
- Se aparecerem erros de encoding no terminal, execute `chcp 65001` antes de rodar o script para garantir suporte a Unicode.

## Arquitetura

- **FastMCP**: Comunicação com servidores MCP
- **CrewAI**: Gerenciamento dos agentes e tarefas
- **Streamlit**: Interface web
- **OpenAI**: Respostas de IA
- **YFinance MCP**: Dados financeiros
- **Supabase MCP**: Banco de dados

## Exemplos de Uso

Depois de rodar, você pode perguntar:
- "Qual o preço atual da ação AAPL?"
- "Mostre os dados financeiros mais recentes da Microsoft"
- "Quanto gastei no mês de julho?"

O sistema escolherá automaticamente a melhor ferramenta para responder sua pergunta. 
