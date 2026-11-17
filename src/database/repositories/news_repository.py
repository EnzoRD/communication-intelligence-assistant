from src.database.connection import get_connection
from datetime import date


def get_latest_news(limit: int = 10) -> list[dict]:
    """Recupera las noticias más recientes desde PostgreSQL."""

    if not 1 <= limit <= 100:
        raise ValueError("El límite debe estar entre 1 y 100.")

    query = """
        SELECT
            rss_news_id,
            title,
            published_at,
            url
        FROM rss_news
        ORDER BY published_at DESC NULLS LAST, rss_news_id DESC
        LIMIT %s;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (limit,))
            columns = [column.name for column in cursor.description]
            rows = cursor.fetchall()

    return [dict(zip(columns, row)) for row in rows]



def search_news(
    search_text: str | None = None,
    source_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 10,
) -> list[dict]:
    """Busca noticias mediante filtros opcionales de texto, fuente y fecha.

    Args:
        search_text: Palabra o frase a buscar en la noticia.
        source_id: Identificador de la fuente RSS.
        date_from: Fecha inicial inclusiva.
        date_to: Fecha final inclusiva.
        limit: Cantidad máxima de resultados (entre 1 y 100).

    Returns:
        Lista de noticias que cumplen todos los filtros indicados.
    """
    if not 1 <= limit <= 100:
        raise ValueError("El límite debe estar entre 1 y 100.")

    if source_id is not None and source_id <= 0:
        raise ValueError("El identificador de fuente debe ser positivo.")

    if date_from and date_to and date_from > date_to:
        raise ValueError("La fecha inicial no puede superar la fecha final.")

    conditions = []
    parameters = []

    if search_text is not None:
        search_text = search_text.strip()

        if not search_text:
            raise ValueError("El texto de búsqueda no puede estar vacío.")

        conditions.append(
            "(title ILIKE %s OR description ILIKE %s OR content ILIKE %s)"
        )
        pattern = f"%{search_text}%"
        parameters.extend([pattern, pattern, pattern])

    if source_id is not None:
        conditions.append("fk_rss_source_id = %s")
        parameters.append(source_id)

    if date_from is not None:
        conditions.append("published_at >= %s::date")
        parameters.append(date_from)

    if date_to is not None:
        conditions.append("published_at < (%s::date + INTERVAL '1 day')")
        parameters.append(date_to)

    if not conditions:
        raise ValueError("Se requiere al menos un filtro de búsqueda.")

    query = """
        SELECT
            rss_news_id,
            title,
            published_at,
            url,
            fk_rss_source_id
        FROM rss_news
        WHERE
    """ + " AND ".join(conditions) + """
        ORDER BY published_at DESC NULLS LAST, rss_news_id DESC
        LIMIT %s;
    """

    parameters.append(limit)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, tuple(parameters))
            columns = [column.name for column in cursor.description]
            rows = cursor.fetchall()

    return [dict(zip(columns, row)) for row in rows]


def get_news_by_id(rss_news_id: int) -> dict | None:
    """Recupera una noticia completa mediante su identificador.

    Args:
        rss_news_id: Identificador de la noticia.

    Returns:
        Diccionario con los datos de la noticia o None
        si el identificador no existe.
    """
    if rss_news_id <= 0:
        raise ValueError("El identificador debe ser positivo.")

    query = """
        SELECT
            n.rss_news_id,
            n.title,
            n.description,
            n.content,
            n.url,
            n.author,
            n.published_at,
            s.name AS source_name
        FROM rss_news AS n
        JOIN rss_sources AS s
            ON s.rss_source_id = n.fk_rss_source_id
        WHERE n.rss_news_id = %s;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (rss_news_id,))
            row = cursor.fetchone()

            if row is None:
                return None

            columns = [column.name for column in cursor.description]

    return dict(zip(columns, row))
