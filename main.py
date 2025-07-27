from dotenv import load_dotenv
import subprocess
import sys
import time

def run_mcp_server():
    """Executa o servidor MCP usando uv run"""
    print("🚀 Iniciando servidor MCP...")
    print("=" * 50)
    
    try:
        # Executa o comando uv run para o mcp_server.py
        subprocess.run(["uv", "run", "src/mcp_server.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar servidor MCP: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Servidor MCP interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

def run_streamlit():
    """Executa o Streamlit"""
    print("\n🌐 Iniciando interface web Streamlit...")
    print("📱 A interface será aberta em: http://localhost:8501")
    print("=" * 50)
    
    try:
        # Executa o comando streamlit run para o app.py
        subprocess.run(["streamlit", "run", "src/app.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar Streamlit: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Streamlit interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

def main():
    load_dotenv()
    
    print("=== Assistente Financeiro Inteligente ===")
    print("Escolha como deseja executar:")
    print("1. Executar servidor MCP (uv run src/mcp_server.py)")
    print("2. Executar interface web (streamlit run src/app.py)")
    print("3. Executar ambos sequencialmente")
    
    escolha = input("Digite 1, 2 ou 3 e pressione Enter: ").strip()
    
    if escolha == "1":
        run_mcp_server()
    elif escolha == "2":
        run_streamlit()
    elif escolha == "3":
        print("⚠️  Para executar ambos, você precisará:")
        print("1. Primeiro execute: uv run src/mcp_server.py (em um terminal)")
        print("2. Depois execute: streamlit run src/app.py (em outro terminal)")
        print("\nOu use o comando direto:")
        print("uv run src/mcp_server.py")
    else:
        print("❌ Opção inválida")

if __name__ == "__main__":
    main()
