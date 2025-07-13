import streamlit as st
import asyncio
from fastmcp import Client
import json
import pandas as pd
import uuid
import nest_asyncio

nest_asyncio.apply()

st.set_page_config(page_title="Super-Agent Chat", page_icon="🤖", layout="wide")
st.title("Super-Agent – AI Chat Interface")

# Unique user memory namespace
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display message history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def extract_text_frontend(obj):
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
                nested = extract_text_frontend(value)
                if nested:
                    return nested
        for v in obj.values():
            nested = extract_text_frontend(v)
            if nested:
                return nested
    # Se for lista, tenta extrair de cada item
    if isinstance(obj, list):
        for item in obj:
            nested = extract_text_frontend(item)
            if nested:
                return nested
    # Se for objeto com .text, .content, .data, etc.
    for attr in ["text", "content", "data", "raw"]:
        if hasattr(obj, attr):
            value = getattr(obj, attr)
            nested = extract_text_frontend(value)
            if nested:
                return nested
    return str(obj)


# Async call to MCP
async def call_agent(question: str, user_id: str):
    client = Client("http://127.0.0.1:8005/sse")
    async with client:
        result = await client.call_tool(
            "multi_analyst", {"question": question, "user_id": user_id}
        )
        return result  # NÃO use str(result) aqui!


# Chat input
if prompt := st.chat_input("Pergunte..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("O agente está pensando..."):
            try:
                response = asyncio.run(call_agent(prompt, st.session_state.user_id))
                clean_response = extract_text_frontend(response)
                st.markdown(clean_response)
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                response = f"Erro: {e}\n\nTraceback:\n{tb}"
                st.markdown(response)
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": clean_response,
        }
    )

