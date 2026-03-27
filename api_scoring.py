"""
API REST para Sistema de Scoring de Pesquisa de Preços
Framework: FastAPI
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import shutil
from datetime import datetime
from dotenv import load_dotenv

# CARREGAR .env ANTES DE TUDO
load_dotenv()

from sistema_scoring import AnalisadorPesquisaPrecos


# Modelos Pydantic
class StatusAnalise(BaseModel):
    id_analise: str
    status: str
    mensagem: str
    progresso: int
    data_inicio: str
    data_fim: Optional[str] = None


class ResultadoResumo(BaseModel):
    id_analise: str
    pontuacao_total: float
    classificacao: str
    nivel_risco: str
    aptidao: str
    data_analise: str


# Configuração da API
app = FastAPI(
    title="API Análise de Pesquisa de Preços",
    description="Sistema automatizado de scoring e conformidade para pesquisas de preços públicas",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurações de diretórios (compatível com Windows e Linux)
# Usa diretório atual se UPLOAD_DIR não estiver no .env
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
RESULTS_DIR = os.getenv("RESULTS_DIR", "./results")

# Cria diretórios se não existirem
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

print(f"📁 Diretórios configurados:")
print(f"   Uploads: {os.path.abspath(UPLOAD_DIR)}")
print(f"   Results: {os.path.abspath(RESULTS_DIR)}")

# Cache de status de análises
analises_em_andamento = {}

# Inicializa analisador
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY não configurada")

analisador = AnalisadorPesquisaPrecos(
    api_key=OPENAI_API_KEY,
    modelo="gpt-4o"
)


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "nome": "API Análise de Pesquisa de Preços",
        "versao": "1.0.0",
        "status": "online",
        "endpoints": {
            "upload": "/api/v1/analisar",
            "status": "/api/v1/status/{id_analise}",
            "resultado_json": "/api/v1/resultado/{id_analise}/json",
            "resultado_html": "/api/v1/resultado/{id_analise}/html"
        }
    }


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "openai_configurado": bool(OPENAI_API_KEY)
    }


@app.post("/api/v1/analisar", response_model=StatusAnalise)
async def analisar_documento(
    background_tasks: BackgroundTasks,
    arquivo: UploadFile = File(...),
):
    """
    Envia documento PDF para análise
    
    Args:
        arquivo: Arquivo PDF da pesquisa de preços
        
    Returns:
        StatusAnalise com ID da análise
    """
    # Valida extensão
    if not arquivo.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos")
    
    # Gera ID único
    id_analise = str(uuid.uuid4())
    
    # Salva arquivo temporário
    caminho_pdf = os.path.join(UPLOAD_DIR, f"{id_analise}.pdf")
    
    try:
        with open(caminho_pdf, "wb") as buffer:
            shutil.copyfileobj(arquivo.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")
    finally:
        arquivo.file.close()
    
    # Registra análise
    analises_em_andamento[id_analise] = {
        "status": "em_processamento",
        "mensagem": "Documento recebido, análise iniciada",
        "progresso": 10,
        "data_inicio": datetime.now().isoformat(),
        "arquivo_original": arquivo.filename
    }
    
    # Adiciona tarefa em background
    background_tasks.add_task(processar_analise, id_analise, caminho_pdf)
    
    return StatusAnalise(
        id_analise=id_analise,
        status="em_processamento",
        mensagem="Análise iniciada com sucesso",
        progresso=10,
        data_inicio=analises_em_andamento[id_analise]["data_inicio"]
    )


def processar_analise(id_analise: str, caminho_pdf: str):
    """
    Processa análise em background
    
    Args:
        id_analise: ID da análise
        caminho_pdf: Caminho do PDF
    """
    try:
        print(f"🔄 Iniciando análise: {id_analise}")
        print(f"📄 PDF: {caminho_pdf}")
        
        # Atualiza status
        analises_em_andamento[id_analise]["progresso"] = 30
        analises_em_andamento[id_analise]["mensagem"] = "Extraindo texto do PDF..."
        print("📝 Status: Extraindo PDF...")
        
        # Define caminhos de saída
        caminho_json = os.path.join(RESULTS_DIR, f"{id_analise}.json")
        caminho_html = os.path.join(RESULTS_DIR, f"{id_analise}.html")
        
        # Atualiza status
        analises_em_andamento[id_analise]["progresso"] = 50
        analises_em_andamento[id_analise]["mensagem"] = "Analisando com IA..."
        print("🤖 Status: Analisando com IA...")
        
        # Processa
        resultado = analisador.processar_pdf_completo(
            caminho_pdf=caminho_pdf,
            caminho_saida_json=caminho_json,
            caminho_saida_html=caminho_html
        )
        
        print(f"✅ Análise concluída! Pontuação: {resultado['pontuacao']['pontuacao_total']}")
        
        # Atualiza status - concluído
        analises_em_andamento[id_analise].update({
            "status": "concluido",
            "mensagem": "Análise concluída com sucesso",
            "progresso": 100,
            "data_fim": datetime.now().isoformat(),
            "resultado": {
                "pontuacao_total": resultado['pontuacao']['pontuacao_total'],
                "classificacao": resultado['pontuacao']['classificacao'],
                "nivel_risco": resultado['pontuacao']['nivel_risco'],
                "aptidao": resultado['conclusao']['aptidao']
            }
        })
        
        # Remove PDF temporário
        try:
            os.remove(caminho_pdf)
            print(f"🗑️  PDF temporário removido")
        except:
            pass
        
    except Exception as e:
        # Log detalhado do erro
        import traceback
        erro_completo = traceback.format_exc()
        print(f"❌ ERRO na análise {id_analise}:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {str(e)}")
        print(f"   Traceback completo:")
        print(erro_completo)
        
        # Atualiza status - erro
        analises_em_andamento[id_analise].update({
            "status": "erro",
            "mensagem": f"Erro na análise: {str(e)}",
            "progresso": 0,
            "data_fim": datetime.now().isoformat(),
            "erro_detalhado": erro_completo  # Para debug
        })


@app.get("/api/v1/status/{id_analise}", response_model=StatusAnalise)
async def consultar_status(id_analise: str):
    """
    Consulta status de uma análise
    
    Args:
        id_analise: ID da análise
        
    Returns:
        StatusAnalise com status atual
    """
    if id_analise not in analises_em_andamento:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    
    info = analises_em_andamento[id_analise]
    
    return StatusAnalise(
        id_analise=id_analise,
        status=info["status"],
        mensagem=info["mensagem"],
        progresso=info["progresso"],
        data_inicio=info["data_inicio"],
        data_fim=info.get("data_fim")
    )


@app.get("/api/v1/resultado/{id_analise}/json")
async def obter_resultado_json(id_analise: str):
    """
    Obtém resultado em JSON
    
    Args:
        id_analise: ID da análise
        
    Returns:
        JSON com resultado completo
    """
    caminho_json = os.path.join(RESULTS_DIR, f"{id_analise}.json")
    
    if not os.path.exists(caminho_json):
        raise HTTPException(status_code=404, detail="Resultado não encontrado")
    
    return FileResponse(
        caminho_json,
        media_type="application/json",
        filename=f"analise_{id_analise}.json"
    )


@app.get("/api/v1/resultado/{id_analise}/html")
async def obter_resultado_html(id_analise: str):
    """
    Obtém relatório em HTML
    
    Args:
        id_analise: ID da análise
        
    Returns:
        Arquivo HTML
    """
    caminho_html = os.path.join(RESULTS_DIR, f"{id_analise}.html")
    
    if not os.path.exists(caminho_html):
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    
    return FileResponse(
        caminho_html,
        media_type="text/html",
        filename=f"relatorio_{id_analise}.html"
    )


@app.get("/api/v1/resultado/{id_analise}/resumo", response_model=ResultadoResumo)
async def obter_resumo(id_analise: str):
    """
    Obtém resumo do resultado
    
    Args:
        id_analise: ID da análise
        
    Returns:
        Resumo com principais métricas
    """
    if id_analise not in analises_em_andamento:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    
    info = analises_em_andamento[id_analise]
    
    if info["status"] != "concluido":
        raise HTTPException(status_code=400, detail="Análise ainda não concluída")
    
    resultado = info["resultado"]
    
    return ResultadoResumo(
        id_analise=id_analise,
        pontuacao_total=resultado["pontuacao_total"],
        classificacao=resultado["classificacao"],
        nivel_risco=resultado["nivel_risco"],
        aptidao=resultado["aptidao"],
        data_analise=info["data_fim"]
    )


@app.delete("/api/v1/analise/{id_analise}")
async def deletar_analise(id_analise: str):
    """
    Deleta análise e arquivos relacionados
    
    Args:
        id_analise: ID da análise
        
    Returns:
        Confirmação de exclusão
    """
    if id_analise not in analises_em_andamento:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    
    # Remove arquivos
    arquivos = [
        os.path.join(RESULTS_DIR, f"{id_analise}.json"),
        os.path.join(RESULTS_DIR, f"{id_analise}.html")
    ]
    
    for arquivo in arquivos:
        if os.path.exists(arquivo):
            os.remove(arquivo)
    
    # Remove do cache
    del analises_em_andamento[id_analise]
    
    return {"mensagem": "Análise deletada com sucesso", "id_analise": id_analise}


@app.get("/api/v1/analises")
async def listar_analises():
    """
    Lista todas as análises
    
    Returns:
        Lista de análises com status
    """
    return {
        "total": len(analises_em_andamento),
        "analises": [
            {
                "id_analise": id_analise,
                "status": info["status"],
                "arquivo_original": info.get("arquivo_original"),
                "data_inicio": info["data_inicio"],
                "data_fim": info.get("data_fim")
            }
            for id_analise, info in analises_em_andamento.items()
        ]
    }


# Executar com: uvicorn api_scoring:app --reload --host 0.0.0.0 --port 8000