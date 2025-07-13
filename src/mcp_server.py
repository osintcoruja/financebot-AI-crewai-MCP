from dotenv import load_dotenv
from fastmcp import FastMCP
from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew, Process
from crewai.memory import EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage
from crewai_tools.adapters.mcp_adapter import MCPServerAdapter
from mcp import StdioServerParameters
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
mcp = FastMCP("multi-agent-server")

# Function for per-user memory
def get_user_memory(user_id: str):
    return EntityMemory(
        storage=RAGStorage(
            embedder_config={
                "provider": "openai",
                "config": {"model": "text-embedding-3-small"},
            },
            type="short_term",
            path=f"./memory_store/{user_id}/",
        )
    )


def try_initialize_mcp_adapter(params, name):
    """Tente inicializar um adaptador MCP com tratamento de tempo limite."""
    try:
        logger.info(f"Tentando inicializar o adaptador MCP {name}...")
        adapter = MCPServerAdapter(params)
        logger.info(f"Adaptador MCP {name} inicializado com sucesso")
        return adapter
    except Exception as e:
        logger.error(f"Falha ao inicializar o adaptador MCP {name}: {e}")
        return None


def extract_text(obj):
    # Se for string, retorna direto
    if isinstance(obj, str):
        return obj
    # Se for dict, tenta achar texto em campos comuns
    if isinstance(obj, dict):
        for key in ["result", "output", "raw", "data"]:
            value = obj.get(key)
            if isinstance(value, str):
                return value
            if isinstance(value, dict) or isinstance(value, list):
                nested = extract_text(value)
                if nested:
                    return nested
        for v in obj.values():
            nested = extract_text(v)
            if nested:
                return nested
    # Se for lista, tenta extrair de cada item
    if isinstance(obj, list):
        for item in obj:
            nested = extract_text(item)
            if nested:
                return nested
    # Se for objeto com .text, .content, .data, etc.
    for attr in ["text", "content", "data", "raw"]:
        if hasattr(obj, attr):
            value = getattr(obj, attr)
            nested = extract_text(value)
            if nested:
                return nested
    return None


async def multi_analyst_core(question: str, user_id: str) -> str:
    """Core da ferramenta multi-analista (sem o decorator MCP)."""
    # MCP YFinance 
    yfinance_params = StdioServerParameters(command="uvx", args=["yfmcp@latest"])
    # MCP Supabase - https://github.com/supabase-community/supabase-mcp
    supabase_params = StdioServerParameters(
        command="npx",
        args=["-y", "@supabase/mcp-server-supabase@latest"],
        env={"SUPABASE_ACCESS_TOKEN": os.getenv("SUPABASE_ACCESS_TOKEN") or "", **os.environ},
    )

    mcp_adapters = []
    tools = []
    
    # Try to initialize adapters with graceful error handling
    yfinance_adapter = try_initialize_mcp_adapter(yfinance_params, "YFinance")
    if yfinance_adapter:
        mcp_adapters.append(yfinance_adapter)
        tools.extend(yfinance_adapter.tools)
    
    supabase_adapter = try_initialize_mcp_adapter(supabase_params, "Supabase")
    if supabase_adapter:
        mcp_adapters.append(supabase_adapter)
        tools.extend(supabase_adapter.tools)
        # print("\n\nSUPABASE ADAPTER: ", supabase_adapter)
        # print("\n\nYFINANCE ADAPTER: ", yfinance_adapter)
        # print("\n\nTOOLS: ", tools)

    # Check if we have any working tools
    if not tools:
        logger.warning("Nenhuma ferramenta MCP disponível. Retornando resposta básica.")
        return f"Peço desculpas, mas no momento não consigo acessar fontes de dados externas para responder à sua pergunta: '{question}'. Os servidores MCP necessários (yfinance e supabase) não estão disponíveis. Certifique-se de que os servidores MCP estejam funcionando e acessíveis."

    try:
        llm = ChatOpenAI(model="gpt-4o-mini")  # Fixed model name
        memory = get_user_memory(user_id)

        # Determine agent capabilities based on available tools
        available_tools = []
        if yfinance_adapter:
            available_tools.append("YFinance (financial data)")
        if supabase_adapter:
            available_tools.append("Supabase (database)")
        
        tool_description = ", ".join(available_tools) if available_tools else "limited tools"

        multi_analyst = Agent(
            role="Analista Profissional de Dados e Finanças",
            goal=f"Responda às perguntas usando as ferramentas disponíveis: {tool_description}",
            backstory="Especialista em SQL, ações, KPIs e bancos de dados. Adapta-se às ferramentas disponíveis e oferece a melhor resposta possível.",
            tools=tools,
            verbose=True,
            llm=llm,
            allow_delegation=False,
        )

        task = Task(
            description=f"Responder a esta pergunta do usuário: {question}",
            expected_output="Resposta útil usando a ferramenta disponível mais adequada.",
            tools=tools,
            agent=multi_analyst,
        )

        crew = Crew(
            agents=[multi_analyst],
            tasks=[task],
            process=Process.sequential,
            memory=True,
            entity_memory=memory,
            verbose=True,
        )

        result = await crew.kickoff_async()
        text = extract_text(getattr(result, "raw", result))
        # print("DEBUG FINAL TEXT:", repr(text))
        if text and isinstance(text, str):
            return text
        return "No answer found."
    except Exception as e:
        logger.error(f"Error during crew execution: {e}")
        return f"Encontrei um erro ao processar sua pergunta: {str(e)}"
    finally:
        # Clean up adapters
        for adapter in mcp_adapters:
            try:
                adapter.stop()
            except Exception as cleanup_error:
                logger.error(f"Erro durante a limpeza do adaptador: {cleanup_error}")


@mcp.tool(name="multi_analyst")
async def multi_analyst_tool(question: str, user_id: str) -> str:
    """Resolve questões financeiras e de BD usando acesso unificado a ferramentas."""
    return await multi_analyst_core(question, user_id)


# Test function that can be called directly
async def test_multi_analyst(question: str, user_id: str) -> str:
    """Função de teste para chamada direta de main.py."""
    return await multi_analyst_core(question, user_id)


if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8005)