"""
Sistema de Scoring Automático para Pesquisa de Preços
Integração com OpenAI API
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import openai
from pdfplumber import open as pdf_open


class NivelRisco(Enum):
    BAIXO = "Baixo"
    BAIXO_MEDIO = "Baixo-Médio"
    MEDIO = "Médio"
    ALTO = "Alto"
    CRITICO = "Crítico"


class Classificacao(Enum):
    ALTA = "CONFORMIDADE ALTA"
    MEDIA_ALTA = "CONFORMIDADE MÉDIA-ALTA"
    MEDIA = "CONFORMIDADE MÉDIA"
    BAIXA = "CONFORMIDADE BAIXA"
    NAO_CONFORMIDADE = "NÃO CONFORMIDADE"


class Aptidao(Enum):
    APTO = "APTO"
    APTO_COM_RESSALVAS = "APTO_COM_RESSALVAS"
    INAPTO = "INAPTO"


@dataclass
class PontuacaoCategoria:
    """Estrutura de pontuação por categoria"""
    pontos_obtidos: float
    pontos_maximos: float
    percentual: float
    itens: List[Dict]


@dataclass
class ResultadoAnalise:
    """Resultado completo da análise"""
    metadata: Dict
    pontuacao: Dict
    analise_qualitativa: Dict
    recomendacoes: Dict
    conclusao: Dict


class AnalisadorPesquisaPrecos:
    """Classe principal para análise de pesquisa de preços"""
    
    PESOS_CATEGORIAS = {
        "estrutura_minima": 25,
        "condicoes_comerciais": 20,
        "parametros_pesquisa": 20,
        "metodologia_estatistica": 20,
        "validade_governanca": 15
    }
    
    def __init__(self, api_key: str, modelo: str = "gpt-4o"):
        """
        Inicializa o analisador
        
        Args:
            api_key: Chave da API OpenAI
            modelo: Modelo a ser usado (gpt-4o, gpt-4-turbo, etc)
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.modelo = modelo
        self.meta_prompt = self._carregar_meta_prompt()
    
    def _carregar_meta_prompt(self) -> str:
        """Carrega o meta-prompt do arquivo"""
        try:
            with open('/home/claude/meta_prompt_scoring.md', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback: meta-prompt inline
            return self._meta_prompt_fallback()
    
    def _meta_prompt_fallback(self) -> str:
        """Meta-prompt inline caso arquivo não exista"""
        return """
        Você é uma IA especialista em análise de Pesquisa de Preços.
        Analise o documento e retorne um JSON estruturado com scoring de conformidade.
        Use o formato especificado com pontuações de 0-100.
        """
    
    def extrair_texto_pdf(self, caminho_pdf: str) -> str:
        """
        Extrai texto de um PDF
        
        Args:
            caminho_pdf: Caminho do arquivo PDF
            
        Returns:
            Texto extraído do PDF
        """
        texto_completo = []
        
        try:
            with pdf_open(caminho_pdf) as pdf:
                for pagina in pdf.pages:
                    texto = pagina.extract_text()
                    if texto:
                        texto_completo.append(f"--- PÁGINA {pagina.page_number} ---\n{texto}")
            
            return "\n\n".join(texto_completo)
        
        except Exception as e:
            raise Exception(f"Erro ao extrair PDF: {str(e)}")
    
    def analisar_documento(self, texto_documento: str) -> ResultadoAnalise:
        """
        Analisa o documento e retorna scoring
        
        Args:
            texto_documento: Texto extraído do documento
            
        Returns:
            ResultadoAnalise com pontuação e recomendações
        """
        try:
            # Monta o prompt para a API
            prompt_usuario = f"""
            Analise o seguinte documento de Pesquisa de Preços e retorne a avaliação completa em JSON:

            DOCUMENTO:
            {texto_documento[:15000]}  # Limita para evitar exceder tokens
            
            Retorne APENAS o JSON, sem texto adicional antes ou depois.
            """
            
            # Chama a API OpenAI
            response = self.client.chat.completions.create(
                model=self.modelo,
                messages=[
                    {"role": "system", "content": self.meta_prompt},
                    {"role": "user", "content": prompt_usuario}
                ],
                temperature=0.1,  # Baixa temperatura para consistência
                response_format={"type": "json_object"}  # Força resposta JSON
            )
            
            # Extrai e valida o JSON
            resultado_json = json.loads(response.choices[0].message.content)
            
            # Valida estrutura
            resultado_validado = self._validar_resultado(resultado_json)
            
            return resultado_validado
            
        except json.JSONDecodeError as e:
            raise Exception(f"Erro ao decodificar JSON da resposta: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro na análise: {str(e)}")
    
    def _validar_resultado(self, resultado: Dict) -> Dict:
        """
        Valida a estrutura do resultado
        
        Args:
            resultado: Dicionário com resultado da análise
            
        Returns:
            Resultado validado
        """
        # Adiciona metadata se estiver faltando
        if 'metadata' not in resultado:
            resultado['metadata'] = {
                'data_analise': datetime.now().isoformat(),
                'versao_sistema': '1.0',
                'objeto_analisado': 'Documento analisado'
            }
        
        # Campos obrigatórios (exceto metadata que já foi corrigido)
        campos_obrigatorios = ['pontuacao', 'analise_qualitativa', 
                               'recomendacoes', 'conclusao']
        
        for campo in campos_obrigatorios:
            if campo not in resultado:
                raise ValueError(f"Campo obrigatório ausente: {campo}")
        
        # Valida pontuação total
        if 'pontuacao_total' not in resultado['pontuacao']:
            resultado['pontuacao']['pontuacao_total'] = self._calcular_pontuacao_total(resultado)
        
        # Adiciona classificação se ausente
        if 'classificacao' not in resultado['pontuacao']:
            resultado['pontuacao']['classificacao'] = self._classificar_pontuacao(
                resultado['pontuacao']['pontuacao_total']
            )
        
        return resultado
    
    def _calcular_pontuacao_total(self, resultado: Dict) -> float:
        """Calcula pontuação total ponderada"""
        total = 0
        for categoria, peso in self.PESOS_CATEGORIAS.items():
            if categoria in resultado['pontuacao']:
                percentual = resultado['pontuacao'][categoria].get('percentual', 0)
                total += (percentual * peso / 100)
        return round(total, 2)
    
    def _classificar_pontuacao(self, pontuacao: float) -> str:
        """Retorna classificação baseada na pontuação"""
        if pontuacao >= 90:
            return Classificacao.ALTA.value
        elif pontuacao >= 75:
            return Classificacao.MEDIA_ALTA.value
        elif pontuacao >= 60:
            return Classificacao.MEDIA.value
        elif pontuacao >= 40:
            return Classificacao.BAIXA.value
        else:
            return Classificacao.NAO_CONFORMIDADE.value
    
    def gerar_relatorio_html(self, resultado: Dict, caminho_saida: str):
        """
        Gera relatório HTML formatado
        
        Args:
            resultado: Resultado da análise
            caminho_saida: Caminho para salvar o HTML
        """
        html = self._construir_html_relatorio(resultado)
        
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def _construir_html_relatorio(self, resultado: Dict) -> str:
        """Constrói HTML do relatório"""
        pontuacao_total = resultado['pontuacao']['pontuacao_total']
        classificacao = resultado['pontuacao']['classificacao']
        
        # Determina cor baseada na classificação
        cores = {
            'CONFORMIDADE ALTA': '#22c55e',
            'CONFORMIDADE MÉDIA-ALTA': '#84cc16',
            'CONFORMIDADE MÉDIA': '#eab308',
            'CONFORMIDADE BAIXA': '#f97316',
            'NÃO CONFORMIDADE': '#ef4444'
        }
        cor = cores.get(classificacao, '#6b7280')
        
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Relatório de Análise - Pesquisa de Preços</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #1f2937;
                    background: #f9fafb;
                    padding: 2rem;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 2rem;
                    text-align: center;
                }}
                .header h1 {{
                    font-size: 2rem;
                    margin-bottom: 0.5rem;
                }}
                .score-box {{
                    background: white;
                    margin: 2rem;
                    padding: 2rem;
                    border-radius: 8px;
                    text-align: center;
                    border: 3px solid {cor};
                }}
                .score-value {{
                    font-size: 4rem;
                    font-weight: bold;
                    color: {cor};
                }}
                .score-label {{
                    font-size: 1.5rem;
                    color: #6b7280;
                    margin-top: 0.5rem;
                }}
                .classification {{
                    display: inline-block;
                    background: {cor};
                    color: white;
                    padding: 0.5rem 1.5rem;
                    border-radius: 20px;
                    font-weight: bold;
                    margin-top: 1rem;
                }}
                .section {{
                    padding: 2rem;
                    border-bottom: 1px solid #e5e7eb;
                }}
                .section:last-child {{
                    border-bottom: none;
                }}
                .section h2 {{
                    color: #667eea;
                    margin-bottom: 1rem;
                    font-size: 1.5rem;
                }}
                .categoria {{
                    background: #f3f4f6;
                    padding: 1.5rem;
                    margin: 1rem 0;
                    border-radius: 8px;
                    border-left: 4px solid #667eea;
                }}
                .categoria h3 {{
                    color: #374151;
                    margin-bottom: 1rem;
                }}
                .progress-bar {{
                    background: #e5e7eb;
                    height: 24px;
                    border-radius: 12px;
                    overflow: hidden;
                    margin: 0.5rem 0;
                }}
                .progress-fill {{
                    height: 100%;
                    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 0.875rem;
                }}
                .item {{
                    background: white;
                    padding: 1rem;
                    margin: 0.5rem 0;
                    border-radius: 6px;
                    border-left: 3px solid #d1d5db;
                }}
                .item.conforme {{ border-left-color: #22c55e; }}
                .item.parcial {{ border-left-color: #eab308; }}
                .item.nao-conforme {{ border-left-color: #ef4444; }}
                .badge {{
                    display: inline-block;
                    padding: 0.25rem 0.75rem;
                    border-radius: 12px;
                    font-size: 0.875rem;
                    font-weight: 600;
                }}
                .badge.conforme {{ background: #dcfce7; color: #16a34a; }}
                .badge.parcial {{ background: #fef3c7; color: #ca8a04; }}
                .badge.nao-conforme {{ background: #fee2e2; color: #dc2626; }}
                .recomendacao {{
                    background: #fef3c7;
                    border-left: 4px solid #eab308;
                    padding: 1rem;
                    margin: 0.5rem 0;
                    border-radius: 6px;
                }}
                .recomendacao.critica {{
                    background: #fee2e2;
                    border-left-color: #dc2626;
                }}
                .conclusao {{
                    background: #f3f4f6;
                    padding: 1.5rem;
                    border-radius: 8px;
                    margin-top: 1rem;
                }}
                ul {{
                    list-style-position: inside;
                    margin: 0.5rem 0;
                }}
                li {{
                    margin: 0.5rem 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Relatório de Análise</h1>
                    <p>Pesquisa de Preços - Administração Pública</p>
                    <p style="font-size: 0.9rem; margin-top: 1rem;">
                        Gerado em: {resultado['metadata'].get('data_analise', 'N/A')}
                    </p>
                </div>
                
                <div class="score-box">
                    <div class="score-value">{pontuacao_total}</div>
                    <div class="score-label">Pontuação Total</div>
                    <div class="classification">{classificacao}</div>
                    <p style="margin-top: 1rem; color: #6b7280;">
                        Nível de Risco: <strong>{resultado['pontuacao'].get('nivel_risco', 'N/A')}</strong>
                    </p>
                </div>
                
                <div class="section">
                    <h2>📋 Pontuação por Categoria</h2>
                    {self._gerar_html_categorias(resultado['pontuacao'])}
                </div>
                
                <div class="section">
                    <h2>💡 Análise Qualitativa</h2>
                    {self._gerar_html_analise_qualitativa(resultado['analise_qualitativa'])}
                </div>
                
                <div class="section">
                    <h2>🎯 Recomendações</h2>
                    {self._gerar_html_recomendacoes(resultado['recomendacoes'])}
                </div>
                
                <div class="section">
                    <h2>✅ Conclusão</h2>
                    {self._gerar_html_conclusao(resultado['conclusao'])}
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _gerar_html_categorias(self, pontuacao: Dict) -> str:
        """Gera HTML das categorias"""
        html_cats = []
        
        categorias_nomes = {
            'estrutura_minima': 'Estrutura Mínima',
            'condicoes_comerciais': 'Condições Comerciais',
            'parametros_pesquisa': 'Parâmetros de Pesquisa',
            'metodologia_estatistica': 'Metodologia Estatística',
            'validade_governanca': 'Validade e Governança'
        }
        
        for cat_key, cat_nome in categorias_nomes.items():
            if cat_key in pontuacao:
                cat = pontuacao[cat_key]
                percentual = cat.get('percentual', 0)
                pontos = cat.get('pontos_obtidos', 0)
                maximos = cat.get('pontos_maximos', 0)
                
                html_cats.append(f"""
                <div class="categoria">
                    <h3>{cat_nome}</h3>
                    <p><strong>{pontos:.1f}</strong> de {maximos} pontos</p>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {percentual}%">
                            {percentual:.1f}%
                        </div>
                    </div>
                    {self._gerar_html_itens_categoria(cat.get('itens', []))}
                </div>
                """)
        
        return "".join(html_cats)
    
    def _gerar_html_itens_categoria(self, itens: List[Dict]) -> str:
        """Gera HTML dos itens de uma categoria"""
        if not itens:
            return ""
        
        html_itens = []
        for item in itens:
            status = item.get('status', 'nao_conforme')
            status_class = status.replace('_', '-')
            
            status_labels = {
                'conforme': 'Conforme',
                'parcial': 'Parcial',
                'nao_conforme': 'Não Conforme'
            }
            
            html_itens.append(f"""
            <div class="item {status_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>{item.get('criterio', 'N/A').replace('_', ' ').title()}</strong>
                    <span class="badge {status_class}">
                        {status_labels.get(status, status)} - {item.get('pontos', 0)}/{item.get('max', 0)}
                    </span>
                </div>
                <p style="margin-top: 0.5rem; color: #6b7280; font-size: 0.9rem;">
                    {item.get('observacao', 'Sem observações')}
                </p>
            </div>
            """)
        
        return "".join(html_itens)
    
    def _gerar_html_analise_qualitativa(self, analise: Dict) -> str:
        """Gera HTML da análise qualitativa"""
        html = []
        
        if analise.get('pontos_fortes'):
            html.append("<h3>✅ Pontos Fortes</h3><ul>")
            for ponto in analise['pontos_fortes']:
                html.append(f"<li>{ponto}</li>")
            html.append("</ul>")
        
        if analise.get('pontos_fracos'):
            html.append("<h3>⚠️ Pontos Fracos</h3><ul>")
            for ponto in analise['pontos_fracos']:
                html.append(f"<li>{ponto}</li>")
            html.append("</ul>")
        
        if analise.get('riscos_criticos'):
            html.append("<h3>🚨 Riscos Críticos</h3><ul>")
            for risco in analise['riscos_criticos']:
                html.append(f"<li style='color: #dc2626; font-weight: 600;'>{risco}</li>")
            html.append("</ul>")
        
        if analise.get('observacoes_gerais'):
            html.append(f"<p style='margin-top: 1rem;'><strong>Observações Gerais:</strong> {analise['observacoes_gerais']}</p>")
        
        return "".join(html)
    
    def _gerar_html_recomendacoes(self, recomendacoes: Dict) -> str:
        """Gera HTML das recomendações"""
        html = []
        
        if recomendacoes.get('imediatas'):
            html.append("<h3>🔴 Ações Imediatas</h3>")
            for rec in recomendacoes['imediatas']:
                html.append(f'<div class="recomendacao critica">{rec}</div>')
        
        if recomendacoes.get('complementacoes'):
            html.append("<h3>🟡 Complementações Necessárias</h3>")
            for rec in recomendacoes['complementacoes']:
                html.append(f'<div class="recomendacao">{rec}</div>')
        
        if recomendacoes.get('melhorias'):
            html.append("<h3>🔵 Sugestões de Melhoria</h3>")
            for rec in recomendacoes['melhorias']:
                html.append(f'<div class="recomendacao" style="background: #dbeafe; border-left-color: #3b82f6;">{rec}</div>')
        
        return "".join(html)
    
    def _gerar_html_conclusao(self, conclusao: Dict) -> str:
        """Gera HTML da conclusão"""
        aptidao = conclusao.get('aptidao', 'N/A')
        
        cores_aptidao = {
            'APTO': '#22c55e',
            'APTO_COM_RESSALVAS': '#eab308',
            'INAPTO': '#ef4444'
        }
        
        cor = cores_aptidao.get(aptidao, '#6b7280')
        
        return f"""
        <div class="conclusao">
            <div style="text-align: center; margin-bottom: 1rem;">
                <span style="display: inline-block; background: {cor}; color: white; 
                             padding: 0.5rem 2rem; border-radius: 20px; font-size: 1.2rem; font-weight: bold;">
                    {aptidao.replace('_', ' ')}
                </span>
            </div>
            <p><strong>Justificativa:</strong> {conclusao.get('justificativa', 'N/A')}</p>
            <p style="margin-top: 1rem;">
                <strong>Impacto no Controle Externo:</strong> 
                <span style="text-transform: uppercase; font-weight: 600;">
                    {conclusao.get('impacto_controle_externo', 'N/A')}
                </span>
            </p>
        </div>
        """
    
    def processar_pdf_completo(self, caminho_pdf: str, caminho_saida_json: str, 
                                caminho_saida_html: str) -> Dict:
        """
        Processa PDF completo e gera relatórios
        
        Args:
            caminho_pdf: Caminho do PDF de entrada
            caminho_saida_json: Caminho para salvar JSON
            caminho_saida_html: Caminho para salvar HTML
            
        Returns:
            Dicionário com resultado da análise
        """
        print("🔄 Extraindo texto do PDF...")
        texto = self.extrair_texto_pdf(caminho_pdf)
        
        print("🤖 Analisando documento com IA...")
        resultado = self.analisar_documento(texto)
        
        print("💾 Salvando resultado JSON...")
        with open(caminho_saida_json, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        
        print("📄 Gerando relatório HTML...")
        self.gerar_relatorio_html(resultado, caminho_saida_html)
        
        print(f"✅ Análise concluída!")
        print(f"   Pontuação: {resultado['pontuacao']['pontuacao_total']}/100")
        print(f"   Classificação: {resultado['pontuacao']['classificacao']}")
        print(f"   Aptidão: {resultado['conclusao']['aptidao']}")
        
        return resultado


# Exemplo de uso
if __name__ == "__main__":
    # Configuração
    API_KEY = os.getenv("OPENAI_API_KEY", "sua-chave-aqui")
    
    # Inicializa analisador
    analisador = AnalisadorPesquisaPrecos(
        api_key=API_KEY,
        modelo="gpt-4o"  # ou "gpt-4-turbo"
    )
    
    # Processa documento
    try:
        resultado = analisador.processar_pdf_completo(
            caminho_pdf="/mnt/user-data/uploads/pesquisa_precos.pdf",
            caminho_saida_json="/home/claude/resultado_analise.json",
            caminho_saida_html="/home/claude/relatorio_analise.html"
        )
        
        print("\n" + "="*50)
        print("RESUMO DA ANÁLISE")
        print("="*50)
        print(f"Pontuação Total: {resultado['pontuacao']['pontuacao_total']}/100")
        print(f"Classificação: {resultado['pontuacao']['classificacao']}")
        print(f"Nível de Risco: {resultado['pontuacao']['nivel_risco']}")
        print(f"Aptidão: {resultado['conclusao']['aptidao']}")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
