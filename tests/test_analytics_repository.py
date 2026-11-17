from datetime import date

import pytest

from src.database.repositories.analytics_repository import (
    get_news_count_by_source,
    get_sentiment_distribution,
    get_top_entities,
    get_entity_sentiment_distribution,
)


def test_news_count_by_source():
    """Verifica la cantidad de noticias por fuente."""
    results = get_news_count_by_source()

    assert len(results) == 7
    assert sum(row["news_count"] for row in results) == 186

    assert all(
        {"rss_source_id", "source_name", "news_count"}.issubset(row)
        for row in results
    )


def test_news_count_by_source_date_filter():
    """Verifica que el filtro temporal funcione correctamente."""
    results = get_news_count_by_source(
        date_from=date(2026, 8, 27),
        date_to=date(2026, 8, 27),
    )

    assert len(results) == 7
    assert 0 < sum(row["news_count"] for row in results) <= 186


def test_news_count_by_source_without_matches():
    """Verifica que las fuentes sin noticias tengan conteo cero."""
    results = get_news_count_by_source(
        date_from=date(2030, 1, 1),
        date_to=date(2030, 1, 31),
    )

    assert len(results) == 7
    assert all(row["news_count"] == 0 for row in results)


def test_news_count_by_source_invalid_dates():
    """Verifica el rechazo de períodos inválidos."""
    with pytest.raises(ValueError):
        get_news_count_by_source(
            date_from=date(2026, 12, 31),
            date_to=date(2026, 1, 1),
        )
        
        
def test_sentiment_distribution():
    """Verifica la distribución de sentimientos del histórico."""
    results = get_sentiment_distribution()

    assert len(results) == 3
    assert sum(row["news_count"] for row in results) == 186
    assert {row["sentiment"] for row in results} == {
        "positive", "neutral", "negative"
    }
    assert abs(sum(row["percentage"] for row in results) - 100) <= 0.01


def test_sentiment_distribution_by_source():
    """Verifica el filtro por fuente RSS."""
    results = get_sentiment_distribution(source_id=1)

    assert sum(row["news_count"] for row in results) == 100


def test_sentiment_distribution_by_date():
    """Verifica el filtro por período de publicación."""
    results = get_sentiment_distribution(
        date_from=date(2026, 8, 26),
        date_to=date(2026, 8, 27),
    )

    assert sum(row["news_count"] for row in results) == 100


def test_sentiment_distribution_without_matches():
    """Verifica períodos sin noticias."""
    results = get_sentiment_distribution(
        date_from=date(2030, 1, 1),
        date_to=date(2030, 1, 31),
    )

    assert results == []


@pytest.mark.parametrize("source_id", [0, -1])
def test_sentiment_distribution_invalid_source(source_id):
    """Verifica el rechazo de identificadores inválidos."""
    with pytest.raises(ValueError):
        get_sentiment_distribution(source_id=source_id)


def test_sentiment_distribution_invalid_dates():
    """Verifica el rechazo de períodos inválidos."""
    with pytest.raises(ValueError):
        get_sentiment_distribution(
            date_from=date(2026, 12, 31),
            date_to=date(2026, 1, 1),
        )
        
def test_top_entities():
    """Verifica el ranking general de entidades."""
    results = get_top_entities(limit=5)

    assert len(results) == 5
    assert results[0]["entity_text"] == (
        "Agencia de Noticias Científicas de la UNQ"
    )
    assert results[0]["news_count"] == 30

    assert all(
        {"entity_text", "entity_type", "news_count"}.issubset(row)
        for row in results
    )

    assert all(
        results[i]["news_count"] >= results[i + 1]["news_count"]
        for i in range(len(results) - 1)
    )


@pytest.mark.parametrize(
    "entity_type",
    ["person", "organization", "location", "product"],
)
def test_top_entities_by_type(entity_type):
    """Verifica el filtro por categoría NER."""
    results = get_top_entities(entity_type=entity_type, limit=5)

    assert len(results) > 0
    assert all(row["entity_type"] == entity_type for row in results)


@pytest.mark.parametrize("entity_type", ["invalid", "technology", ""])
def test_top_entities_invalid_type(entity_type):
    """Verifica el rechazo de categorías no permitidas."""
    with pytest.raises(ValueError):
        get_top_entities(entity_type=entity_type)


@pytest.mark.parametrize("limit", [0, -1, 101])
def test_top_entities_invalid_limit(limit):
    """Verifica el rechazo de límites inválidos."""
    with pytest.raises(ValueError):
        get_top_entities(limit=limit)
        
def test_entity_sentiment_distribution():
    """Verifica los sentimientos de noticias que mencionan Google."""
    results = get_entity_sentiment_distribution(
        "Google", "organization"
    )

    counts = {row["sentiment"]: row["news_count"] for row in results}

    assert counts == {
        "neutral": 3,
        "negative": 1,
        "positive": 1,
    }


def test_entity_sentiment_distribution_without_type():
    """Verifica la consulta sin especificar categoría NER."""
    results = get_entity_sentiment_distribution("Google")

    assert isinstance(results, list)
    assert all(row["news_count"] > 0 for row in results)


def test_entity_sentiment_distribution_not_found():
    """Verifica el comportamiento ante una entidad inexistente."""
    results = get_entity_sentiment_distribution(
        "EntidadInexistenteXYZ123"
    )

    assert results == []


@pytest.mark.parametrize("entity_text", ["", "   "])
def test_entity_sentiment_distribution_empty_text(entity_text):
    """Verifica el rechazo de nombres vacíos."""
    with pytest.raises(ValueError):
        get_entity_sentiment_distribution(entity_text)


@pytest.mark.parametrize("entity_type", ["invalid", "technology", ""])
def test_entity_sentiment_distribution_invalid_type(entity_type):
    """Verifica el rechazo de categorías NER inválidas."""
    with pytest.raises(ValueError):
        get_entity_sentiment_distribution("Google", entity_type)