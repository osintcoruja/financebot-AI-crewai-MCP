import streamlit as st
import asyncio
from fastmcp import Client
import json
import uuid
import nest_asyncio

nest_asyncio.apply()

# Configuração da página (da ideia do app.py)
st.set_page_config(
    page_title="Assistente Financeiro",
    page_icon="💰",
    layout="wide"
)

# Título da aplicação (da ideia do app.py)
st.title("💰 Assistente Financeiro")
st.markdown("Sistema inteligente para gerenciar suas finanças pessoais!")

# ID único do usuário e namespace de memória
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibir histórico de mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def extract_text_frontend(obj, level=0):
    """
    Extrai de forma recursiva o texto principal de uma resposta complexa (dict/list).
    """
    if level > 10:  # Evita recursão infinita
        return ""

    if isinstance(obj, str):
        return obj

    # Handle CallToolResult and similar objects
    if hasattr(obj, 'content'):
        return extract_text_frontend(obj.content, level + 1)
    
    if hasattr(obj, 'result'):
        return extract_text_frontend(obj.result, level + 1)
    
    if hasattr(obj, 'output'):
        return extract_text_frontend(obj.output, level + 1)
    
    if hasattr(obj, 'response'):
        return extract_text_frontend(obj.response, level + 1)
    
    # Convert to dict if possible
    if hasattr(obj, '__dict__'):
        obj = obj.__dict__
    elif hasattr(obj, 'model_dump'):
        obj = obj.model_dump()

    if isinstance(obj, dict):
        # Prioriza chaves conhecidas que contêm a resposta final
        for key in ["result", "output", "answer", "response", "data", "raw", "content", "text", "message"]:
            if key in obj:
                res = extract_text_frontend(obj[key], level + 1)
                if res and isinstance(res, str):
                    return res
        # Se não encontrar, busca em todos os valores
        for value in obj.values():
            res = extract_text_frontend(value, level + 1)
            if res and isinstance(res, str):
                return res

    if isinstance(obj, list):
        results = [res for item in obj if (res := extract_text_frontend(item, level + 1)) and isinstance(res, str)]
        if results:
            return "\n".join(results)

    return "" # Retorna vazio se nenhum texto for encontrado


# Chamada assíncrona para o MCP
async def call_agent(question: str, user_id: str):
    """Chama o 'assistente_financeiro_inteligente' tool no servidor MCP."""
    client = Client("http://127.0.0.1:8005/sse")
    async with client:
        result = await client.call_tool(
            "assistente_financeiro_inteligente", {"question": question, "user_id": user_id}
        )
        return result


# Lógica do chat
if prompt := st.chat_input("Digite sua pergunta aqui..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🤖 Processando..."):
            try:
                response = asyncio.run(call_agent(prompt, st.session_state.user_id))
                clean_response = extract_text_frontend(response)
                
                if not clean_response:
                    # Fallback para exibir o JSON se nenhum texto claro for extraído
                    # Converte CallToolResult para dict antes de serializar
                    if hasattr(response, '__dict__'):
                        response_dict = response.__dict__
                    elif hasattr(response, 'model_dump'):
                        response_dict = response.model_dump()
                    else:
                        response_dict = str(response)
                    
                    try:
                        pretty_response = json.dumps(response_dict, indent=2, ensure_ascii=False, default=str)
                        clean_response = f"Não foi possível extrair uma resposta em texto. Resposta completa:\n```json\n{pretty_response}\n```"
                    except Exception as json_error:
                        clean_response = f"Não foi possível extrair uma resposta em texto. Resposta (formato string):\n```\n{str(response)}\n```"
                
                st.markdown(clean_response)
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                clean_response = f"❌ Erro ao processar: {e}\n\nTraceback:\n{tb}"
                st.markdown(clean_response)

    st.session_state.messages.append(
        {"role": "assistant", "content": clean_response}
    )

# Barra lateral com informações (da ideia do app.py)
with st.sidebar:
    st.header("ℹ️ Sobre o Assistente")
    st.markdown("""
    **O que posso fazer?**
    
    💰 **Transações Financeiras**
    - Registrar receitas e despesas
    - Categorizar gastos
    - Controlar contas bancárias
    
    📈 **Consultas de Ativos**
    - Ver preços de ações
    - Consultar cotações
    - Análises de mercado
    
    **Exemplos de perguntas:**
    - "Gastei 50 reais no mercado"
    - "Qual o preço da PETR4?"
    - "Recebi 1000 de salário"
    - "Como está o dólar?"
    """)
    
    st.header("🔧 Configuração")
    st.markdown("""
    Certifique-se de ter:
    1. O servidor do Super-Agent rodando.
    2. Dependências do projeto instaladas.
    3. Conexão com a internet.
    """)
    
    if st.button("🧹 Limpar Histórico"):
        st.session_state.messages = []
        # Nota: Isso limpa apenas o histórico da interface.
        # A memória do agente no servidor é mantida pelo user_id.
        st.rerun()
    
    st.header("👤 Informações")
    st.markdown(f"**ID do Usuário:** `{st.session_state.user_id[:8]}...`")

# Rodapé (da ideia do app.py)
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    💡 Dica: Seja específico nas suas perguntas para obter melhores respostas!
</div>
""", unsafe_allow_html=True)

