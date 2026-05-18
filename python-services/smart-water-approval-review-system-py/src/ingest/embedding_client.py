from __future__ import annotations

import logging

from openai import OpenAI

from src.config import config

logger = logging.getLogger(__name__)


class EmbeddingClient:
    def __init__(self) -> None:
        api_key = config.EMBEDDING_API_KEY
        if not api_key:
            logger.warning("EMBEDDING_API_KEY is not set - embeddings will fail")
        self._client = OpenAI(
            api_key=api_key,
            base_url=config.EMBEDDING_BASE_URL,
        )
        self._model = config.EMBEDDING_MODEL
        self._provider = config.EMBEDDING_PROVIDER

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            resp = self._client.embeddings.create(
                model=self._model,
                input=texts,
            )
        except Exception as e:
            logger.error("Embedding API call failed: %s", e)
            raise

        embeddings: list[list[float]] = []
        for data in resp.data:
            if data.embedding:
                embeddings.append(data.embedding)

        if len(embeddings) != len(texts):
            logger.error(
                "Embedding API returned %d results for %d inputs",
                len(embeddings),
                len(texts),
            )
            raise ValueError("Embedding count mismatch")

        logger.info("Embedded %d texts (model: %s)", len(texts), self._model)
        return embeddings

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def model(self) -> str:
        return self._model
