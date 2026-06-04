import json
import sys
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

from app.rag.chunker import ChunkerTexto


def test_chunker_respeita_tamanho_e_preserva_sobreposicao():
    texto = (
        "Consulta médica com recibo fiscal válido. "
        "Mensalidade escolar possui limite anual. "
        "Previdência PGBL pode ser dedutível dentro do limite legal. "
        "Medicamento comprado em farmácia não é dedutível."
    )

    chunker = ChunkerTexto(tamanho_chunk=75, overlap=15)
    chunks = chunker.dividir_texto(texto)

    assert len(chunks) >= 2
    assert all(len(chunk) <= 75 for chunk in chunks)
    assert chunks[0][-15:].strip()
    assert chunks[0][-15:].strip().split()[-1] in chunks[1]


def test_dataset_de_avaliacao_tem_60_perguntas_anotadas():
    caminho = RAIZ / "data" / "eval" / "perguntas.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    perguntas = dados["perguntas"]

    assert len(perguntas) == 60
    assert all(pergunta["pergunta"].strip() for pergunta in perguntas)
    assert all(pergunta.get("keywords") for pergunta in perguntas)
    assert all(pergunta.get("resposta_referencia") for pergunta in perguntas)


def test_arquivos_internos_estao_protegidos_no_gitignore():
    gitignore = (RAIZ / ".gitignore").read_text(encoding="utf-8")

    assert "AGENTE.md" in gitignore
    assert "Atividade.pdf" in gitignore
