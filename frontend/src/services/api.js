import axios from "axios";

// Em Docker (nginx): usa /api que o nginx redireciona para o backend.
// Em dev local sem Docker: VITE_API_URL=http://localhost:8000 no .env,
//   ou o proxy do Vite em vite.config.js cuida de /api automaticamente.
const API_URL = import.meta.env.VITE_API_URL || "/api";

const api = axios.create({
  baseURL: API_URL,
  timeout: 180000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const detalhe = error.response?.data?.detail;
    const mensagem =
      typeof detalhe === "string"
        ? detalhe
        : error.response?.statusText || error.message || "Erro inesperado";
    return Promise.reject(new Error(mensagem));
  }
);

export async function enviarPergunta(pergunta, modelo) {
  const response = await api.post("/chat", { pergunta, modelo });
  return response.data;
}

export async function uploadDocumento(arquivo) {
  const formData = new FormData();
  formData.append("arquivo", arquivo);
  const response = await api.post("/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 180000,
  });
  return response.data;
}

export async function salvarDocumento(dados) {
  const response = await api.post("/documents/save", dados, { timeout: 180000 });
  return response.data;
}

export async function listarHistorico(params) {
  const response = await api.get("/history", { params });
  return response.data;
}

export async function excluirDocumento(id) {
  const response = await api.delete(`/history/${id}`);
  return response.data;
}

export async function obterResumoAnual(ano) {
  const response = await api.get("/history/summary", {
    params: ano ? { ano } : undefined,
  });
  return response.data;
}

export async function listarArquivosBase() {
  const response = await api.get("/knowledge/files");
  return response.data;
}

export async function uploadArquivoBase(arquivo) {
  const formData = new FormData();
  formData.append("arquivo", arquivo);
  const response = await api.post("/knowledge/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 180000,
  });
  return response.data;
}

export async function reindexarBase(configuracao) {
  const response = await api.post("/knowledge/reindex", configuracao, {
    timeout: 180000,
  });
  return response.data;
}

export async function removerArquivoBase(nome) {
  const response = await api.delete(`/knowledge/files/${nome}`);
  return response.data;
}

export async function obterStatus() {
  const response = await api.get("/status");
  return response.data;
}

export async function avaliarRecuperacao() {
  const response = await api.post("/evaluation/recuperacao", {}, { timeout: 120000 });
  return response.data;
}

export async function obterResumoCategorias() {
  const response = await api.get("/documents/categorias");
  return response.data;
}

export async function registrarPerfil(nome, cpf) {
  const response = await api.post("/declarante/perfil", { nome_completo: nome, cpf });
  return response.data;
}

export async function verificarTitularidade(nomeBeneficiario) {
  const response = await api.post("/declarante/verificar-titularidade", null, {
    params: { nome_beneficiario: nomeBeneficiario },
  });
  return response.data;
}
