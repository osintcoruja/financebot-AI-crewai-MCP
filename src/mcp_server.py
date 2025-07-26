# === PARTE 1: Imports, configuração e MCP ===

from dotenv import load_dotenv
import os
import logging
from datetime import datetime, timedelta
from fastmcp import FastMCP

from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew, Process
from crewai.memory import EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage
from crewai_tools.adapters.mcp_adapter import MCPServerAdapter
from tools.relative_date_resolver import resolve_relative_date

load_dotenv()
mcp = FastMCP("assistente_financeiro_inteligente")

# Configura logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Parâmetros MCP
try:
    from mcp import StdioServerParameters
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

def try_initialize_mcp_adapter(params, name):
    try:
        logger.info(f"Inicializando adaptador MCP {name}...")
        return MCPServerAdapter(params)
    except Exception as e:
        logger.error(f"Erro ao iniciar MCP {name}: {e}")
        return None

from crewai.memory import EntityMemory
memoria_nova = EntityMemory()  # isso é uma memória "zerada"

# === PARTE 2: Memória isolada e classificação de conversa ===

def get_session_memory(user_id: str, session_id: str):
    return EntityMemory(
        storage=RAGStorage(
            embedder_config={
                "provider": "openai",
                "config": {"model": "text-embedding-3-small"},
            },
            type="short_term",
            path=f"./memory_store/{user_id}/{session_id}/",
        )
    )

def is_new_conversation(question: str) -> bool:
    q = question.strip().lower()
    if q in {"sim", "não", "confirmar", "cancelar", "ok", "certo"} or q.isdigit():
        return False
    if any(p in q for p in ["gastei", "recebi", "investi", "preço", "cotação", "valor", "quanto", "quero", "oi", "olá"]):
        return True
    return len(q.split()) > 1

# === PARTE 3: Agente Classificador + Orquestrador ===

def criar_agente_classificador(tools, llm):
    return Agent(
        role="Classificador de Solicitações",
        goal="Identificar se a solicitação do usuário é sobre controle financeiro ou consulta de ativos.",
        backstory="Especialista em compreender intenções financeiras e organizar informações.",
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

def criar_agente_orquestrador(tools, llm):
    return Agent(
        role="Orquestrador de Tarefas Financeiras",
        goal="Analisar a classificação e delegar a execução para a crew apropriada.",
        backstory="Gerente responsável por direcionar tarefas para o time certo, garantindo fluidez e sucesso.",
        tools=tools,
        llm=llm,
        verbose=True,
        allow_delegation=True
    )

# === PARTE 4: Crew: Controle Financeiro ===

def crew_controle_financeiro(tools, llm, memory, dados_json):
    coletor_controle_financeiro = Agent(
        role="Coletor de Dados Financeiros",
        goal="Extrair e organizar os dados da transação financeira.",
        backstory="Especialista em captar detalhes de receitas e despesas em linguagem natural.",
        tools=tools,
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    gestor_dados = Agent(
        role="Gestor de Dados SQL",
        goal="Executar comandos SQL no Supabase conforme os dados coletados.",
        backstory="Especialista em persistência de dados e manipulação de transações.",
        tools=tools,
        llm=llm,
        memory=memoria_nova,
        verbose=True,
        allow_delegation=False
    )

    redator = Agent(
        role="Comunicador Financeiro",
        goal="Gerar resposta clara e amigável ao usuário.",
        backstory="Responsável por traduzir os dados da transação realizada no banco Supabase para linguagem humana.",
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    task_coleta_controle_financeiro = Task(
    description=f"""📥 TAREFA: EXTRAÇÃO E ORGANIZAÇÃO DE DADOS FINANCEIROS

    🎯 Objetivo: Interpretar a mensagem do usuário e **extrair um JSON completo** com os seguintes dados:

    - valor (float)
    - tipo (receita ou despesa)
    - categoria (como 'Salário', 'Alimentação', etc.)
    - conta_id (sempre 5)
    - data_transacao (formato ISO: YYYY-MM-DD)
    - descricao (sempre usar a frase original)

    ⚠️ **USO OBRIGATÓRIO DA TOOL `resolve_relative_date` PARA CALCULAR A DATA**:
    - A expressão temporal (como "hoje", "ontem", "15/07") **deve ser passada para a ferramenta `resolve_relative_date`**. 
    Use a ferramenta resolve_relative_date assim:
    Action: resolve_relative_date  
    Action Input: {{"input": "ontem"}}
    - Nunca assuma a data diretamente — utilize sempre a tool para garantir precisão.

    🧠 **Regras de extração obrigatórias**:

    - **Valor**: identificar números como "500", "mil", "R$ 200"
    - **Tipo**:
    - receita → "recebi", "ganhei", "vendi"
    - despesa → "gastei", "paguei", "comprei"
    - **Categoria**: sugerir com base no contexto (ex: "mercado" → "Alimentação")
    - **Conta**: sempre usar `conta_id=5` se não especificado
    - **Data**: extrair expressão e converter usando a tool `resolve_relative_date`
    - **Descrição**: usar a frase original (ex: "ganhei 500 de salário")

    📤 **SAÍDA FINAL DEVE SER NO FORMATO JSON CONFORME O EXEMPLO ABAIXO** a ser encaminhado para o agente gestor_dados:
    
    "dados": {{
        "valor": 500.0,
        "tipo": "receita",
        "categoria": "Salário",
        "conta_id": 5,
        "data_transacao": "2025-07-25",
        "descricao": "ganhei 500 de salário"
    }}

    👑 **REGRAS DE OURO**:
    - A data deve vir da tool — nunca invente ou assuma diretamente.
    """,
        expected_output="""Objeto JSON {dados_json} estruturado com todos os campos extraídos corretamente e com data_transacao 
        já resolvida pela tool resolve_relative_date""",
        tools=[resolve_relative_date],
        agent=coletor_controle_financeiro
    )

    task_gestor_dados = Task(
        description=f"""Executar a transação no banco Supabase com os dados fornecidos pelo agente coletor_controle_financeiro.
        Os dados são: {dados_json}. Os dados devem estar alinhado com aqueles coletados pelo agente coletor_controle_financeiro.""",
        expected_output="Resultado da queryno banco Supabase",
        agent=gestor_dados
    )

    task_redator = Task(
        description="""
        Sua missão é FORMULAR a resposta final com base no resultado da transação ou da consulta no banco Supabase.

        🎯 FORMATO PADRÃO PARA CONTROLE FINANCEIRO (CONTROLE_FINANCEIRO):
        - Sempre que possível, use esse modelo fixo:
        
        💸 Sua transação foi registrada com sucesso:
        • Valor: R$ {dados_json["valor"]}
        • Categoria: {dados_json["categoria"]}
        • Data: {dados_json["data_transacao"]}
        • Conta: {dados_json["conta_id"]}
        📝 Descrição: {dados_json["descricao"]}

        ⚠️ NUNCA inclua "ID de conta", "ID de categoria", "json" ou qualquer detalhe técnico.
        ⚠️ Sempre formate o valor como moeda brasileira ("R$ 150,00")
        ⚠️ Sempre use data no formato DD/MM/AAAA

        🎯 FORMATO PADRÃO PARA CONSULTA DE ATIVO (CONSULTA_ATIVO):
        - Exemplo: "A cotação atual de PETR4 é R$ 32,70."

        👑 REGRAS DE OURO:
        - NUNCA exiba código, JSON bruto, IDs ou termos técnicos
        - A resposta deve ser CLARA, HUMANA e NATURAL
        - Inicie com um ícone: 💸 ou 📈 dependendo do tipo
        """,
        expected_output="""Resposta final clara e amigável para o usuário e fiel ao resultado da 
        transação ou da consulta no banco Supabase feita pelo agente gestor_dados""",
        agent=redator
    )


    return Crew(
        agents=[coletor_controle_financeiro, gestor_dados, redator],
        tasks=[task_coleta_controle_financeiro, task_gestor_dados, task_redator],
        process=Process.sequential,
        memory=True,
        entity_memory=memory,
        verbose=True,
    )

# === PARTE 5: Crew: Consulta de Ativos Financeiros ===

def crew_consulta_ativos(tools, llm, memory, dados_json):
    coletor_ativos = Agent(
        role="Coletor de Dados de Ativos",
        goal="Extrair informações necessárias para consulta de ativos (ex: símbolo, tipo de dado).",
        backstory="Especialista em finanças e análise de mercado, focado em interpretar pedidos de ativos.",
        tools=tools,
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    analista_ativos = Agent(
        role="Consultor de Mercado Financeiro",
        goal="Consultar dados atualizados do ativo usando YFinance.",
        backstory="Profissional de mercado que busca preços, tendências e dados em tempo real.",
        tools=tools,
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    redator = Agent(
        role="Redator de Informações de Ativos",
        goal="Responder ao usuário com clareza sobre o ativo solicitado.",
        backstory="Responsável por transformar resultados técnicos de mercado em mensagens claras.",
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    task_coleta_ativos = Task(
        description=f"""
        Extrair informações necessárias para consulta de ativos.
        Verificar se tem:
            - simbolo: código do ativo (PETR4, USDBRL, ^BVSP)
            - tipo_consulta: "cotacao", "analise", "historico"
        - Sempre usar a tool `resolve_relative_date` para calcular a data.
        - Use a ferramenta resolve_relative_date assim:
            Action: resolve_relative_date  
            Action Input: {{"input": "ontem"}}
        - Resultado:
        {{
        "dados": {{
                    "simbolo": "PETR4", 
                    "tipo_consulta": "cotacao" | "analise",
                    "data": "2025-07-25"
                }}
        }}
        """,
        expected_output="Json com informações necessárias para consulta de ativos",
        agent=coletor_ativos
    )

    task_analise_ativos = Task(
        description=f"""Obter informações sobre o ativo usando os dados: {dados_json}""",
        expected_output="Cotação ou análise do ativo",
        agent=analista_ativos
    )

    task_redator = Task(
        description="Formate e entregue o resultado ao usuário de forma clara e natural.",
        expected_output="Resposta final amigável sobre o ativo",
        agent=redator
    )

    return Crew(
        agents=[coletor_ativos, analista_ativos, redator],
        tasks=[task_coleta_ativos, task_analise_ativos, task_redator],
        process=Process.sequential,
        memory=True,
        entity_memory=memory,
        verbose=True
    )

# === PARTE 6: Execução principal ===

async def assist_financ_core(question: str, user_id: str) -> str:
    llm = ChatOpenAI(model="gpt-4o-mini")
    
    is_new = is_new_conversation(question)
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    memory = get_session_memory(user_id, session_id)

    if is_new:
        try:
            memory.clear()
        except: pass

    # Inicializa adaptadores
    tools = []
    tools.append(resolve_relative_date)

    supabase = try_initialize_mcp_adapter(StdioServerParameters(
        command="npx",
        args=["-y", "@supabase/mcp-server-supabase@latest", "--project-ref=rhtnuzfmshfmreuffqox"],
        env={"SUPABASE_ACCESS_TOKEN": os.getenv("SUPABASE_ACCESS_TOKEN", ""), **os.environ}
    ), "Supabase")

    yfinance = try_initialize_mcp_adapter(StdioServerParameters(
        command="uvx",
        args=["yfmcp@latest"]
    ), "YFinance")

    for adapter in [supabase, yfinance]:
        if adapter:
            tools.extend(adapter.tools)
            tools.append(resolve_relative_date) # Adiciona a tool de resolução de data relativa

    classificador = criar_agente_classificador(tools, llm)

    classificacao_task = Task(
        description=f"""
        📥 Sua missão é analisar a seguinte frase: "{question}" e **obrigatoriamente** gerar um objeto JSON no seguinte formato:

        📋 FORMATO FIXO OBRIGATÓRIO:
        {{
        "classificacao": "CONTROLE_FINANCEIRO" | "CONSULTA_ATIVO",
        "status": "COMPLETO",
        "dados": {{
            // para CONTROLE_FINANCEIRO:
            "valor": 1500.00,
            "tipo": "receita" | "despesa",
            "conta_id": 5,
            "categoria": "Alimentação",
            "data_transacao": "2025-07-20 | hoje | ontem | anteontem | 15/07/2025",
            "descricao": "Descrição livre da transação"

            // para CONSULTA_ATIVO:
            "simbolo": "PETR4",
            "tipo_consulta": "cotacao" | "analise"
        }}
        }}

        ⚠️ Regras obrigatórias:
        - NÃO SAIA do formato acima.
        - NÃO inclua observações, explicações ou textos soltos.
        - SEMPRE inclua status="COMPLETO"
        - Use sempre conta_id=5 se não informado
        - Sempre que possível, preencha a descrição com base na frase original
        """,
        expected_output="Objeto JSON {dados_json} estruturado como especificado acima",
        agent=classificador
    )

    crew_classificacao = Crew(
        agents=[classificador],
        tasks=[classificacao_task],
        process=Process.sequential,
        memory=True,
        entity_memory=memory,
        verbose=True,
    )

    import json

    resultado = await crew_classificacao.kickoff_async()
    resposta_str = str(resultado)

    try:
        resposta_json = json.loads(resposta_str)
    except:
        return "Erro ao interpretar a resposta do classificador."

    logger.info(f"🔍 Resposta JSON do classificador: {resposta_json}")

    classificacao = resposta_json.get("classificacao")
    dados = resposta_json.get("dados")


    # Decide qual crew executar
    if classificacao == "CONTROLE_FINANCEIRO":
        crew = crew_controle_financeiro(tools, llm, memory, dados)
    elif classificacao == "CONSULTA_ATIVO":
        crew = crew_consulta_ativos(tools, llm, memory, dados)
    else:
        return "Classificação desconhecida. Não sei o que fazer com isso."

    # Executa a próxima etapa
    resposta_final = await crew.kickoff_async()
    return str(resposta_final)


# === PARTE 7: Tool MCP + função de teste e entrada CLI ===

@mcp.tool(name="assistente_financeiro_inteligente")
async def assistente_financeiro_tool(question: str, user_id: str) -> str:
    return await assist_financ_core(question, user_id)

async def test_assistente_financeiro(question: str, user_id: str):
    return await assist_financ_core(question, user_id)


if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8005)
