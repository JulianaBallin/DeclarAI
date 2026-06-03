import { useState, useEffect } from "react";
import { Trash2, Download, RefreshCw } from "lucide-react";
import { listarHistorico, excluirDocumento } from "../services/api";

const ICONES_CAT = {
  "Recibo Medico": "🏥",
  "Comprovante Educacional": "🎓",
  "Informe de Rendimentos": "💼",
  "Nota Fiscal": "🧾",
  "Previdencia Privada": "🏦",
  "Doacoes": "❤️",
  "Pensao Alimenticia": "👨‍👧",
  "Aluguel": "🏠",
  "Documento Nao Classificado": "📄",
};

export default function Historico() {
  const [documentos, setDocumentos] = useState([]);
  const [carregando, setCarregando] = useState(false);
  const [filtroCategoria, setFiltroCategoria] = useState("");
  const [mensagem, setMensagem] = useState(null);

  async function carregar() {
    setCarregando(true);
    try {
      const params = { limite: 200 };
      if (filtroCategoria) params.categoria = filtroCategoria;
      const lista = await listarHistorico(params);
      setDocumentos(lista);
    } catch (err) {
      setMensagem({ tipo: "error", texto: `Erro: ${err.message}` });
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    carregar();
  }, [filtroCategoria]);

  async function excluir(id, nome) {
    if (!confirm(`Excluir "${nome}"?`)) return;
    try {
      await excluirDocumento(id);
      setDocumentos((prev) => prev.filter((d) => d.id !== id));
      setMensagem({ tipo: "success", texto: `"${nome}" removido.` });
    } catch (err) {
      setMensagem({ tipo: "error", texto: `Erro: ${err.message}` });
    }
  }

  const contagem = documentos.reduce((acc, d) => {
    const cat = d.categoria || "Documento Nao Classificado";
    acc[cat] = (acc[cat] || 0) + 1;
    return acc;
  }, {});

  const categorias = Object.keys(contagem).sort();

  return (
    <div className="page">
      <div className="page-header">
        <h1>Historico de Documentos</h1>
        <button className="btn-secondary btn-sm" onClick={carregar}>
          <RefreshCw size={14} /> Atualizar
        </button>
      </div>

      {mensagem && (
        <div className={`alert alert-${mensagem.tipo}`}>
          {mensagem.texto}
          <button className="alert-close" onClick={() => setMensagem(null)}>x</button>
        </div>
      )}

      <div className="filters">
        <select
          value={filtroCategoria}
          onChange={(e) => setFiltroCategoria(e.target.value)}
          className="filter-select"
        >
          <option value="">Todas as categorias</option>
          {categorias.map((cat) => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      <div className="stats-cards">
        <div className="stat-card">
          <span className="stat-number">{documentos.length}</span>
          <span className="stat-label">Total de Documentos</span>
        </div>
        {categorias.slice(0, 4).map((cat) => (
          <div key={cat} className="stat-card">
            <span className="stat-number">{contagem[cat]}</span>
            <span className="stat-label">{ICONES_CAT[cat] || "📁"} {cat}</span>
          </div>
        ))}
      </div>

      {carregando && <p className="loading-text">Carregando...</p>}

      {!carregando && documentos.length === 0 && (
        <div className="empty-state">
          <p>Nenhum documento encontrado. Envie documentos na aba Upload.</p>
        </div>
      )}

      {categorias.map((cat) => {
        const docs = documentos.filter(
          (d) => (d.categoria || "Documento Nao Classificado") === cat
        );
        if (!docs.length) return null;
        return (
          <details key={cat} className="categoria-section" open>
            <summary className="categoria-header">
              {ICONES_CAT[cat] || "📁"} {cat}
              <span className="categoria-count">{docs.length}</span>
            </summary>
            <div className="docs-list">
              {docs.map((doc) => (
                <div key={doc.id} className="doc-row">
                  <div className="doc-info">
                    <span className="doc-nome">📄 {doc.nome_arquivo}</span>
                    <div className="doc-meta">
                      <span>{doc.tipo_arquivo?.toUpperCase()}</span>
                      <span>{doc.data_detectada || "-"}</span>
                      <span>{doc.valor_detectado || "-"}</span>
                      <span>{doc.emitente_detectado || "-"}</span>
                      <span>Salvo: {(doc.criado_em || "").slice(0, 10)}</span>
                    </div>
                  </div>
                  <div className="doc-acoes">
                    <button
                      className="btn-danger btn-sm"
                      onClick={() => excluir(doc.id, doc.nome_arquivo)}
                    >
                      <Trash2 size={12} /> Excluir
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </details>
        );
      })}
    </div>
  );
}
