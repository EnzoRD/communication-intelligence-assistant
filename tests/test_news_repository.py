from src.database.repositories.news_repository import get_latest_news, get_news_by_id
import pytest

def test_get_latest_news():
    """Verifica la recuperación de noticias desde PostgreSQL."""

    news = get_latest_news(limit=5)

    assert isinstance(news, list)
    assert len(news) <= 5
    assert len(news) > 0, "No se recuperaron noticias."

    required_fields = {
        "rss_news_id",
        "title",
        "published_at",
        "url",
    }

    for article in news:
        assert required_fields.issubset(article.keys())

    print(f"Prueba superada: {len(news)} noticias recuperadas.")

    for article in news:
        print(f"[{article['rss_news_id']}] {article['title']}")
        



@pytest.mark.parametrize("limit", [0, -1, 101])
def test_get_latest_news_invalid_limit(limit):
    """Verifica que se rechacen límites fuera del rango permitido."""
    with pytest.raises(ValueError):
        get_latest_news(limit=limit)


def test_get_latest_news_limit():
    """Verifica que la consulta respete el límite solicitado."""
    assert len(get_latest_news(limit=3)) <= 3

from src.database.repositories.news_repository import search_news


def test_search_news():
    """Verifica la búsqueda textual de noticias."""
    results = search_news("Google", limit=3)

    assert isinstance(results, list)
    assert 0 < len(results) <= 3

    required_fields = {
        "rss_news_id", "title", "published_at", "url"
    }

    for news in results:
        assert required_fields.issubset(news.keys())


@pytest.mark.parametrize("limit", [0, -1, 101])
def test_search_news_invalid_limit(limit):
    """Verifica que se rechacen límites inválidos."""
    with pytest.raises(ValueError):
        search_news("Google", limit=limit)


@pytest.mark.parametrize("search_text", ["", "   "])
def test_search_news_empty_text(search_text):
    """Verifica que se rechacen búsquedas vacías."""
    with pytest.raises(ValueError):
        search_news(search_text)

from datetime import date


def test_search_news_by_source():
    """Verifica que las noticias correspondan a la fuente solicitada."""
    results = search_news(source_id=7, limit=5)

    assert len(results) > 0
    assert all(news["fk_rss_source_id"] == 7 for news in results)


def test_search_news_by_date():
    """Verifica que las noticias estén dentro del período indicado."""
    results = search_news(
        date_from=date(2026, 8, 26),
        date_to=date(2026, 8, 27),
        limit=10,
    )

    assert len(results) > 0
    assert all(
        date(2026, 8, 26) <= news["published_at"].date() <= date(2026, 8, 27)
        for news in results
    )


def test_search_news_combined_filters():
    """Verifica la combinación de texto, fuente y fechas."""
    results = search_news(
        search_text="Google",
        source_id=1,
        date_from=date(2026, 8, 27),
        date_to=date(2026, 8, 27),
        limit=5,
    )

    assert len(results) > 0
    assert all(news["fk_rss_source_id"] == 1 for news in results)


@pytest.mark.parametrize(
    "filters",
    [
        {},
        {"source_id": 0},
        {"source_id": -1},
        {"date_from": date(2026, 8, 28), "date_to": date(2026, 8, 26)},
    ],
)
def test_search_news_invalid_filters(filters):
    """Verifica el rechazo de filtros inválidos."""
    with pytest.raises(ValueError):
        search_news(**filters)
        

def test_get_news_by_id():
    """Verifica la recuperación de una noticia completa."""
    news = get_news_by_id(3)

    assert news is not None
    assert news["rss_news_id"] == 3

    required_fields = {
        "rss_news_id",
        "title",
        "description",
        "content",
        "url",
        "author",
        "published_at",
        "source_name",
    }

    assert required_fields.issubset(news.keys())
    assert len(news["content"]) > 0
    assert news["source_name"] == "Infobae - Tecno"


def test_get_news_by_id_not_found():
    """Verifica el comportamiento ante una noticia inexistente."""
    assert get_news_by_id(999999999) is None


@pytest.mark.parametrize("rss_news_id", [0, -1])
def test_get_news_by_id_invalid_id(rss_news_id):
    """Verifica el rechazo de identificadores inválidos."""
    with pytest.raises(ValueError):
        get_news_by_id(rss_news_id)

if __name__ == "__main__":
    test_get_latest_news()