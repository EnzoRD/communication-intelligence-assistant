
"""Pruebas de integración del repositorio de búsqueda semántica."""

import pytest

from src.database.connection import get_connection
from src.database.repositories import semantic_repository
from src.database.repositories.semantic_repository import (
    search_similar_news,
    search_topic_news,
)


# Configuración temática utilizada en las pruebas.
TEST_TOPIC = "inteligencia_artificial"
TEST_QUERY = "riesgos de la inteligencia artificial"


# ============================================================
# Búsqueda semántica general
# ============================================================


def test_semantic_search():
    """Verifica que la búsqueda devuelva fragmentos válidos."""
    results = search_similar_news(
        "¿Qué riesgos tiene la inteligencia artificial?",
        limit=3,
    )

    assert len(results) == 3

    required_fields = {
        "rss_news_id",
        "title",
        "chunk_index",
        "chunk_text",
        "url",
        "published_at",
        "cosine_similarity",
    }

    assert required_fields.issubset(results[0].keys())

    assert all(
        result["chunk_text"].strip()
        for result in results
    )


def test_semantic_search_order():
    """Verifica el orden descendente de similitud."""
    results = search_similar_news(
        "Inteligencia artificial y empleo",
        limit=5,
    )

    similarities = [
        result["cosine_similarity"]
        for result in results
    ]

    assert similarities == sorted(similarities, reverse=True)


@pytest.mark.parametrize("limit", [0, -1, 21])
def test_semantic_search_invalid_limit(limit):
    """Verifica el rechazo de límites inválidos."""
    with pytest.raises(ValueError):
        search_similar_news(
            "inteligencia artificial",
            limit=limit,
        )


@pytest.mark.parametrize("query_text", ["", "   "])
def test_semantic_search_empty_query(query_text):
    """Verifica el rechazo de consultas vacías."""
    with pytest.raises(ValueError):
        search_similar_news(query_text)


def test_semantic_search_limit():
    """Verifica que se respete la cantidad solicitada."""
    results = search_similar_news(
        "Avances tecnológicos",
        limit=2,
    )

    assert len(results) == 2


# ============================================================
# Búsqueda semántica temática
# ============================================================


def test_topic_search():
    """Verifica la estructura de la búsqueda temática."""
    results = search_topic_news(
        TEST_QUERY,
        topic=TEST_TOPIC,
    )

    assert results["topic"] == TEST_TOPIC
    assert len(results["main_results"]) == 3
    assert len(results["complementary_results"]) <= 1


def test_topic_search_relevance():
    """Verifica la clasificación temática de los resultados."""
    results = search_topic_news(
        TEST_QUERY,
        topic=TEST_TOPIC,
    )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT rss_news_id
                FROM nli_news
                WHERE topic = %s
                  AND (keyword_match OR nli_recovered);
                """,
                (TEST_TOPIC,),
            )

            relevant_ids = {
                row[0]
                for row in cursor.fetchall()
            }

    assert all(
        result["rss_news_id"] in relevant_ids
        for result in results["main_results"]
    )

    assert all(
        result["rss_news_id"] not in relevant_ids
        for result in results["complementary_results"]
    )


def test_topic_search_complementary_threshold(monkeypatch):
    """Verifica que se respete el umbral configurado internamente."""
    monkeypatch.setattr(
        semantic_repository,
        "COMPLEMENTARY_MIN_SIMILARITY",
        0.99,
    )

    results = search_topic_news(
        TEST_QUERY,
        topic=TEST_TOPIC,
    )

    assert results["complementary_results"] == []


@pytest.mark.parametrize("limit", [0, -1, 21])
def test_topic_search_invalid_limit(limit):
    """Verifica el rechazo de límites inválidos."""
    with pytest.raises(ValueError):
        search_topic_news(
            TEST_QUERY,
            topic=TEST_TOPIC,
            limit=limit,
        )


@pytest.mark.parametrize("query_text", ["", "   "])
def test_topic_search_empty_query(query_text):
    """Verifica el rechazo de consultas vacías."""
    with pytest.raises(ValueError):
        search_topic_news(
            query_text,
            topic=TEST_TOPIC,
        )


def test_topic_search_unknown_topic():
    """Verifica el rechazo de temáticas sin clasificación NLI."""
    with pytest.raises(ValueError, match="clasificaciones NLI"):
        search_topic_news(
            "noticias sobre energía",
            topic="energia",
        )


@pytest.mark.parametrize("topic", ["", "   "])
def test_topic_search_empty_topic(topic):
    """Verifica el rechazo de temáticas vacías."""
    with pytest.raises(
        ValueError,
        match="temática no puede estar vacía",
    ):
        search_topic_news(
            TEST_QUERY,
            topic=topic,
        )


def test_topic_search_requires_topic():
    """Verifica que el argumento de temática sea obligatorio."""
    with pytest.raises(TypeError):
        search_topic_news(TEST_QUERY)


def test_topic_search_rejects_external_threshold():
    """Verifica que el umbral no pueda modificarse por argumento."""
    with pytest.raises(TypeError):
        search_topic_news(
            TEST_QUERY,
            topic=TEST_TOPIC,
            min_similarity=0.2,
        )
