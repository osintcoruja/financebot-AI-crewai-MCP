from src.mcp_server import test_multi_analyst
from dotenv import load_dotenv
import asyncio
import os
import subprocess
import time
import sys
import threading

def start_mcp_server():
    # Inicia o servidor MCP em background e mostra o output em tempo real
    mcp_proc = subprocess.Popen(
        [sys.executable, "src/mcp_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    print("Servidor MCP iniciado em background. Logs do MCP:")
    def print_logs():
        if mcp_proc.stdout is not None:
            for line in mcp_proc.stdout:
                safe_line = line.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
                print(f"[MCP] {safe_line}", end="")
        else:
            print("[MCP] Nenhuma saída de log disponível (stdout=None)")
    t = threading.Thread(target=print_logs, daemon=True)
    t.start()
    # Aguarda alguns segundos para garantir que o servidor suba
    time.sleep(3)
    return mcp_proc

def stop_mcp_server(mcp_proc):
    if mcp_proc and mcp_proc.poll() is None:
        mcp_proc.terminate()
        try:
            mcp_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            mcp_proc.kill()
        print("Servidor MCP finalizado.")

async def main():
    load_dotenv()
    
    print("=== Teste do Servidor CrewAI MCP ===")
    print("Escolha como deseja interagir com o sistema:")
    print("1. Testar no terminal (modo texto)")
    print("2. Abrir interface web (Streamlit)")
    escolha = input("Digite 1 ou 2 e pressione Enter: ").strip()
    
    mcp_proc = start_mcp_server()
    try:
        if escolha == "2":
            print("\nAbrindo o Streamlit...")
            print("A interface web será aberta. O servidor MCP já está rodando.")
            subprocess.run(["streamlit", "run", "src/app.py"])
            return
        
        print("\n=== Teste Básico da Ferramenta ===")
        print("Exemplo de pergunta: Qual o preço atual da ação AAPL?")
        question = "Qual o preço atual da ação AAPL?"
        user_id = "usuario_teste"
        print(f"Pergunta: {question}")
        print("Processando resposta...\n")
        
        try:
            result = await test_multi_analyst(question, user_id)
            print(f"Resposta: {result}")
        except Exception as e:
            print(f"Erro: {str(e)}")
        
        print("\n=== Instruções de Configuração ===")
        print("1. Certifique-se de ter sua chave da OpenAI no arquivo .env:")
        print("   OPENAI_API_KEY=sua_chave_aqui")
        print("2. Instale as dependências: pip install -r requirements.txt")
        print("3. Rode: python src/mcp_server.py (em um terminal)")
        print("4. Rode: streamlit run src/app.py (em outro terminal)")
    finally:
        stop_mcp_server(mcp_proc)

if __name__ == "__main__":
    asyncio.run(main())
