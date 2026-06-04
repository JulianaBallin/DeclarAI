"""
Rotas da API para avaliação do pipeline RAG do DeclaraAI.

Expõe endpoints para medir a qualidade da recuperação semântica e das
respostas geradas, facilitando a análise de desempenho do sistema.
"""

import logging

from app.services.evaluation_service import ServicoAvaliacao
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

roteador = APIRouter()


class RequisicaoAvaliacaoPergunta(BaseModel):
    pergunta: str


@roteador.post(
    "/evaluation/recuperacao",
    summary="Avaliar recuperação semântica",
    description=(
        "Executa a avaliação apenas da etapa de recuperação do pipeline RAG, "
        "sem chamar o LLM. Mede a relevância semântica dos chunks recuperados "
        "para cada caso de teste pré-definido. Rápido - não requer Ollama ativo."
    ),
)
async def avaliar_recuperacao():
    """
    Avalia a qualidade da recuperação semântica com métricas quantitativas.

    Métricas retornadas:
    - taxa_recuperacao_pct: % de perguntas com contexto encontrado
    - score_medio_contexto: similaridade cosseno média dos chunks (0-1)
    - analise_falhas: casos onde a recuperação falhou
    """
    try:
        servico = ServicoAvaliacao()
        resultado = servico.avaliar_recuperacao()
        return resultado
    except Exception as erro:
        logger.error(f"Erro na avaliação de recuperação: {erro}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao avaliar recuperação: {str(erro)}",
        )


@roteador.post(
    "/evaluation/recuperacao-pergunta",
    summary="Avaliar recuperação de uma pergunta",
    description=(
        "Executa a recuperação semântica para uma pergunta isolada. "
        "Usado pelos scripts de comparação de chunking e modelos."
    ),
)
async def avaliar_recuperacao_pergunta(requisicao: RequisicaoAvaliacaoPergunta):
    """Avalia uma pergunta individual sem chamar o LLM."""
    if not requisicao.pergunta.strip():
        raise HTTPException(status_code=422, detail="A pergunta não pode ser vazia.")

    try:
        servico = ServicoAvaliacao()
        return servico.avaliar_pergunta(requisicao.pergunta)
    except Exception as erro:
        logger.error(f"Erro na avaliação da pergunta: {erro}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao avaliar pergunta: {str(erro)}",
        )


@roteador.post(
    "/evaluation/completa",
    summary="Avaliação completa do pipeline RAG",
    description=(
        "Executa a avaliação do pipeline RAG completo, incluindo geração de resposta "
        "via LLM (Ollama). Mede cobertura de palavras-chave nas respostas. "
        "Requer Ollama disponível - pode levar alguns minutos."
    ),
)
async def avaliar_completa():
    """
    Avalia o pipeline RAG completo (recuperação + geração de resposta).

    Métricas retornadas:
    - score_medio_contexto: relevância semântica dos chunks (0-1)
    - media_cobertura_keywords_pct: % médio de termos esperados nas respostas
    - taxa_recuperacao_pct: % de perguntas com contexto encontrado
    - analise_falhas: casos com cobertura de palavras-chave < 50%
    """
    try:
        servico = ServicoAvaliacao()
        resultado = await servico.avaliar_completa()
        return resultado
    except Exception as erro:
        logger.error(f"Erro na avaliação completa: {erro}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao avaliar pipeline completo: {str(erro)}",
        )


@roteador.get(
    "/evaluation/casos-teste",
    summary="Listar casos de teste",
    description="Retorna os casos de teste utilizados na avaliação do sistema.",
)
async def listar_casos_teste():
    """Lista as perguntas e categorias usadas na avaliação."""
    try:
        servico = ServicoAvaliacao()
        return {
            "casos_teste": servico.listar_casos_teste(),
            "total": len(servico.listar_casos_teste()),
        }
    except Exception as erro:
        raise HTTPException(status_code=500, detail=str(erro))
