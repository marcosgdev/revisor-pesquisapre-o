/**
 * Componente React - Análise de Pesquisa de Preços
 * Sistema de Upload e Visualização de Scoring
 */

import React, { useState, useEffect } from 'react';
import './AnalisePesquisaPrecos.css';

const API_BASE_URL = 'http://localhost:8000';

const AnalisePesquisaPrecos = () => {
  const [arquivo, setArquivo] = useState(null);
  const [idAnalise, setIdAnalise] = useState(null);
  const [status, setStatus] = useState(null);
  const [resultado, setResultado] = useState(null);
  const [historico, setHistorico] = useState([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState(null);

  // Carrega histórico ao montar
  useEffect(() => {
    carregarHistorico();
  }, []);

  // Polling de status quando análise está em andamento
  useEffect(() => {
    if (idAnalise && status?.status === 'em_processamento') {
      const interval = setInterval(() => {
        verificarStatus(idAnalise);
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [idAnalise, status]);

  const carregarHistorico = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analises`);
      const data = await response.json();
      setHistorico(data.analises || []);
    } catch (error) {
      console.error('Erro ao carregar histórico:', error);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      setArquivo(file);
      setErro(null);
    } else {
      setErro('Por favor, selecione um arquivo PDF válido');
      setArquivo(null);
    }
  };

  const uploadArquivo = async () => {
    if (!arquivo) {
      setErro('Nenhum arquivo selecionado');
      return;
    }

    setLoading(true);
    setErro(null);

    const formData = new FormData();
    formData.append('arquivo', arquivo);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analisar`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Erro ao enviar arquivo');
      }

      const data = await response.json();
      setIdAnalise(data.id_analise);
      setStatus(data);
      setResultado(null);
    } catch (error) {
      setErro(`Erro: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const verificarStatus = async (id) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/status/${id}`);
      const data = await response.json();
      
      setStatus(data);

      if (data.status === 'concluido') {
        carregarResultado(id);
        carregarHistorico();
      } else if (data.status === 'erro') {
        setErro(data.mensagem);
      }
    } catch (error) {
      console.error('Erro ao verificar status:', error);
    }
  };

  const carregarResultado = async (id) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/resultado/${id}/resumo`);
      const data = await response.json();
      setResultado(data);
    } catch (error) {
      console.error('Erro ao carregar resultado:', error);
    }
  };

  const downloadJSON = () => {
    window.open(`${API_BASE_URL}/api/v1/resultado/${idAnalise}/json`, '_blank');
  };

  const abrirRelatorioHTML = () => {
    window.open(`${API_BASE_URL}/api/v1/resultado/${idAnalise}/html`, '_blank');
  };

  const resetar = () => {
    setArquivo(null);
    setIdAnalise(null);
    setStatus(null);
    setResultado(null);
    setErro(null);
    carregarHistorico();
  };

  const obterCorPontuacao = (pontuacao) => {
    if (pontuacao >= 90) return '#22c55e';
    if (pontuacao >= 75) return '#84cc16';
    if (pontuacao >= 60) return '#eab308';
    if (pontuacao >= 40) return '#f97316';
    return '#ef4444';
  };

  const formatarData = (dataISO) => {
    const data = new Date(dataISO);
    return data.toLocaleString('pt-BR');
  };

  return (
    <div className="container">
      <header className="header">
        <h1>📊 Análise de Pesquisa de Preços</h1>
        <p>Sistema automatizado de scoring e conformidade</p>
      </header>

      {/* Upload Section */}
      {!idAnalise && (
        <div className="upload-section">
          <div className="upload-area">
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              id="file-input"
              style={{ display: 'none' }}
            />
            <label htmlFor="file-input" className="upload-label">
              <div className="upload-icon">📄</div>
              <p>Clique para selecionar o PDF</p>
              {arquivo && <p className="file-name">📎 {arquivo.name}</p>}
            </label>
          </div>

          {erro && (
            <div className="alert alert-error">
              ⚠️ {erro}
            </div>
          )}

          <button
            onClick={uploadArquivo}
            disabled={!arquivo || loading}
            className="btn btn-primary"
          >
            {loading ? '⏳ Enviando...' : '🚀 Iniciar Análise'}
          </button>
        </div>
      )}

      {/* Progress Section */}
      {status && status.status === 'em_processamento' && (
        <div className="progress-section">
          <h2>⏳ Análise em Andamento</h2>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${status.progresso}%` }}
            >
              {status.progresso}%
            </div>
          </div>
          <p>{status.mensagem}</p>
        </div>
      )}

      {/* Results Section */}
      {resultado && status?.status === 'concluido' && (
        <div className="results-section">
          <h2>✅ Análise Concluída</h2>
          
          <div className="score-card">
            <div className="score-circle" style={{
              borderColor: obterCorPontuacao(resultado.pontuacao_total)
            }}>
              <div className="score-value" style={{
                color: obterCorPontuacao(resultado.pontuacao_total)
              }}>
                {resultado.pontuacao_total}
              </div>
              <div className="score-label">pontos</div>
            </div>
            
            <div className="score-details">
              <div className="detail-item">
                <span className="detail-label">Classificação:</span>
                <span className="detail-value">{resultado.classificacao}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Nível de Risco:</span>
                <span className="detail-value">{resultado.nivel_risco}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Aptidão:</span>
                <span className="detail-value badge" style={{
                  backgroundColor: resultado.aptidao === 'APTO' ? '#22c55e' :
                                  resultado.aptidao === 'APTO_COM_RESSALVAS' ? '#eab308' : '#ef4444'
                }}>
                  {resultado.aptidao.replace(/_/g, ' ')}
                </span>
              </div>
            </div>
          </div>

          <div className="actions">
            <button onClick={abrirRelatorioHTML} className="btn btn-secondary">
              📄 Ver Relatório Completo
            </button>
            <button onClick={downloadJSON} className="btn btn-secondary">
              💾 Baixar JSON
            </button>
            <button onClick={resetar} className="btn btn-outline">
              🔄 Nova Análise
            </button>
          </div>
        </div>
      )}

      {/* History Section */}
      {historico.length > 0 && (
        <div className="history-section">
          <h2>📋 Histórico de Análises</h2>
          <div className="history-list">
            {historico.map((item) => (
              <div key={item.id_analise} className="history-item">
                <div className="history-info">
                  <strong>{item.arquivo_original || 'Documento'}</strong>
                  <span className="history-date">
                    {formatarData(item.data_inicio)}
                  </span>
                </div>
                <span className={`badge badge-${item.status}`}>
                  {item.status === 'concluido' ? '✅' : 
                   item.status === 'em_processamento' ? '⏳' : '❌'}
                  {' '}{item.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalisePesquisaPrecos;
