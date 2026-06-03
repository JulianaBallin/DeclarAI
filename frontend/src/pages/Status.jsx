import { useState, useEffect } from "react";
import { RefreshCw, CheckCircle, XCircle, Activity } from "lucide-react";
import { obterStatus } from "../services/api";

export default function Status() {
  const [status, setStatus] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState(null);

  async function carregar() {
    setCarregando(true);
    setErro(null);
    try {
      const dados = await obterStatus();
      setStatus(dados);
    } catch (err) {
      setErro(err.message);
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    carregar();
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Status do Sistema</h1>
        <button className="btn-secondary btn-sm" onClick={carregar}>
          <RefreshCw size={14} /> Atualizar
        </button>
      </div>

      {carregando && <p className="loading-text">Verificando status...</p>}
      {erro && <div className="alert alert-error">{erro}</div>}

      {status && (
        <div className="status-grid">
          <div className="status-card">
            <div className="status-card-header">
              <Activity size={20} />
              <h3>Pipeline RAG</h3>
            </div>
            <div className="status-item">
              {status.rag_inicializado ? (
                <CheckCircle size={16} className="icon-green" />
              ) : (
                <XCircle size={16} className="icon-red" />
              )}
              <span>RAG {status.rag_inicializado ? "inicializado" : "nao inicializado"}</span>
            </div>
            <div className="status-item">
              <span className="status-label">Modelo LLM:</span>
              <span className="status-value">{status.modelo_llm || "-"}</span>
            </div>
            <div className="status-item">
              <span className="status-label">Modelo Embedding:</span>
              <span className="status-value">{status.modelo_embedding || "-"}</span>
            </div>
          </div>

          <div className="status-card">
            <div className="status-card-header">
              <Activity size={20} />
              <h3>Base de Conhecimento</h3>
            </div>
            <div className="status-item">
              <span className="status-label">Chunks indexados:</span>
              <span className="status-value stat-highlight">{status.chunks_indexados ?? "-"}</span>
            </div>
            <div className="status-item">
              <span className="status-label">Documentos na base:</span>
              <span className="status-value">{status.documentos_base ?? "-"}</span>
            </div>
          </div>

          <div className="status-card">
            <div className="status-card-header">
              <Activity size={20} />
              <h3>Ollama</h3>
            </div>
            <div className="status-item">
              {status.ollama_disponivel ? (
                <CheckCircle size={16} className="icon-green" />
              ) : (
                <XCircle size={16} className="icon-red" />
              )}
              <span>Ollama {status.ollama_disponivel ? "disponivel" : "indisponivel"}</span>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <h2>Informacoes do Sistema</h2>
        <div className="info-list">
          <div className="info-row">
            <span>API URL</span>
            <code>{import.meta.env.VITE_API_URL || "http://localhost:8000"}</code>
          </div>
          <div className="info-row">
            <span>Documentacao da API</span>
            <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">
              /docs (Swagger UI)
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
