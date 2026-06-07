"""
Script de avaliação de estratégias de chunking para o DeclarAI.

Testa diferentes configurações de chunking nas perguntas do dataset
e salva métricas em CSV para comparação no artigo acadêmico.

Configurações testadas:
- Chunking fixo com diferentes chunk_size e overlap
- Chunking por sentença (NLTK)
- Chunking semântico (SemanticChunker)

Uso:
    python scripts/avaliar_chunking.py
    python scripts/avaliar_chunking.py --config fixo
    python scripts/avaliar_chunking.py --limite 10
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
RESULTADOS_PATH = RESULTADOS_DIR / "resultados_chunking.csv"

API_URL = os.getenv("API_URL", "http://localhost:8000")

CONFIGURACOES_CHUNKING = [
    {"nome": "fixo_200_0",   "tipo": "fixo", "chunk_size": 200, "chunk_overlap": 0},
    {"nome": "fixo_400_40",  "tipo": "fixo", "chunk_size": 400, "chunk_overlap": 40},
    {"nome": "fixo_600_80",  "tipo": "fixo", "chunk_size": 600, "chunk_overlap": 80},
    {"nome": "fixo_800_120", "tipo": "fixo", "chunk_size": 800, "chunk_overlap": 120},
    {"nome": "fixo_1000_200","tipo": "fixo", "chunk_size": 1000,"chunk_overlap": 200},
    {"nome": "sentenca",     "tipo": "sentenca", "chunk_size": None, "chunk_overlap": None},
    {"nome": "semantico",    "tipo": "semantico","chunk_size": None, "chunk_overlap": None},
]

COLUNAS_CSV = [
    "configuracao",
    "tipo_chunking",
    "chunk_size",
    "chunk_overlap",
    "pergunta_id",
    "categoria",
    "dificuldade",
    "pergunta",
    "chunks_recuperados",
    "score_medio_contexto",
    "cobertura_keywords_pct",
    "contexto_encontrado",
    "latencia_segundos",
    "data_execucao",
]


def carregar_perguntas() -> list[dict]:
    with open(PERGUNTAS_PATH, encoding="utf-8") as f:
        dados = json.load(f)
    return dados["perguntas"]


def configurar_chunking(config: dict) -> bool:
    try:
        payload = {
            "tipo": config["tipo"],
            "chunk_size": config["chunk_size"],
            "chunk_overlap": config["chunk_overlap"],
        }
        resposta = requests.post(
            f"{API_URL}/knowledge/reindex",
            json=payload,
            timeout=300,
        )
        if resposta.status_code == 200:
            dados = resposta.json()
            print(f"  Re-indexado: {dados.get('chunks_indexados', 0)} chunks")
            return True
        print(f"  Erro ao re-indexar: {resposta.status_code} - {resposta.text[:100]}")
        return False
    except Exception as e:
        print(f"  Erro ao configurar chunking: {e}")
        return False


def avaliar_recuperacao(pergunta: str) -> dict:
    inicio = time.perf_counter()
    try:
        resposta = requests.post(
            f"{API_URL}/evaluation/recuperacao-pergunta",
            json={"pergunta": pergunta},
            timeout=60,
        )
        latencia = time.perf_counter() - inicio
        if resposta.status_code == 200:
            dados = resposta.json()
            dados["latencia_segundos"] = round(latencia, 2)
            return dados
    except Exception as e:
        print(f"  ERRO: {e}")
    return {
        "chunks_recuperados": 0,
        "score_medio_contexto": 0.0,
        "contexto_encontrado": False,
        "latencia_segundos": 0,
    }


def calcular_cobertura_keywords(contextos: list[str], keywords: list[str]) -> float:
    if not keywords or not contextos:
        return 0.0
    texto_completo = " ".join(contextos).lower()
    encontradas = sum(1 for kw in keywords if kw.lower() in texto_completo)
    return round(encontradas / len(keywords) * 100, 1)


def avaliar_configuracao(config: dict, perguntas: list[dict]) -> list[dict]:
    print(f"\n{'=' * 60}")
    print(f"Configuração: {config['nome']}")
    if config["chunk_size"]:
        print(f"  chunk_size={config['chunk_size']}, overlap={config['chunk_overlap']}")
    print(f"{'=' * 60}")

    configurado = configurar_chunking(config)
    if not configurado:
        print("  Pulando esta configuração (erro no re-indexamento)")
        return []

    resultados = []
    for i, pergunta in enumerate(perguntas, 1):
        print(f"  [{i:02d}/{len(perguntas)}] {pergunta['pergunta'][:55]}...")

        dados = avaliar_recuperacao(pergunta["pergunta"])
        cobertura = calcular_cobertura_keywords(
            dados.get("contextos", []), pergunta.get("keywords", [])
        )

        resultados.append({
            "configuracao": config["nome"],
            "tipo_chunking": config["tipo"],
            "chunk_size": config["chunk_size"] or "",
            "chunk_overlap": config["chunk_overlap"] or "",
            "pergunta_id": pergunta["id"],
            "categoria": pergunta["categoria"],
            "dificuldade": pergunta["dificuldade"],
            "pergunta": pergunta["pergunta"],
            "chunks_recuperados": dados.get("chunks_recuperados", 0),
            "score_medio_contexto": dados.get("score_medio_contexto", 0.0),
            "cobertura_keywords_pct": cobertura,
            "contexto_encontrado": dados.get("contexto_encontrado", False),
            "latencia_segundos": dados.get("latencia_segundos", 0),
            "data_execucao": datetime.now().isoformat(),
        })

    return resultados


def imprimir_resumo(resultados: list[dict], config_nome: str) -> None:
    if not resultados:
        return
    n = len(resultados)
    taxa_rec = sum(1 for r in resultados if r["contexto_encontrado"]) / n * 100
    score_medio = sum(r["score_medio_contexto"] for r in resultados) / n
    cobertura_media = sum(r["cobertura_keywords_pct"] for r in resultados) / n
    latencia_media = sum(r["latencia_segundos"] for r in resultados) / n
    print(f"\nResumo - {config_nome}")
    print(f"  Taxa de recuperação: {taxa_rec:.1f}%")
    print(f"  Score médio de contexto: {score_medio:.4f}")
    print(f"  Cobertura de keywords média: {cobertura_media:.1f}%")
    print(f"  Latência média: {latencia_media:.2f}s")


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
    parser = argparse.ArgumentParser(description="Avaliação de estratégias de chunking - DeclarAI")
    parser.add_argument(
        "--config",
        choices=[c["nome"] for c in CONFIGURACOES_CHUNKING],
        help="Avalia apenas esta configuração",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=None,
        help="Limita número de perguntas (útil para testes rápidos)",
    )
    args = parser.parse_args()

    perguntas = carregar_perguntas()
    if args.limite:
        perguntas = perguntas[: args.limite]

    configs = (
        [c for c in CONFIGURACOES_CHUNKING if c["nome"] == args.config]
        if args.config
        else CONFIGURACOES_CHUNKING
    )

    print(f"Dataset: {len(perguntas)} perguntas")
    print(f"Configurações a testar: {len(configs)}")
    print(f"API: {API_URL}")

    todos_resultados = []
    for config in configs:
        resultados = avaliar_configuracao(config, perguntas)
        imprimir_resumo(resultados, config["nome"])
        todos_resultados.extend(resultados)

    salvar_csv(todos_resultados)
    print(f"\nTotal de registros salvos: {len(todos_resultados)}")

    print("\nPróximos passos:")
    print("  1. Abra notebooks/01_experimentos_chunking.ipynb para visualizar os gráficos")
    print("  2. Execute: jupyter notebook notebooks/01_experimentos_chunking.ipynb")


if __name__ == "__main__":
    main()
