# 📊 Sistema de Scoring Automático - Pesquisa de Preços

Sistema completo de análise e pontuação automatizada de documentos de pesquisa de preços para administração pública.

## 🎯 Características

- ✅ **Scoring automático** de 0 a 100 pontos
- 📊 **5 categorias de avaliação** com pesos diferenciados
- 🤖 **Integração com OpenAI** (GPT-4o/GPT-4 Turbo)
- 📄 **Relatórios HTML** profissionais e detalhados
- 🔄 **API REST** completa para integração
- ⚡ **Processamento assíncrono** em background
- 📱 **Pronto para frontend** React/Vue/Angular

## 📦 Instalação

### 1. Clone ou baixe os arquivos

```bash
# Estrutura de diretórios
mkdir -p projeto_scoring
cd projeto_scoring
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite com sua chave da OpenAI
nano .env
```

Adicione sua chave:
```
OPENAI_API_KEY=sk-sua-chave-aqui
```

## 🚀 Uso

### Opção 1: Uso Direto (Script Python)

```python
from sistema_scoring import AnalisadorPesquisaPrecos

# Inicializa
analisador = AnalisadorPesquisaPrecos(
    api_key="sua-chave-openai",
    modelo="gpt-4o"
)

# Processa PDF
resultado = analisador.processar_pdf_completo(
    caminho_pdf="documento.pdf",
    caminho_saida_json="resultado.json",
    caminho_saida_html="relatorio.html"
)

# Resultado
print(f"Pontuação: {resultado['pontuacao']['pontuacao_total']}/100")
print(f"Classificação: {resultado['pontuacao']['classificacao']}")
```

### Opção 2: API REST

#### Iniciar o servidor

```bash
uvicorn api_scoring:app --reload --host 0.0.0.0 --port 8000
```

#### Endpoints disponíveis

**1. Upload e análise**
```bash
curl -X POST "http://localhost:8000/api/v1/analisar" \
  -F "arquivo=@documento.pdf"
```

Resposta:
```json
{
  "id_analise": "uuid-aqui",
  "status": "em_processamento",
  "mensagem": "Análise iniciada com sucesso",
  "progresso": 10,
  "data_inicio": "2025-01-16T10:30:00"
}
```

**2. Consultar status**
```bash
curl "http://localhost:8000/api/v1/status/{id_analise}"
```

**3. Obter resultado JSON**
```bash
curl "http://localhost:8000/api/v1/resultado/{id_analise}/json" \
  -o resultado.json
```

**4. Obter relatório HTML**
```bash
curl "http://localhost:8000/api/v1/resultado/{id_analise}/html" \
  -o relatorio.html
```

**5. Obter resumo**
```bash
curl "http://localhost:8000/api/v1/resultado/{id_analise}/resumo"
```

Resposta:
```json
{
  "id_analise": "uuid",
  "pontuacao_total": 87.5,
  "classificacao": "CONFORMIDADE MÉDIA-ALTA",
  "nivel_risco": "Baixo-Médio",
  "aptidao": "APTO_COM_RESSALVAS",
  "data_analise": "2025-01-16T10:35:00"
}
```

## 📊 Sistema de Pontuação

### Categorias e Pesos

| Categoria | Peso | Pontos Máximos |
|-----------|------|----------------|
| **Estrutura Mínima** | 25% | 25 |
| **Condições Comerciais** | 20% | 20 |
| **Parâmetros de Pesquisa** | 20% | 20 |
| **Metodologia Estatística** | 20% | 20 |
| **Validade e Governança** | 15% | 15 |
| **TOTAL** | 100% | **100** |

### Classificações

| Pontuação | Classificação | Nível de Risco |
|-----------|---------------|----------------|
| 90-100 | CONFORMIDADE ALTA | Baixo |
| 75-89 | CONFORMIDADE MÉDIA-ALTA | Baixo-Médio |
| 60-74 | CONFORMIDADE MÉDIA | Médio |
| 40-59 | CONFORMIDADE BAIXA | Alto |
| 0-39 | NÃO CONFORMIDADE | Crítico |

### Aptidão do Documento

- **APTO**: Documento pode subsidiar a contratação sem ressalvas
- **APTO COM RESSALVAS**: Necessita complementações menores
- **INAPTO**: Não está apto para uso, requer saneamento

## 📋 Estrutura do JSON de Resultado

```json
{
  "metadata": {
    "data_analise": "2025-01-16T10:35:00",
    "versao_sistema": "1.0",
    "objeto_analisado": "descrição"
  },
  "pontuacao": {
    "estrutura_minima": {
      "pontos_obtidos": 22,
      "pontos_maximos": 25,
      "percentual": 88,
      "itens": [...]
    },
    "pontuacao_total": 87.5,
    "classificacao": "CONFORMIDADE MÉDIA-ALTA",
    "nivel_risco": "Baixo-Médio"
  },
  "analise_qualitativa": {
    "pontos_fortes": [],
    "pontos_fracos": [],
    "riscos_criticos": []
  },
  "recomendacoes": {
    "imediatas": [],
    "complementacoes": [],
    "melhorias": []
  },
  "conclusao": {
    "aptidao": "APTO_COM_RESSALVAS",
    "justificativa": "...",
    "impacto_controle_externo": "medio"
  }
}
```

## 🎨 Integração Frontend

### Exemplo React

```jsx
import { useState } from 'react';

function AnalisePesquisaPrecos() {
  const [idAnalise, setIdAnalise] = useState(null);
  const [status, setStatus] = useState(null);

  const uploadArquivo = async (arquivo) => {
    const formData = new FormData();
    formData.append('arquivo', arquivo);

    const response = await fetch('http://localhost:8000/api/v1/analisar', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    setIdAnalise(data.id_analise);
    
    // Polling de status
    verificarStatus(data.id_analise);
  };

  const verificarStatus = async (id) => {
    const interval = setInterval(async () => {
      const response = await fetch(`http://localhost:8000/api/v1/status/${id}`);
      const data = await response.json();
      
      setStatus(data);

      if (data.status === 'concluido' || data.status === 'erro') {
        clearInterval(interval);
      }
    }, 3000);
  };

  return (
    <div>
      <input 
        type="file" 
        accept=".pdf" 
        onChange={(e) => uploadArquivo(e.target.files[0])} 
      />
      
      {status && (
        <div>
          <p>Status: {status.status}</p>
          <p>Progresso: {status.progresso}%</p>
          
          {status.status === 'concluido' && (
            <a href={`http://localhost:8000/api/v1/resultado/${idAnalise}/html`}>
              Ver Relatório
            </a>
          )}
        </div>
      )}
    </div>
  );
}
```

## 🔧 Customização

### Ajustar Pesos das Categorias

Edite em `sistema_scoring.py`:

```python
PESOS_CATEGORIAS = {
    "estrutura_minima": 30,  # Aumentar importância
    "condicoes_comerciais": 15,  # Diminuir importância
    # ...
}
```

### Modificar Critérios de Classificação

```python
def _classificar_pontuacao(self, pontuacao: float) -> str:
    if pontuacao >= 95:  # Mais rigoroso
        return Classificacao.ALTA.value
    # ...
```

### Personalizar Relatório HTML

Modifique o método `_construir_html_relatorio()` para adicionar:
- Logo da instituição
- Cores personalizadas
- Seções adicionais
- Gráficos específicos

## 🐛 Troubleshooting

### Erro: "OPENAI_API_KEY não configurada"

Solução:
```bash
export OPENAI_API_KEY=sua-chave-aqui
```

### PDF não sendo processado

Verifique:
- Arquivo é PDF válido
- Tamanho < 10MB
- PDF não está protegido por senha

### Timeout na análise

Aumente o timeout em `.env`:
```
AI_ANALYSIS_TIMEOUT=600
```

## 📝 Logs

Os logs são salvos em:
```
/home/claude/logs/sistema_scoring.log
```

Nível de log configurável em `.env`:
```
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## 🔒 Segurança

- ✅ Validação de tipo de arquivo
- ✅ Limite de tamanho
- ✅ Sanitização de nomes
- ✅ Processamento em diretório temporário
- ✅ Limpeza automática de arquivos

## 📈 Performance

- **Tempo médio**: 30-60 segundos por documento
- **PDFs pequenos** (<10 páginas): ~30s
- **PDFs médios** (10-30 páginas): ~45s
- **PDFs grandes** (>30 páginas): ~60s+

## 🤝 Contribuindo

Melhorias sugeridas:
- [ ] Suporte a múltiplos idiomas
- [ ] Integração com banco de dados
- [ ] Dashboard administrativo
- [ ] Exportação para Excel
- [ ] Comparação entre documentos
- [ ] Machine Learning para scoring automático

## 📄 Licença

Sistema desenvolvido para facilitar a gestão pública de licitações.

## 📞 Suporte

Para dúvidas ou problemas:
- Abra uma issue no repositório
- Entre em contato com o administrador do sistema

---

**Versão**: 1.0.0  
**Última atualização**: Janeiro 2025  
**Compatibilidade**: Python 3.9+
