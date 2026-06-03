import { useState } from "react";
import { TestTube, CheckCircle, XCircle, TrendingUp } from "lucide-react";
import { avaliarRecuperacao } from "../services/api";

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
      <h1>Avaliacao do Pipeline RAG</h1>
      <p className="page-desc">
        Metricas quantitativas para validar a qualidade da recuperacao semantica
        e das respostas geradas pelo DeclaraAI.
      </p>

      <div className="card">
        <h2>Metricas implementadas (inspiradas no RAGAS)</h2>
        <table className="metrics-table">
          <thead>
            <tr>
              <th>Metrica</th>
              <th>Descricao</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Taxa de Recuperacao</strong></td>
              <td>% de perguntas com ao menos 1 chunk recuperado</td>
            </tr>
            <tr>
              <td><strong>Score Medio de Contexto</strong></td>
              <td>Similaridade cosseno media dos chunks retornados (0-1)</td>
            </tr>
            <tr>
              <td><strong>Cobertura de Keywords</strong></td>
              <td>% de termos esperados presentes na resposta gerada</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="card">
        <div className="card-header">
          <h2>Avaliar Recuperacao Semantica</h2>
          <span className="badge-secondary">Nao requer Ollama</span>
        </div>
        <p>Testa o retriever com 8 perguntas do dominio IRPF sem chamar o LLM.</p>
        <button
          className="btn-primary"
          onClick={avaliar}
          disabled={carregando}
        >
          <TestTube size={16} />
          {carregando ? "Avaliando..." : "Avaliar Recuperacao"}
        </button>

        {erro && <div className="alert alert-error">{erro}</div>}

        {resultado && (
          <div className="resultado-avaliacao">
            <div className="alert alert-success">
              <CheckCircle size={16} /> Avaliacao concluida!
            </div>

            <GaugeBarra
              label="Taxa de Recuperacao (%)"
              valor={resultado.taxa_recuperacao_pct || 0}
            />

            <div className="metricas-row">
              <div className="metrica-card">
                <span className="metrica-valor">
                  {(resultado.score_medio_contexto || 0).toFixed(4)}
                </span>
                <span className="metrica-label">Score Medio de Contexto</span>
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
        <h2>Avaliacao com Scripts (linha de comando)</h2>
        <p>Para comparacao completa entre modelos e estrategias de chunking:</p>
        <div className="code-block">
          <pre>{`# Comparar modelos LLM (salva em data/eval/resultados_llm.csv)
python scripts/avaliar_llm.py

# Ablation study: vanilla LLM vs RAG
python scripts/avaliar_llm.py --no-rag

# Comparar estrategias de chunking
python scripts/avaliar_chunking.py

# Avaliacao RAGAS (requer: pip install ragas)
python scripts/avaliar_ragas.py --modelo mistral`}</pre>
        </div>
      </div>
    </div>
  );
}
