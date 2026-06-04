"""
Script de avaliação comparativa de LLMs para o DeclaraAI.

Roda as perguntas do dataset de avaliação com diferentes modelos via Ollama
e salva os resultados em CSV para comparação no artigo acadêmico.

Modos de execução:
    python scripts/avaliar_llm.py                    # todos os modelos
    python scripts/avaliar_llm.py --modelo mistral   # apenas um modelo
    python scripts/avaliar_llm.py --no-rag           # ablation study (sem RAG)
"""

import argparse
import csv
import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent.parent
PERGUNTAS_PATH = BASE_DIR / "data" / "eval" / "perguntas.json"
RESULTADOS_DIR = BASE_DIR / "data" / "eval"
RESULTADOS_PATH = RESULTADOS_DIR / "resultados_llm.csv"

API_URL = os.getenv("API_URL", "http://localhost:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

MODELOS = [
    "vanilla_sem_rag",
    "mistral",
    "llama3.2:3b",
    "phi4-mini",
    "gemma3:4b",
    "qwen2.5:7b",
]

COLUNAS_CSV = [
    "modelo",
    "pergunta_id",
    "categoria",
    "dificuldade",
    "pergunta",
    "resposta_preview",
    "chunks_recuperados",
    "score_medio_contexto",
    "cobertura_keywords_pct",
    "latencia_segundos",
    "modo_rag",
    "data_execucao",
]


def carregar_perguntas() -> list[dict]:
    with open(PERGUNTAS_PATH, encoding="utf-8") as f:
        dados = json.load(f)
    return dados["perguntas"]


def chamar_chat_rag(pergunta: str, modelo: str) -> dict:
    payload = {"pergunta": pergunta, "modelo": modelo}
    inicio = time.perf_counter()
    resposta = requests.post(
        f"{API_URL}/chat",
        json=payload,
        timeout=180,
    )
    latencia = time.perf_counter() - inicio
    dados = resposta.json() if resposta.status_code == 200 else {}
    dados["latencia_segundos"] = round(latencia, 2)
    return dados


def chamar_llm_direto(pergunta: str, modelo: str) -> dict:
    payload = {
        "model": modelo,
        "prompt": (
            f"Você é um especialista em imposto de renda brasileiro. "
            f"Responda diretamente à seguinte pergunta: {pergunta}"
        ),
        "stream": False,
    }
    inicio = time.perf_counter()
    resposta = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json=payload,
        timeout=180,
    )
    latencia = time.perf_counter() - inicio
    dados = resposta.json() if resposta.status_code == 200 else {}
    return {
        "resposta": dados.get("response", ""),
        "chunks_recuperados": 0,
        "score_medio_contexto": 0.0,
        "latencia_segundos": round(latencia, 2),
    }


def calcular_cobertura_keywords(resposta: str, keywords: list[str]) -> float:
    if not keywords:
        return 0.0
    resp_lower = resposta.lower()
    encontradas = sum(1 for kw in keywords if kw.lower() in resp_lower)
    return round(encontradas / len(keywords) * 100, 1)


def avaliar_modelo(modelo: str, perguntas: list[dict], modo_rag: bool) -> list[dict]:
    resultados = []
    nome_modelo = modelo if modo_rag else "vanilla_sem_rag"
    modelo_ollama = modelo if modelo != "vanilla_sem_rag" else "mistral"

    print(f"\n{'=' * 60}")
    print(f"Modelo: {nome_modelo} | RAG: {'sim' if modo_rag else 'não'}")
    print(f"{'=' * 60}")

    for i, pergunta in enumerate(perguntas, 1):
        print(f"  [{i:02d}/{len(perguntas)}] {pergunta['pergunta'][:60]}...")

        try:
            if modo_rag and modelo != "vanilla_sem_rag":
                dados = chamar_chat_rag(pergunta["pergunta"], modelo_ollama)
            else:
                dados = chamar_llm_direto(pergunta["pergunta"], modelo_ollama)

            resposta_texto = dados.get("resposta", "")
            cobertura = calcular_cobertura_keywords(
                resposta_texto, pergunta.get("keywords", [])
            )

            resultados.append({
                "modelo": nome_modelo,
                "pergunta_id": pergunta["id"],
                "categoria": pergunta["categoria"],
                "dificuldade": pergunta["dificuldade"],
                "pergunta": pergunta["pergunta"],
                "resposta_preview": resposta_texto[:150].replace("\n", " "),
                "chunks_recuperados": dados.get("chunks_recuperados", 0),
                "score_medio_contexto": dados.get("score_medio_contexto", 0.0),
                "cobertura_keywords_pct": cobertura,
                "latencia_segundos": dados.get("latencia_segundos", 0),
                "modo_rag": "sim" if modo_rag else "não",
                "data_execucao": datetime.now().isoformat(),
            })
        except Exception as e:
            print(f"  ERRO: {e}")
            resultados.append({
                "modelo": nome_modelo,
                "pergunta_id": pergunta["id"],
                "categoria": pergunta["categoria"],
                "dificuldade": pergunta["dificuldade"],
                "pergunta": pergunta["pergunta"],
                "resposta_preview": f"ERRO: {e}",
                "chunks_recuperados": 0,
                "score_medio_contexto": 0.0,
                "cobertura_keywords_pct": 0.0,
                "latencia_segundos": 0,
                "modo_rag": "sim" if modo_rag else "não",
                "data_execucao": datetime.now().isoformat(),
            })

    return resultados


def imprimir_resumo(resultados: list[dict], modelo: str) -> None:
    if not resultados:
        return
    cobertura_media = sum(r["cobertura_keywords_pct"] for r in resultados) / len(resultados)
    latencia_media = sum(r["latencia_segundos"] for r in resultados) / len(resultados)
    chunks_media = sum(r["chunks_recuperados"] for r in resultados) / len(resultados)
    print(f"\nResumo - {modelo}")
    print(f"  Cobertura de keywords média: {cobertura_media:.1f}%")
    print(f"  Latência média: {latencia_media:.1f}s")
    print(f"  Chunks recuperados em média: {chunks_media:.1f}")


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
    parser = argparse.ArgumentParser(description="Avaliação comparativa de LLMs - DeclaraAI")
    parser.add_argument("--modelo", choices=MODELOS, help="Avalia apenas este modelo")
    parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Modo ablation study: chama LLM diretamente sem RAG",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=None,
        help="Limita o número de perguntas (útil para testes rápidos)",
    )
    args = parser.parse_args()

    perguntas = carregar_perguntas()
    if args.limite:
        perguntas = perguntas[: args.limite]

    print(f"Dataset: {len(perguntas)} perguntas")
    print(f"API: {API_URL}")

    modelos_para_testar = [args.modelo] if args.modelo else MODELOS
    todos_resultados = []

    for modelo in modelos_para_testar:
        modo_rag = not args.no_rag and modelo != "vanilla_sem_rag"
        resultados = avaliar_modelo(modelo, perguntas, modo_rag)
        imprimir_resumo(resultados, modelo)
        todos_resultados.extend(resultados)

    salvar_csv(todos_resultados)
    print(f"\nTotal de registros salvos: {len(todos_resultados)}")


if __name__ == "__main__":
    main()
