"""
Script de avaliação RAGAS para o DeclaraAI.

Calcula as 4 métricas RAGAS usando Ollama local como juiz:
- Faithfulness: respostas estão apoiadas no contexto?
- Answer Relevancy: respostas endereçam as perguntas?
- Context Precision: chunks relevantes chegam no topo?
- Context Recall: tudo necessário foi recuperado?

Pré-requisito:
    pip install ragas langchain-community

Uso:
    python scripts/avaliar_ragas.py
    python scripts/avaliar_ragas.py --modelo qwen2.5:7b
    python scripts/avaliar_ragas.py --limite 10
"""

import argparse
import csv
import json
import os
from datetime import datetime
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent.parent
PERGUNTAS_PATH = BASE_DIR / "data" / "eval" / "perguntas.json"
RESULTADOS_DIR = BASE_DIR / "data" / "eval"
RESULTADOS_PATH = RESULTADOS_DIR / "resultados_ragas.csv"

API_URL = os.getenv("API_URL", "http://localhost:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

COLUNAS_CSV = [
    "modelo_llm",
    "pergunta_id",
    "categoria",
    "dificuldade",
    "pergunta",
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
    "media_ragas",
    "data_execucao",
]


def carregar_perguntas() -> list[dict]:
    with open(PERGUNTAS_PATH, encoding="utf-8") as f:
        dados = json.load(f)
    return dados["perguntas"]


def coletar_dados_rag(pergunta: str, modelo: str) -> dict:
    payload = {"pergunta": pergunta, "modelo": modelo}
    resposta = requests.post(f"{API_URL}/chat", json=payload, timeout=180)
    if resposta.status_code == 200:
        return resposta.json()
    return {}


def avaliar_com_ragas(perguntas: list[dict], modelo: str) -> list[dict]:
    try:
        from datasets import Dataset
        from langchain_community.llms import Ollama
        from ragas import evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )
    except ImportError as e:
        print(f"Dependência não instalada: {e}")
        print("Execute: pip install ragas langchain-community datasets")
        return []

    llm_juiz = Ollama(model=modelo, base_url=OLLAMA_URL)

    questoes, respostas, contextos, ground_truths = [], [], [], []

    print(f"\nColetando respostas do pipeline RAG com modelo '{modelo}'...")
    for i, pergunta in enumerate(perguntas, 1):
        print(f"  [{i:02d}/{len(perguntas)}] {pergunta['pergunta'][:55]}...")
        dados = coletar_dados_rag(pergunta["pergunta"], modelo)

        questoes.append(pergunta["pergunta"])
        respostas.append(dados.get("resposta", ""))
        contextos.append(dados.get("contexto_utilizado") or [])
        ground_truths.append(pergunta.get("resposta_referencia", ""))

    dataset = Dataset.from_dict({
        "question": questoes,
        "answer": respostas,
        "contexts": contextos,
        "ground_truth": ground_truths,
    })

    print("\nCalculando métricas RAGAS (pode demorar vários minutos)...")
    resultado = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=llm_juiz,
    )

    df = resultado.to_pandas()
    resultados = []
    for i, (_, row) in enumerate(df.iterrows()):
        pergunta = perguntas[i]
        faith = row.get("faithfulness", 0.0) or 0.0
        rel = row.get("answer_relevancy", 0.0) or 0.0
        prec = row.get("context_precision", 0.0) or 0.0
        rec = row.get("context_recall", 0.0) or 0.0
        media = (faith + rel + prec + rec) / 4

        resultados.append({
            "modelo_llm": modelo,
            "pergunta_id": pergunta["id"],
            "categoria": pergunta["categoria"],
            "dificuldade": pergunta["dificuldade"],
            "pergunta": pergunta["pergunta"],
            "faithfulness": round(faith, 4),
            "answer_relevancy": round(rel, 4),
            "context_precision": round(prec, 4),
            "context_recall": round(rec, 4),
            "media_ragas": round(media, 4),
            "data_execucao": datetime.now().isoformat(),
        })

    return resultados


def imprimir_resumo(resultados: list[dict], modelo: str) -> None:
    if not resultados:
        return
    n = len(resultados)
    metricas = ["faithfulness", "answer_relevancy", "context_precision", "context_recall", "media_ragas"]
    print(f"\nResumo RAGAS - modelo: {modelo}")
    for m in metricas:
        media = sum(r[m] for r in resultados) / n
        print(f"  {m}: {media:.4f}")


def salvar_csv(todos_resultados: list[dict]) -> None:
    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    modo = "a" if RESULTADOS_PATH.exists() else "w"
    with open(RESULTADOS_PATH, mode=modo, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS_CSV)
        if modo == "w":
            writer.writeheader()
        writer.writerows(todos_resultados)
    print(f"\nResultados salvos em: {RESULTADOS_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Avaliação RAGAS - DeclaraAI")
    parser.add_argument("--modelo", default="mistral", help="Modelo Ollama a usar como LLM e juiz")
    parser.add_argument("--limite", type=int, default=None, help="Limita número de perguntas")
    args = parser.parse_args()

    perguntas = carregar_perguntas()
    if args.limite:
        perguntas = perguntas[: args.limite]

    print(f"Dataset: {len(perguntas)} perguntas")
    print(f"Modelo: {args.modelo}")
    print(f"API: {API_URL}")

    resultados = avaliar_com_ragas(perguntas, args.modelo)
    if resultados:
        imprimir_resumo(resultados, args.modelo)
        salvar_csv(resultados)
        print(f"\nTotal de registros salvos: {len(resultados)}")
    else:
        print("Nenhum resultado gerado. Verifique as dependências e o Ollama.")


if __name__ == "__main__":
    main()
