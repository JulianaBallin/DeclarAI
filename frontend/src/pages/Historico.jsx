import { useState, useEffect } from "react";
import {
  Building2,
  FileText,
  GraduationCap,
  HeartHandshake,
  Home,
  Landmark,
  PiggyBank,
  RefreshCw,
  Stethoscope,
  Trash2,
} from "lucide-react";
import { listarHistorico, excluirDocumento, obterResumoAnual } from "../services/api";

const CATEGORIAS_ICONES = [
  ["Recibo Médico", Stethoscope],
  ["Comprovante Educacional", GraduationCap],
  ["Informe de Rendimentos", Building2],
  ["Nota Fiscal", FileText],
  ["Previdência Privada", PiggyBank],
  ["Doações", HeartHandshake],
  ["Pensão Alimentícia", Landmark],
  ["Aluguel", Home],
  ["Documento Não Classificado", FileText],
];

function normalizarCategoria(categoria) {
  return (categoria || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

const ICONES_CAT = Object.fromEntries(
  CATEGORIAS_ICONES.map(([categoria, Icone]) => [
    normalizarCategoria(categoria),
    Icone,
  ])
);

function IconeCategoria({ categoria }) {
  const Icone = ICONES_CAT[normalizarCategoria(categoria)] || FileText;
  return <Icone size={16} aria-hidden="true" />;
}

export default function Historico() {
  const [documentos, setDocumentos] = useState([]);
  const [carregando, setCarregando] = useState(false);
  const [filtroCategoria, setFiltroCategoria] = useState("");
  const [mensagem, setMensagem] = useState(null);
  const [resumo, setResumo] = useState(null);
  const [anoResumo, setAnoResumo] = useState(new Date().getFullYear());

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

  async function carregarResumo() {
    try {
      const dados = await obterResumoAnual(anoResumo);
      setResumo(dados);
    } catch (err) {
      setMensagem({ tipo: "error", texto: `Erro no resumo: ${err.message}` });
    }
  }

  useEffect(() => {
    carregar();
  }, [filtroCategoria]);

  useEffect(() => {
    carregarResumo();
  }, [anoResumo]);

  async function excluir(id, nome) {
    if (!confirm(`Excluir "${nome}"?`)) return;
    try {
      await excluirDocumento(id);
      setDocumentos((prev) => prev.filter((d) => d.id !== id));
      setMensagem({ tipo: "success", texto: `"${nome}" removido.` });
      carregarResumo();
    } catch (err) {
      setMensagem({ tipo: "error", texto: `Erro: ${err.message}` });
    }
  }

  const contagem = documentos.reduce((acc, d) => {
    const cat = d.categoria || "Documento Não Classificado";
    acc[cat] = (acc[cat] || 0) + 1;
    return acc;
  }, {});

  const categorias = Object.keys(contagem).sort();
  const categoriasResumo = Object.entries(resumo?.categorias || {});
  const moeda = new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  });

  return (
    <div className="page">
      <div className="page-header">
        <h1>Histórico de Documentos</h1>
        <button
          className="btn-secondary btn-sm"
          onClick={() => {
            carregar();
            carregarResumo();
          }}
        >
          <RefreshCw size={14} /> Atualizar
        </button>
      </div>

      {mensagem && (
        <div className={`alert alert-${mensagem.tipo}`}>
          {mensagem.texto}
          <button className="alert-close" onClick={() => setMensagem(null)} aria-label="Fechar alerta">
            x
          </button>
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
        <label className="ano-resumo">
          Ano do resumo
          <input
            type="number"
            min="2000"
            max="2100"
            value={anoResumo}
            onChange={(e) => setAnoResumo(Number(e.target.value))}
          />
        </label>
      </div>

      <div className="stats-cards">
        <div className="stat-card">
          <span className="stat-number">{documentos.length}</span>
          <span className="stat-label">Total de documentos</span>
        </div>
        {categorias.slice(0, 4).map((cat) => (
          <div key={cat} className="stat-card">
            <span className="stat-number">{contagem[cat]}</span>
            <span className="stat-label stat-label-icon">
              <IconeCategoria categoria={cat} /> {cat}
            </span>
          </div>
        ))}
      </div>

      {resumo && (
        <div className="card resumo-card">
          <div className="card-header">
            <h2>Resumo Anual {resumo.ano}</h2>
            <span className="badge-secondary">{resumo.total_documentos} documentos</span>
          </div>
          <div className="resumo-totais">
            <div>
              <span className="stat-label">Deduções estimadas</span>
              <strong>{moeda.format(resumo.total_deducoes_estimado || 0)}</strong>
            </div>
            <div>
              <span className="stat-label">Economia estimada</span>
              <strong>{moeda.format(resumo.economia_estimada || 0)}</strong>
            </div>
          </div>
          {resumo.aviso_estimativa && (
            <p className="resumo-aviso">{resumo.aviso_estimativa}</p>
          )}
          {categoriasResumo.length > 0 && (
            <div className="resumo-categorias">
              {categoriasResumo.map(([categoria, dadosCategoria]) => (
                <div key={categoria} className="resumo-categoria">
                  <span>{categoria}</span>
                  <strong>{moeda.format(dadosCategoria.total_numerico || 0)}</strong>
                  {dadosCategoria.alerta_limite && (
                    <small>{dadosCategoria.alerta_limite}</small>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {carregando && <p className="loading-text">Carregando...</p>}

      {!carregando && documentos.length === 0 && (
        <div className="empty-state">
          <p>Nenhum documento encontrado. Envie documentos na aba Upload.</p>
        </div>
      )}

      {categorias.map((cat) => {
        const docs = documentos.filter(
          (d) => (d.categoria || "Documento Não Classificado") === cat
        );
        if (!docs.length) return null;
        return (
          <details key={cat} className="categoria-section" open>
            <summary className="categoria-header">
              <span className="categoria-title">
                <IconeCategoria categoria={cat} /> {cat}
              </span>
              <span className="categoria-count">{docs.length}</span>
            </summary>
            <div className="docs-list">
              {docs.map((doc) => (
                <div key={doc.id} className="doc-row">
                  <div className="doc-info">
                    <span className="doc-nome">
                      <FileText size={15} aria-hidden="true" /> {doc.nome_arquivo}
                    </span>
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
