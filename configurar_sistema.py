"""
Script de Configuração Automática
Execute: python configurar_sistema.py
"""

import os
import sys

def verificar_python():
    """Verifica versão do Python"""
    versao = sys.version_info
    print(f"✅ Python {versao.major}.{versao.minor}.{versao.micro}")
    if versao.major < 3 or (versao.major == 3 and versao.minor < 9):
        print("⚠️  Recomendamos Python 3.9 ou superior")
    return True

def verificar_dependencias():
    """Verifica se dependências estão instaladas"""
    print("\n🔍 Verificando dependências...")
    
    modulos = [
        'openai', 'pdfplumber', 'PyPDF2', 'fastapi', 
        'uvicorn', 'pydantic', 'dotenv', 'pandas', 
        'numpy', 'requests'
    ]
    
    faltando = []
    
    for modulo in modulos:
        try:
            if modulo == 'dotenv':
                __import__('dotenv')
            elif modulo == 'PyPDF2':
                __import__('PyPDF2')
            else:
                __import__(modulo)
            print(f"  ✅ {modulo}")
        except ImportError:
            print(f"  ❌ {modulo} - NÃO INSTALADO")
            faltando.append(modulo)
    
    if faltando:
        print(f"\n❌ Faltam {len(faltando)} dependências")
        print("\n📦 Execute para instalar:")
        deps = ' '.join(faltando)
        if 'dotenv' in faltando:
            deps = deps.replace('dotenv', 'python-dotenv')
        print(f"   pip install {deps}")
        return False
    
    print("\n✅ Todas as dependências instaladas!")
    return True

def criar_env():
    """Cria arquivo .env interativamente"""
    print("\n🔑 Configuração da Chave OpenAI")
    print("="*60)
    
    if os.path.exists('.env'):
        print("\n⚠️  Arquivo .env já existe!")
        resp = input("Deseja recriar? (s/N): ").lower()
        if resp != 's':
            print("✅ Mantendo .env existente")
            return verificar_env_existente()
    
    print("\n📝 Você precisa de uma chave da OpenAI")
    print("   1. Acesse: https://platform.openai.com/api-keys")
    print("   2. Faça login ou crie conta")
    print("   3. Clique em 'Create new secret key'")
    print("   4. Copie a chave (começa com sk-)")
    print()
    
    chave = input("Cole sua chave OpenAI aqui: ").strip()
    
    if not chave:
        print("❌ Chave não pode estar vazia")
        return False
    
    if not chave.startswith('sk-'):
        print("⚠️  Aviso: Chave não começa com 'sk-'")
        resp = input("Continuar mesmo assim? (s/N): ").lower()
        if resp != 's':
            return False
    
    # Cria o arquivo .env
    conteudo_env = f"""# Configuração do Sistema de Scoring
# Gerado automaticamente em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# OpenAI API (OBRIGATÓRIO)
OPENAI_API_KEY={chave}
OPENAI_MODEL=gpt-4o

# Diretórios (opcional)
UPLOAD_DIR=./uploads
RESULTS_DIR=./results

# API Settings (opcional)
API_HOST=0.0.0.0
API_PORT=8000
"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(conteudo_env)
        print("\n✅ Arquivo .env criado com sucesso!")
        return True
    except Exception as e:
        print(f"\n❌ Erro ao criar .env: {e}")
        return False

def verificar_env_existente():
    """Verifica se .env existente tem a chave"""
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        if 'OPENAI_API_KEY=' in conteudo:
            # Extrai a chave
            for linha in conteudo.split('\n'):
                if linha.startswith('OPENAI_API_KEY='):
                    chave = linha.split('=', 1)[1].strip()
                    if chave and chave != 'sua-chave-aqui':
                        print(f"✅ Chave encontrada: {chave[:15]}...")
                        return True
        
        print("❌ .env existe mas não tem chave válida")
        return False
    except Exception as e:
        print(f"❌ Erro ao ler .env: {e}")
        return False

def testar_chave():
    """Testa se a chave funciona"""
    print("\n🔄 Testando chave OpenAI...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from openai import OpenAI
        
        chave = os.getenv('OPENAI_API_KEY')
        if not chave:
            print("❌ Chave não carregada do .env")
            return False
        
        client = OpenAI(api_key=chave)
        
        # Teste simples
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Responda: OK"}],
            max_tokens=5
        )
        
        print(f"✅ Conexão OK! Resposta: {response.choices[0].message.content}")
        print(f"   Tokens usados: {response.usage.total_tokens}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar: {str(e)}")
        
        if "invalid" in str(e).lower():
            print("\n💡 Chave inválida. Gere uma nova em:")
            print("   https://platform.openai.com/api-keys")
        elif "quota" in str(e).lower() or "billing" in str(e).lower():
            print("\n💡 Sem créditos. Adicione em:")
            print("   https://platform.openai.com/account/billing")
        
        return False

def criar_diretorios():
    """Cria diretórios necessários"""
    print("\n📁 Criando diretórios...")
    
    dirs = ['uploads', 'results', 'logs']
    
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"  ✅ {d}/")
        else:
            print(f"  ↪️  {d}/ (já existe)")
    
    return True

def mostrar_proximo_passo():
    """Mostra o que fazer agora"""
    print("\n" + "="*60)
    print("🎉 CONFIGURAÇÃO COMPLETA!")
    print("="*60)
    
    print("\n🚀 PRÓXIMOS PASSOS:")
    print("\n1. Testar o sistema:")
    print("   python teste_sistema.py")
    
    print("\n2. Iniciar a API:")
    print("   uvicorn api_scoring:app --reload --port 8000")
    
    print("\n3. Analisar um PDF:")
    print("   python sistema_scoring.py seu_documento.pdf")
    
    print("\n📚 DOCUMENTAÇÃO:")
    print("   - GUIA_RAPIDO.md (início rápido)")
    print("   - TUTORIAL_COMPLETO.md (guia detalhado)")
    print("   - README.md (documentação técnica)")
    
    print("\n💡 DICAS:")
    print("   - Use gpt-4o-mini para economizar")
    print("   - Cada análise custa ~$0.01 a $0.05")
    print("   - Mantenha o .env seguro")
    
    print("\n✅ Sistema pronto para usar!")

def main():
    """Função principal"""
    print("\n" + "🔧"*30)
    print("\n   CONFIGURADOR AUTOMÁTICO")
    print("   Sistema de Scoring de Pesquisa de Preços")
    print("\n" + "🔧"*30)
    
    # 1. Verificar Python
    print("\n1️⃣  Verificando Python...")
    if not verificar_python():
        return
    
    # 2. Verificar dependências
    print("\n2️⃣  Verificando dependências...")
    if not verificar_dependencias():
        print("\n⚠️  Instale as dependências primeiro")
        print("   pip install openai pdfplumber PyPDF2 fastapi uvicorn python-multipart pydantic python-dotenv pandas numpy requests")
        return
    
    # 3. Criar .env
    print("\n3️⃣  Configurando .env...")
    if not criar_env():
        print("\n❌ Configure o .env manualmente:")
        print("   1. Crie arquivo .env")
        print("   2. Adicione: OPENAI_API_KEY=sua-chave")
        return
    
    # 4. Testar chave
    print("\n4️⃣  Testando conexão...")
    input("⏸️  Pressione ENTER para testar (usará ~5 tokens)...")
    if not testar_chave():
        print("\n⚠️  Corrija a chave antes de continuar")
        return
    
    # 5. Criar diretórios
    print("\n5️⃣  Criando estrutura...")
    criar_diretorios()
    
    # 6. Próximos passos
    mostrar_proximo_passo()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Configuração cancelada")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
