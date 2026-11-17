
"""Servicio de generación de embeddings para búsqueda semántica."""

import numpy as np
from functools import lru_cache
from sentence_transformers import SentenceTransformer


MODEL_NAME = "intfloat/multilingual-e5-small"
EMBEDDING_DIMENSION = 384


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Carga y reutiliza el modelo de embeddings."""
    return SentenceTransformer(MODEL_NAME)


def encode_query(query_text: str) -> np.ndarray:
    """Genera un embedding normalizado para una consulta textual.

    Args:
        query_text: Consulta en lenguaje natural.

    Returns:
        Vector NumPy de 384 dimensiones normalizado.

    Raises:
        ValueError: Si la consulta está vacía.
    """
    query_text = query_text.strip()

    if not query_text:
        raise ValueError("La consulta no puede estar vacía.")

    model = get_embedding_model()

    embedding = model.encode(
        f"query: {query_text}",
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    if embedding.shape != (EMBEDDING_DIMENSION,):
        raise ValueError("Dimensionalidad del embedding incorrecta.")

    return embedding
