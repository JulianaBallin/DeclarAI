import { useState, useRef } from "react";
import { Upload as UploadIcon, FileText, CheckCircle, AlertCircle, X } from "lucide-react";
import { uploadDocumento, salvarDocumento } from "../services/api";

const FORMATOS_ACEITOS = ".pdf,.txt,.html,.xml,.jpg,.jpeg,.png";

export default function Upload() {
  const [arquivo, setArquivo] = useState(null);
  const [processando, setProcessando] = useState(false);
  const [dados, setDados] = useState(null);
  const [salvando, setSalvando] = useState(false);
  const [mensagem, setMensagem] = useState(null);
  const [confirmado, setConfirmado] = useState(false);
  const inputRef = useRef(null);

  function selecionarArquivo(e) {
    const f = e.target.files?.[0];
    if (f) {
      setArquivo(f);
      setDados(null);
      setMensagem(null);
      setConfirmado(false);
    }
  }

  function onDrop(e) {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) {
      setArquivo(f);
      setDados(null);
      setMensagem(null);
      setConfirmado(false);
    }
  }

  async function processar() {
    if (!arquivo) return;
    setProcessando(true);
    setMensagem(null);
    try {
      const resultado = await uploadDocumento(arquivo);
      setDados(resultado.dados || resultado);
      setMensagem({ tipo: "success", texto: "Documento processado com sucesso!" });
    } catch (err) {
      setMensagem({ tipo: "error", texto: `Erro: ${err.message}` });
    } finally {
      setProcessando(false);
    }
  }

  async function salvar() {
    if (!dados || !confirmado) return;
    setSalvando(true);
    try {
      const info = await salvarDocumento(dados);
      setMensagem({
        tipo: "success",
        texto: `Documento salvo! ID: ${info.id} | Categoria: ${info.categoria}`,
      });
      setDados(null);
      setArquivo(null);
      setConfirmado(false);
    } catch (err) {
      setMensagem({ tipo: "error", texto: `Erro ao salvar: ${err.message}` });
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="page">
      <h1>Upload de Documento Fiscal</h1>
      <p className="page-desc">
        Envie recibos medicos, notas fiscais, comprovantes de educacao, informes de rendimentos
        e outros documentos para organizacao automatica.
      </p>

      <div
        className={`dropzone${arquivo ? " dropzone-active" : ""}`}
        onDrop={onDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => inputRef.current?.click()}
      >
        <UploadIcon size={40} className="dropzone-icon" />
        {arquivo ? (
          <p className="dropzone-filename">
            <FileText size={16} /> {arquivo.name}{" "}
            <span className="dropzone-size">
              ({(arquivo.size / 1024).toFixed(1)} KB)
            </span>
          </p>
        ) : (
          <>
            <p>Arraste o arquivo aqui ou clique para selecionar</p>
            <p className="dropzone-hint">PDF, TXT, HTML, XML, JPG, PNG (max 10 MB)</p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept={FORMATOS_ACEITOS}
          onChange={selecionarArquivo}
          style={{ display: "none" }}
        />
      </div>

      {arquivo && !dados && (
        <button
          className="btn-primary"
          onClick={processar}
          disabled={processando}
        >
          {processando ? "Processando..." : "Processar Documento"}
        </button>
      )}

      {mensagem && (
        <div className={`alert alert-${mensagem.tipo}`}>
          {mensagem.tipo === "success" ? (
            <CheckCircle size={16} />
          ) : (
            <AlertCircle size={16} />
          )}
          {mensagem.texto}
        </div>
      )}

      {dados && (
        <div className="card">
          <div className="card-header">
            <h2>Dados Extraidos</h2>
            <span className="badge">{dados.categoria || "Nao classificado"}</span>
          </div>

          <div className="dados-grid">
            <div className="dado-item">
              <label>Tipo do documento</label>
              <span>{dados.tipo_documento || "-"}</span>
            </div>
            <div className="dado-item">
              <label>Natureza do conteudo</label>
              <span>{dados.natureza_conteudo || "-"}</span>
            </div>
            <div className="dado-item">
              <label>Situacao no IRPF</label>
              <span className={`status-${(dados.status_irpf || "").toLowerCase().replace(/\s/g, "-")}`}>
                {dados.status_irpf || "-"}
              </span>
            </div>
            <div className="dado-item">
              <label>Emitente</label>
              <span>{dados.emitente_detectado || "-"}</span>
            </div>
            <div className="dado-item">
              <label>CNPJ/CPF</label>
              <span>{dados.cnpj_emitente || "-"}</span>
            </div>
            <div className="dado-item">
              <label>Data</label>
              <span>{dados.data_detectada || "-"}</span>
            </div>
            <div className="dado-item">
              <label>Valor</label>
              <span>{dados.valor_detectado || "-"}</span>
            </div>
            <div className="dado-item">
              <label>Beneficiario</label>
              <span>{dados.nome_beneficiario || "-"}</span>
            </div>
          </div>

          {dados.justificativa_enriquecida && (
            <div className="justificativa">
              <strong>Analise do assistente:</strong>
              <p>{dados.justificativa_enriquecida}</p>
            </div>
          )}

          {dados.aviso_deducao && (
            <div className="alert alert-warning">
              <AlertCircle size={16} />
              {dados.aviso_deducao}
            </div>
          )}

          <div className="confirmacao">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={confirmado}
                onChange={(e) => setConfirmado(e.target.checked)}
              />
              Confirmo que revisei os dados acima e estao corretos
            </label>
          </div>

          <div className="btn-row">
            <button
              className="btn-primary"
              onClick={salvar}
              disabled={!confirmado || salvando}
            >
              {salvando ? "Salvando..." : "Salvar Documento"}
            </button>
            <button
              className="btn-secondary"
              onClick={() => {
                setDados(null);
                setArquivo(null);
                setConfirmado(false);
                setMensagem(null);
              }}
            >
              <X size={14} /> Descartar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
