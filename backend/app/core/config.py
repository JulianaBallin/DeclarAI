"""
Configurações centrais da aplicação DeclaraAI.
Carrega variáveis de ambiente com fallback para valores padrão.
"""

from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracoes(BaseSettings):
    """Configurações globais carregadas via variáveis de ambiente ou arquivo .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Informações da aplicação
    NOME_APP: str = "DeclaraAI"
    VERSAO_APP: str = "1.0.0"
    DEBUG: bool = False

    # Banco de dados relacional (SQLite)
    DATABASE_URL: str = "sqlite:///./data/declaraai.db"

    # Caminhos de dados
    CAMINHO_UPLOADS: str = "./data/uploads"
    CAMINHO_BASE_CONHECIMENTO: str = "./data/knowledge_base"
    CAMINHO_CHROMA: str = "./data/chroma_db"

    # Configurações de chunking
    # chunk_size=600: equilibra contexto e precisão semântica em documentos fiscais
    # overlap=80: preserva continuidade entre fragmentos adjacentes
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 80

    # Modelo de embeddings (multilíngue, leve, código aberto)
    # paraphrase-multilingual-MiniLM-L12-v2: suporte a PT-BR, 384 dims, rápido
    MODELO_EMBEDDINGS: str = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    # Integração com Ollama (LLM local)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODELO: str = "mistral"

    # Recuperação semântica
    TOP_K_RESULTADOS: int = 5

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalizar_debug(cls, valor: Any) -> Any:
        """Aceita valores comuns de ambiente para modo debug."""
        if isinstance(valor, str):
            normalizado = valor.strip().lower()
            if normalizado in {
                "release",
                "prod",
                "production",
                "false",
                "0",
                "no",
                "não",
                "nao",
                "off",
            }:
                return False
            if normalizado in {
                "debug",
                "dev",
                "development",
                "true",
                "1",
                "yes",
                "sim",
                "on",
            }:
                return True
        return valor


# Instância global de configurações
configuracoes = Configuracoes()
