import { useState, useRef } from "react";
import {
  Upload as UploadIcon,
  FileText,
  CheckCircle,
  AlertCircle,
  ShieldCheck,
  X,
} from "lucide-react";
import {
  registrarPerfil,
  uploadDocumento,
  salvarDocumento,
  verificarTitularidade,
} from "../services/api";

const FORMATOS_ACEITOS = ".pdf,.txt,.html,.xml,.jpg,.jpeg,.png";

export default function Upload() {
  const [arquivo, setArquivo] = useState(null);
  const [processando, setProcessando] = useState(false);
  const [dados, setDados] = useState(null);
  const [salvando, setSalvando] = useState(false);
  const [mensagem, setMensagem] = useState(null);
  const [confirmado, setConfirmado] = useState(false);
  const [perfil, setPerfil] = useState(() => ({
    nome: localStorage.getItem("declaraai_nome_declarante") || "",
    cpf: localStorage.getItem("declaraai_cpf_declarante") || "",
  }));
  const [salvandoPerfil, setSalvandoPerfil] = useState(false);
  const [titularidade, setTitularidade] = useState(null);
  const inputRef = useRef(null);

  function selecionarArquivo(e) {
    const f = e.target.files?.[0];
    if (f) {
      setArquivo(f);
      setDados(null);
      setMensagem(null);
      setConfirmado(false);
      setTitularidade(null);
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
      setTitularidade(null);
    }
  }

  async function salvarPerfil(e) {
    e.preventDefault();
    if (!perfil.nome.trim() || !perfil.cpf.trim()) {
      setMensagem({
        tipo: "error",
        texto: "Informe nome completo e CPF do declarante.",
      });
      return;
    }

    setSalvandoPerfil(true);
    try {
      await registrarPerfil(perfil.nome.trim(), perfil.cpf.trim());
      localStorage.setItem("declaraai_nome_declarante", perfil.nome.trim());
      localStorage.setItem("declaraai_cpf_declarante", perfil.cpf.trim());
      setMensagem({ tipo: "success", texto: "Declarante registrado para esta sessão." });
      if (dados?.nome_beneficiario) {
        await avaliarTitularidade(dados.nome_beneficiario);
      }
    } catch (err) {
      setMensagem({ tipo: "error", texto: `Erro ao registrar declarante: ${err.message}` });
    } finally {
      setSalvandoPerfil(false);
    }
  }

  async function avaliarTitularidade(nomeBeneficiario) {
    if (!nomeBeneficiario || !perfil.nome.trim() || !perfil.cpf.trim()) {
      setTitularidade(null);
      return;
    }

    await registrarPerfil(perfil.nome.trim(), perfil.cpf.trim());
    const resultado = await verificarTitularidade(nomeBeneficiario);
    setTitularidade(resultado);
  }

  async function processar() {
    if (!arquivo) return;
    setProcessando(true);
    setMensagem(null);
    setTitularidade(null);
    try {
      const resultado = await uploadDocumento(arquivo);
      const dadosProcessados = resultado.dados || resultado;
      setDados(dadosProcessados);
      await avaliarTitularidade(dadosProcessados.nome_beneficiario);
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
      setTitularidade(null);
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
        Envie recibos médicos, notas fiscais, comprovantes de educação, informes de rendimentos
        e outros documentos para organização automática.
      </p>

      <form className="card perfil-card" onSubmit={salvarPerfil}>
        <div className="card-header">
          <h2>Declarante</h2>
          <span className="badge-secondary">Titularidade</span>
        </div>
        <div className="perfil-grid">
          <label>
            Nome completo
            <input
              type="text"
              value={perfil.nome}
              onChange={(e) => setPerfil((prev) => ({ ...prev, nome: e.target.value }))}
              placeholder="Nome do titular da declaração"
            />
          </label>
          <label>
            CPF
            <input
              type="text"
              value={perfil.cpf}
              onChange={(e) => setPerfil((prev) => ({ ...prev, cpf: e.target.value }))}
              placeholder="000.000.000-00"
            />
          </label>
          <button
            className="btn-secondary"
            type="submit"
            disabled={salvandoPerfil || !perfil.nome.trim() || !perfil.cpf.trim()}
          >
            <ShieldCheck size={14} />
            {salvandoPerfil ? "Registrando..." : "Registrar"}
          </button>
        </div>
      </form>

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
            <h2>Dados Extraídos</h2>
            <span className="badge">{dados.categoria || "Não classificado"}</span>
          </div>

          <div className="dados-grid">
            <div className="dado-item">
              <label>Tipo do documento</label>
              <span>{dados.tipo_documento || "-"}</span>
            </div>
            <div className="dado-item">
              <label>Natureza do conteúdo</label>
              <span>{dados.natureza_conteudo || "-"}</span>
            </div>
            <div className="dado-item">
              <label>Situação no IRPF</label>
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
              <label>Beneficiário</label>
              <span>{dados.nome_beneficiario || "-"}</span>
            </div>
          </div>

          {dados.nome_beneficiario && !titularidade && (
            <div className="alert alert-warning">
              <AlertCircle size={16} />
              Registre o declarante acima para verificar se o beneficiário é titular,
              dependente provável ou terceiro.
            </div>
          )}

          {titularidade && (
            <div
              className={`alert ${
                titularidade.status === "titular" ? "alert-success" : "alert-warning"
              }`}
            >
              <ShieldCheck size={16} />
              {titularidade.mensagem}
            </div>
          )}

          {dados.justificativa_enriquecida && (
            <div className="justificativa">
              <strong>Análise do assistente:</strong>
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
              Confirmo que revisei os dados acima e estão corretos
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
                setTitularidade(null);
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
