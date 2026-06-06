"""
Utilitários para nomes de arquivos recebidos via upload.
"""

import re
from pathlib import Path


def nome_arquivo_seguro(nome_original: str | None, fallback: str = "arquivo") -> str:
    """
    Retorna um nome de arquivo seguro para persistência local.

    Remove diretórios enviados pelo cliente, caracteres de controle e símbolos
    que podem causar traversal ou nomes inválidos em sistemas de arquivos.
    """
    nome = (nome_original or fallback).replace("\\", "/")
    nome = Path(nome).name.strip()
    nome = re.sub(r"[\x00-\x1f\x7f]", "", nome)
    nome = re.sub(r"\s+", " ", nome)
    nome = re.sub(r"[^0-9A-Za-zÀ-ÿ._ -]", "_", nome).strip(" .")

    if not nome or nome in {".", ".."}:
        nome = fallback

    return nome[:180]
