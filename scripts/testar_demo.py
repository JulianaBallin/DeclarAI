"""
Testes do fluxo de demonstração (docs/roteiro_demonstracao.md seção 5).
Uso: python scripts/testar_demo.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

BASE = "http://localhost:8000"
FRONTEND = "http://localhost:3000"
BASE_DIR = Path(__file__).parent.parent
# Recibo de dentista: classifica como Recibo Médico e ativa titularidade (Pedro dependente).
UPLOAD_FILE = BASE_DIR / "data/test_documents/simulation/05_recibo_dentista_pedro.txt"

PERGUNTA_CHAT = "Curso de inglês é dedutível como educação?"
PERFIL = {
    "nome_completo": "Ana Clara Rodrigues Nascimento",
    "cpf": "071.234.567-18",
}
BENEFICIARIO = "Pedro Henrique Rodrigues Nascimento"


def test(name: str, fn) -> bool:
    try:
        ok, detail = fn()
        tag = "OK" if ok else "FALHOU"
        print(f"[{tag}] {name}: {detail}")
        return ok
    except Exception as exc:
        print(f"[FALHOU] {name}: {exc}")
        return False


def main() -> int:
    results: list[bool] = []
    print("=" * 60)
    print("TESTES DO ROTEIRO DE DEMONSTRACAO - DeclarAI")
    print("=" * 60)

    # 1. Health
    def health():
        r = requests.get(f"{BASE}/", timeout=15)
        return r.status_code == 200, f"status={r.status_code}"

    results.append(test("Health GET /", health))

    # 2. Status
    def status():
        r = requests.get(f"{BASE}/status", timeout=15)
        d = r.json()
        ok = r.status_code == 200 and d.get("rag_inicializado") is not None
        return ok, (
            f"rag={d.get('rag_inicializado')}, "
            f"chunks={d.get('chunks_indexados', '?')}, "
            f"ollama={d.get('ollama_disponivel', '?')}"
        )

    results.append(test("Status GET /status", status))

    # 3. Frontend
    def frontend():
        r = requests.get(FRONTEND, timeout=15)
        return r.status_code == 200, f"status={r.status_code}"

    results.append(test("Frontend GET :3000", frontend))

    # 4. Knowledge
    def knowledge():
        r = requests.get(f"{BASE}/knowledge/files", timeout=30)
        d = r.json()
        ok = r.status_code == 200 and d.get("chunks_indexados", 0) > 0
        return ok, f"chunks={d.get('chunks_indexados')}, arquivos={d.get('total_arquivos')}"

    results.append(test("Knowledge GET /knowledge/files", knowledge))

    # 5. Ingest
    def ingest():
        r = requests.post(f"{BASE}/ingest", timeout=120)
        d = r.json() if r.status_code == 200 else {}
        ok = r.status_code == 200
        return ok, f"status={r.status_code}, chunks={d.get('chunks_indexados', d)}"

    results.append(test("Ingest POST /ingest", ingest))

    # 6. Chat aquecimento (2x)
    for i in (1, 2):
        def chat(n=i):
            inicio = time.perf_counter()
            r = requests.post(
                f"{BASE}/chat",
                json={"pergunta": PERGUNTA_CHAT},
                timeout=300,
            )
            lat = round(time.perf_counter() - inicio, 1)
            d = r.json() if r.status_code == 200 else {}
            ok = r.status_code == 200 and bool(d.get("resposta"))
            preview = (d.get("resposta") or "")[:80].replace("\n", " ")
            return ok, (
                f"latencia={lat}s, chunks={d.get('chunks_recuperados', 0)}, "
                f"preview={preview!r}"
            )

        results.append(test(f"Chat RAG (aquecimento {i}/2)", lambda n=i: chat(n)))

    # 7. Perfil declarante
    def perfil():
        r = requests.post(f"{BASE}/declarante/perfil", json=PERFIL, timeout=30)
        d = r.json() if r.status_code == 200 else {}
        ok = r.status_code == 200
        return ok, f"status={r.status_code}, nome={d.get('nome_completo', d)}"

    results.append(test("Perfil POST /declarante/perfil", perfil))

    # 8. Upload documento principal (recibo dentista — caso validado na avaliacao)
    def upload():
        if not UPLOAD_FILE.exists():
            return False, f"arquivo nao encontrado: {UPLOAD_FILE}"
        mime = (
            "application/pdf"
            if UPLOAD_FILE.suffix.lower() == ".pdf"
            else "text/plain"
        )
        inicio = time.perf_counter()
        with open(UPLOAD_FILE, "rb") as f:
            r = requests.post(
                f"{BASE}/documents/upload",
                files={"arquivo": (UPLOAD_FILE.name, f, mime)},
                timeout=600,
            )
        lat = round(time.perf_counter() - inicio, 1)
        body = r.json() if r.status_code == 200 else {}
        dados = body.get("dados", {})
        cat = dados.get("categoria", "?")
        tipo = dados.get("tipo_documento", "")
        natureza = dados.get("natureza_conteudo", "")
        # Na demo, o badge usa `categoria` (LLM pode variar); tipo/natureza/status
        # costumam refletir melhor o caso de saúde do recibo de dentista.
        ok = (
            r.status_code == 200
            and tipo == "Recibo"
            and natureza == "Saúde"
            and "dedut" in str(dados.get("status_irpf", "")).lower()
        )
        return ok, (
            f"latencia={lat}s, categoria={cat}, tipo={tipo}, natureza={natureza}, "
            f"status_irpf={dados.get('status_irpf', '?')}, http={r.status_code}"
        )

    results.append(test("Upload POST /documents/upload (recibo dentista)", upload))

    # 9. Titularidade
    def titularidade():
        r = requests.post(
            f"{BASE}/declarante/verificar-titularidade",
            params={"nome_beneficiario": BENEFICIARIO},
            timeout=30,
        )
        d = r.json() if r.status_code == 200 else {}
        ok = r.status_code == 200
        return ok, (
            f"status={d.get('status', '?')}, "
            f"mensagem={d.get('mensagem', '?')[:60]}"
        )

    results.append(test("Titularidade POST /declarante/verificar-titularidade", titularidade))

    # 10. Historico
    def historico():
        r = requests.get(f"{BASE}/history", timeout=30)
        d = r.json() if r.status_code == 200 else []
        ok = r.status_code == 200
        n = len(d) if isinstance(d, list) else d.get("total", 0)
        return ok, f"documentos={n}"

    results.append(test("Historico GET /history", historico))

    def resumo():
        r = requests.get(f"{BASE}/history/summary", timeout=30)
        d = r.json() if r.status_code == 200 else {}
        ok = r.status_code == 200
        return ok, f"keys={list(d.keys())[:5]}"

    results.append(test("Historico GET /history/summary", resumo))

    # 11. Avaliacao recuperacao
    def avaliacao():
        inicio = time.perf_counter()
        r = requests.post(f"{BASE}/evaluation/recuperacao", timeout=300)
        lat = round(time.perf_counter() - inicio, 1)
        d = r.json() if r.status_code == 200 else {}
        ok = r.status_code == 200
        return ok, (
            f"latencia={lat}s, casos={d.get('total_casos_testados', d.get('total', '?'))}"
        )

    results.append(test("Avaliacao POST /evaluation/recuperacao", avaliacao))

    # Resumo
    ok_count = sum(results)
    total = len(results)
    print("=" * 60)
    print(f"RESULTADO: {ok_count}/{total} testes OK")
    print("=" * 60)

    if ok_count == total:
        print("Demo pronta para ensaio no navegador.")
        print(f"  Frontend: {FRONTEND}")
        print(f"  Swagger:  {BASE}/docs")
        return 0

    print("Alguns testes falharam — revise os itens [FALHOU] acima.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
