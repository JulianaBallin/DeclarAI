import { useState, useRef, useEffect } from "react";
import { Send, Trash2, Bot, User, Sparkles } from "lucide-react";
import { enviarPergunta } from "../services/api";

const MENSAGEM_BOAS_VINDAS = {
  papel: "assistant",
  conteudo:
    "Olá! Sou o DeclaraAI, seu assistente para o Imposto de Renda.\n\nPode me perguntar sobre deduções, documentos necessários, prazos, categorias tributárias, rendimentos isentos e muito mais.",
  fontes: [],
};

const SUGESTOES = [
  "Quais despesas médicas posso deduzir?",
  "Qual o limite de dedução com educação?",
  "Como funciona o PGBL no IR?",
  "Quem é obrigado a declarar o IR?",
  "Qual a diferença entre simplificada e completa?",
  "Posso deduzir pensão alimentícia?",
];

const SAUDACOES = new Set([
  "oi", "ola", "olá", "hey", "hello", "hi", "e ai", "e aí", "eai",
  "bom dia", "boa tarde", "boa noite", "tudo bem", "tudo bom",
  "obrigado", "obrigada", "valeu", "tchau", "ate mais", "até mais", "ate logo", "até logo",
]);

function respostaLocal(pergunta) {
  const norm = pergunta.toLowerCase().trim().replace(/[!.,?]$/, "");
  if (SAUDACOES.has(norm)) {
    return "Olá! Como posso te ajudar com o Imposto de Renda hoje?";
  }
  return null;
}

export default function Chat() {
  const [mensagens, setMensagens] = useState([MENSAGEM_BOAS_VINDAS]);
  const [input, setInput] = useState("");
  const [carregando, setCarregando] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensagens]);

  async function enviar(e) {
    e.preventDefault();
    const pergunta = input.trim();
    if (!pergunta || carregando) return;

    setInput("");
    setMensagens((prev) => [...prev, { papel: "user", conteudo: pergunta }]);

    const respLocal = respostaLocal(pergunta);
    if (respLocal) {
      setMensagens((prev) => [
        ...prev,
        { papel: "assistant", conteudo: respLocal, fontes: [] },
      ]);
      return;
    }

    setCarregando(true);
    try {
      const dados = await enviarPergunta(pergunta);
      setMensagens((prev) => [
        ...prev,
        {
          papel: "assistant",
          conteudo: dados.resposta || "Sem resposta.",
          fontes: dados.fontes || [],
          chunks: dados.chunks_recuperados || 0,
          score: dados.score_medio_contexto,
        },
      ]);
    } catch (err) {
      setMensagens((prev) => [
        ...prev,
        {
          papel: "assistant",
          conteudo: `Erro ao contatar o servidor: ${err.message}. Verifique se o backend está em execução.`,
          fontes: [],
          erro: true,
        },
      ]);
    } finally {
      setCarregando(false);
    }
  }

  function usarSugestao(texto) {
    setInput(texto);
  }

  const mostrarSugestoes = mensagens.length === 1;

  return (
    <div className="page-chat">
      <div className="chat-header">
        <h1>Chat com Assistente RAG</h1>
        <button
          className="btn-secondary btn-sm"
          onClick={() => setMensagens([MENSAGEM_BOAS_VINDAS])}
        >
          <Trash2 size={14} /> Limpar
        </button>
      </div>

      <div className="chat-messages">
        {mensagens.map((msg, i) => (
          <div key={i} className={`message message-${msg.papel}`}>
            <div className="message-avatar">
              {msg.papel === "assistant" ? <Bot size={18} /> : <User size={18} />}
            </div>
            <div className="message-body">
              <div className={`message-bubble${msg.erro ? " message-error" : ""}`}>
                {msg.conteudo.split("\n").map((linha, j) => (
                  <p key={j}>{linha}</p>
                ))}
              </div>
              {msg.chunks !== undefined && (
                <span className="message-meta">
                  {msg.chunks} trechos consultados
                  {msg.score !== undefined && msg.score > 0 && (
                    <> &middot; score {msg.score.toFixed(3)}</>
                  )}
                </span>
              )}
              {msg.fontes && msg.fontes.length > 0 && (
                <details className="fontes-details">
                  <summary>Fontes consultadas ({msg.fontes.length})</summary>
                  <ul>
                    {msg.fontes.map((f, j) => (
                      <li key={j}>{f}</li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          </div>
        ))}

        {mostrarSugestoes && (
          <div className="sugestoes-area">
            <p className="sugestoes-titulo">
              <Sparkles size={14} /> Perguntas frequentes
            </p>
            <div className="sugestoes-grid">
              {SUGESTOES.map((s, i) => (
                <button
                  key={i}
                  className="sugestao-btn"
                  onClick={() => usarSugestao(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {carregando && (
          <div className="message message-assistant">
            <div className="message-avatar">
              <Bot size={18} />
            </div>
            <div className="message-body">
              <div className="message-bubble message-loading">
                <span className="loading-dot" />
                <span className="loading-dot" />
                <span className="loading-dot" />
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form className="chat-input-area" onSubmit={enviar}>
        <input
          className="chat-input"
          type="text"
          placeholder="Digite sua dúvida sobre IR..."
          aria-label="Digite sua dúvida sobre Imposto de Renda"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={carregando}
        />
        <button
          className="btn-primary chat-send-btn"
          type="submit"
          disabled={!input.trim() || carregando}
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}
