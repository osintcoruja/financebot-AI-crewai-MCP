# Guia de Instalação do Super Agent AI

Este guia irá ajudá-lo a configurar e rodar o aplicativo Super Agent AI.

## Pré-requisitos

1. **Python 3.8+** instalado em seu sistema
2. **Node.js** (para o servidor MCP do Supabase)
3. **uv** (para o servidor MCP do YFinance)

## Passos de Instalação

### 1. Instale as dependências Python

```bash
pip install -r requirements.txt
```

### 2. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Obrigatório: Chave da OpenAI
OPENAI_API_KEY=sua_chave_openai_aqui

# Opcional: Token do Supabase (se for usar o MCP do Supabase)
SUPABASE_ACCESS_TOKEN=seu_token_supabase_aqui
```

### 3. Instale as dependências dos servidores MCP

#### Para YFinance (dados financeiros):
```bash
# Instale o uv se ainda não tiver
pip install uv
# O servidor MCP do yfinance será instalado automaticamente via uvx
```

#### Para Supabase (banco de dados):
```bash
# Instale as dependências Node.js
npm install -g @supabase/mcp-server-supabase
```

## Rodando a Aplicação

### Opção 1: Interface Web (Streamlit) - Recomendado

1. Inicie o servidor MCP (agora automático pelo main.py):
```bash
python main.py
```
2. Escolha a opção 2 para abrir a interface web.
3. O navegador abrirá em `http://localhost:8501`.

### Opção 2: Teste pelo Terminal

```bash
python main.py
```
Escolha a opção 1 para testar via terminal.

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
- "Quais tabelas existem no banco?"

O sistema escolherá automaticamente a melhor ferramenta para responder sua pergunta. 
