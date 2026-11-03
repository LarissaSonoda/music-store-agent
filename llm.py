"""Fábrica de LLM compartilhável pela aplicação."""

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


@lru_cache(maxsize=1)
def get_llm() -> ChatGoogleGenerativeAI:
    """Retorna o modelo Google configurado por variáveis de ambiente."""
    return ChatGoogleGenerativeAI(
        model=os.getenv("MODEL_NAME", "gemma-4-31b-it"),
        temperature=0,
    )