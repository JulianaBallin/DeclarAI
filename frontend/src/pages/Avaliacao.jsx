import { useState } from "react";
import { TestTube, CheckCircle, XCircle, TrendingUp, Info } from "lucide-react";
import { avaliarRecuperacao } from "../services/api";

const COMPARACAO_MODELOS = [
  { modelo: "mistral (RAG)", cobertura: 72.4, latencia: 8.2, descricao: "Modelo padrão + base de conhecimento", recomendado: true },
  { modelo: "mistral (sem RAG)", cobertura: 44.1, latencia: 5.1, descricao: "LLM direto, sem recuperação", recomendado: false },
  { modelo: "llama3.2:3b (RAG)", cobertura: 65.8, latencia: 6.4, descricao: "Modelo compacto + RAG", recomendado: false },
  { modelo: "phi4-mini (RAG)", cobertura: 68.3, latencia: 7.0, descricao: "Microsoft Phi-4 Mini + RAG", recomendado: false },
  { modelo: "gemma3:4b (RAG)", cobertura: 61.2, latencia: 6.9, descricao: "Google Gemma 3 + RAG", recomendado: false },
];

function GaugeBarra({ label, valor, maximo = 100 }) {
  const pct = Math.min(valor / maximo, 1);
  const cor = pct >= 0.7 ? "#2e7d32" : pct >= 0.4 ? "#f9a825" : "#c62828";
  return (
    <div className="gauge">
      <div className="gauge-header">
        <span className="gauge-label">{label}</span>
        <span className="gauge-value">{valor.toFixed(1)} / {maximo}</span>
      </div>
      <div className="gauge-track">
        <div
          className="gauge-fill"
          style={{ width: `${pct * 100}%`, backgroundColor: cor }}
        />
      </div>
    </div>
  );
}

export default function Avaliacao() {
  const [resultado, setResultado] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState(null);

  async function avaliar() {
    setCarregando(true);
    setErro(null);
    try {
      const dados = await avaliarRecuperacao();
      setResultado(dados);
    } catch (err) {
      setErro(err.message);
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div className="page">
      <h1>Avaliação do Pipeline RAG</h1>
      <p className="page-desc">
        Métricas quantitativas para validar a qualidade da recuperação semântica e das respostas geradas pelo DeclaraAI.
      </p>

      <div className="card">
        <h2>Métricas implementadas (inspiradas no RAGAS)</h2>
        <table className="metrics-table">
          <thead>
            <tr>
              <th>Métrica</th>
              <th>Descrição</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Taxa de Recuperação</strong></td>
              <td>Percentual de perguntas com ao menos 1 chunk recuperado</td>
            </tr>
            <tr>
              <td><strong>Score Médio de Contexto</strong></td>
              <td>Similaridade cosseno média dos chunks retornados (0 a 1)</td>
            </tr>
            <tr>
              <td><strong>Cobertura de Keywords</strong></td>
              <td>Percentual de termos esperados presentes na resposta gerada</td>
            </tr>
            <tr>
              <td><strong>Latência por Pergunta</strong></td>
              <td>Tempo médio de resposta em segundos, incluindo recuperação e geração</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="card">
        <div className="card-header">
          <h2>Comparação de Modelos LLM</h2>
          <span className="badge-secondary">60 perguntas anotadas</span>
        </div>
        <p className="page-desc" style={{ marginBottom: "1rem" }}>
          Comparação entre modelos Ollama com e sem RAG no dataset de avaliação do domínio IRPF.
          Cobertura de keywords indica quão bem a resposta abrange os termos esperados.
        </p>
        <div className="comparacao-table-wrap">
          <table className="metrics-table">
            <thead>
              <tr>
                <th>Modelo</th>
                <th>Cobertura Keywords (%)</th>
                <th>Latência Média (s)</th>
                <th>Descrição</th>
              </tr>
            </thead>
            <tbody>
              {COMPARACAO_MODELOS.map((m) => (
                <tr key={m.modelo} className={m.recomendado ? "row-recomendado" : ""}>
                  <td>
                    <strong>{m.modelo}</strong>
                    {m.recomendado && (
                      <span className="badge" style={{ marginLeft: 8, fontSize: "0.7rem" }}>padrão</span>
                    )}
                  </td>
                  <td>
                    <span style={{ color: m.cobertura >= 70 ? "#2e7d32" : m.cobertura >= 50 ? "#f9a825" : "#c62828", fontWeight: 700 }}>
                      {m.cobertura}%
                    </span>
                  </td>
                  <td>{m.latencia}s</td>
                  <td style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>{m.descricao}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="alert alert-warning" style={{ marginTop: "1rem" }}>
          <Info size={16} />
          Resultados obtidos com dataset de 60 perguntas anotadas. Execute os scripts para atualizar com
          seus modelos instalados: <code>python scripts/avaliar_llm.py</code>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2>Avaliar Recuperação Semântica</h2>
          <span className="badge-secondary">Não requer Ollama</span>
        </div>
        <p>Testa o retriever com o dataset anotado do domínio IRPF sem chamar o LLM.</p>
        <button
          className="btn-primary"
          onClick={avaliar}
          disabled={carregando}
          style={{ marginTop: "0.75rem" }}
        >
          <TestTube size={16} />
          {carregando ? "Avaliando..." : "Avaliar Recuperação"}
        </button>

        {erro && <div className="alert alert-error" style={{ marginTop: "0.75rem" }}>{erro}</div>}

        {resultado && (
          <div className="resultado-avaliacao">
            <div className="alert alert-success">
              <CheckCircle size={16} /> Avaliação concluída!
            </div>

            <GaugeBarra
              label="Taxa de Recuperação (%)"
              valor={resultado.taxa_recuperacao_pct || 0}
            />

            <div className="metricas-row">
              <div className="metrica-card">
                <span className="metrica-valor">
                  {(resultado.score_medio_contexto || 0).toFixed(4)}
                </span>
                <span className="metrica-label">Score Médio de Contexto</span>
              </div>
              <div className="metrica-card">
                <span className="metrica-valor">{resultado.chunks_indexados || 0}</span>
                <span className="metrica-label">Chunks Indexados</span>
              </div>
              <div className="metrica-card metrica-destaque">
                <span className="metrica-valor">{resultado.casos_sem_contexto || 0}</span>
                <span className="metrica-label">Casos sem Contexto</span>
              </div>
            </div>

            {resultado.interpretacao && (
              <div className="interpretacao">
                <TrendingUp size={16} />
                <p>{resultado.interpretacao}</p>
              </div>
            )}

            {resultado.analise_falhas?.length > 0 && (
              <details>
                <summary>Casos de Falha ({resultado.analise_falhas.length})</summary>
                <ul>
                  {resultado.analise_falhas.map((f, i) => (
                    <li key={i}>
                      <strong>{f.categoria}:</strong> {f.pergunta}
                    </li>
                  ))}
                </ul>
              </details>
            )}

            {resultado.resultados?.length > 0 && (
              <details>
                <summary>Resultados Detalhados por Pergunta</summary>
                <div className="resultados-lista">
                  {resultado.resultados.map((r) => (
                    <div key={r.id} className="resultado-item">
                      <span className={`resultado-status ${r.contexto_encontrado ? "ok" : "fail"}`}>
                        {r.contexto_encontrado ? <CheckCircle size={14} /> : <XCircle size={14} />}
                      </span>
                      <span className="resultado-pergunta">{r.pergunta}</span>
                      <span className="resultado-score">
                        Score: {r.score_medio_contexto.toFixed(4)} | Chunks: {r.chunks_recuperados}
                      </span>
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>
        )}
      </div>

      <div className="card">
        <h2>Avaliação com Scripts (linha de comando)</h2>
        <p>Para comparação completa entre modelos e estratégias de chunking:</p>
        <div className="code-block" style={{ marginTop: "0.75rem" }}>
          <pre>{`# Comparar modelos LLM (salva em data/eval/resultados_llm.csv)
python scripts/avaliar_llm.py

# Ablation study: vanilla LLM vs RAG
python scripts/avaliar_llm.py --no-rag

# Comparar estratégias de chunking
python scripts/avaliar_chunking.py

# Avaliação RAGAS (requer: pip install ragas)
python scripts/avaliar_ragas.py --modelo mistral`}</pre>
        </div>
      </div>
    </div>
  );
}
