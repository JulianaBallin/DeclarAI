import { useState, useEffect } from "react";
import { BookOpen, Trash2, Upload, RefreshCw, CheckCircle, AlertCircle } from "lucide-react";
import { listarArquivosBase, uploadArquivoBase, removerArquivoBase } from "../services/api";

const ICONES = { pdf: "📕", txt: "📄", html: "🌐", htm: "🌐" };

export default function BaseConhecimento() {
  const [dados, setDados] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const [arquivo, setArquivo] = useState(null);
  const [enviando, setEnviando] = useState(false);
  const [mensagem, setMensagem] = useState(null);

  async function carregar() {
    setCarregando(true);
    try {
      const resultado = await listarArquivosBase();
      setDados(resultado);
    } catch (err) {
      setMensagem({ tipo: "error", texto: `Erro ao carregar: ${err.message}` });
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    carregar();
  }, []);

  async function enviar() {
    if (!arquivo) return;
    setEnviando(true);
    try {
      const resultado = await uploadArquivoBase(arquivo);
      setMensagem({
        tipo: "success",
        texto: `"${resultado.arquivo}" adicionado! Base re-indexada com ${resultado.chunks_indexados} trechos.`,
      });
      setArquivo(null);
      carregar();
    } catch (err) {
      setMensagem({ tipo: "error", texto: `Erro: ${err.message}` });
    } finally {
      setEnviando(false);
    }
  }

  async function remover(nome) {
    if (!confirm(`Remover "${nome}" da base de conhecimento?`)) return;
    try {
      await removerArquivoBase(nome);
      setMensagem({ tipo: "success", texto: `"${nome}" removido.` });
      carregar();
    } catch (err) {
      setMensagem({ tipo: "error", texto: `Erro: ${err.message}` });
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Base de Conhecimento</h1>
        <button className="btn-secondary btn-sm" onClick={carregar}>
          <RefreshCw size={14} /> Atualizar
        </button>
      </div>
      <p className="page-desc">
        Gerencie os documentos de referencia que o assistente usa para responder perguntas.
        Adicione PDFs, TXTs ou HTMLs com conteudo fiscal.
      </p>

      {mensagem && (
        <div className={`alert alert-${mensagem.tipo}`}>
          {mensagem.tipo === "success" ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          {mensagem.texto}
          <button className="alert-close" onClick={() => setMensagem(null)}>x</button>
        </div>
      )}

      <div className="card">
        <h2>Adicionar Documento</h2>
        <div className="upload-row">
          <input
            type="file"
            accept=".pdf,.txt,.html"
            onChange={(e) => setArquivo(e.target.files?.[0] || null)}
          />
          <button
            className="btn-primary"
            onClick={enviar}
            disabled={!arquivo || enviando}
          >
            <Upload size={14} /> {enviando ? "Enviando..." : "Adicionar a Base"}
          </button>
        </div>
        {arquivo && (
          <p className="upload-hint">
            Arquivo selecionado: <strong>{arquivo.name}</strong> ({(arquivo.size / 1024).toFixed(1)} KB)
          </p>
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <h2>Arquivos na Base</h2>
          {dados && (
            <div className="stats-row">
              <span className="stat-chip">{dados.total_arquivos} arquivos</span>
              <span className="stat-chip">{dados.chunks_indexados} chunks</span>
            </div>
          )}
        </div>

        {carregando && <p className="loading-text">Carregando...</p>}

        {dados && dados.arquivos?.length === 0 && (
          <div className="empty-state">
            <BookOpen size={40} />
            <p>Nenhum arquivo na base de conhecimento.</p>
            <p>Use o formulario acima para adicionar o primeiro documento.</p>
          </div>
        )}

        {dados?.arquivos?.map((arq) => (
          <div key={arq.nome} className="file-row">
            <span className="file-icon">{ICONES[arq.tipo] || "📁"}</span>
            <span className="file-name">{arq.nome}</span>
            <span className="file-type">{arq.tipo.toUpperCase()}</span>
            <span className="file-size">{arq.tamanho_kb} KB</span>
            <button
              className="btn-danger btn-sm"
              onClick={() => remover(arq.nome)}
            >
              <Trash2 size={12} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
