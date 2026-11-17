
"""Consultas analíticas sobre las noticias almacenadas."""

from datetime import date

from src.database.connection import get_connection


def get_news_count_by_source(
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[dict]:
    """Obtiene la cantidad de noticias por fuente RSS.

    Args:
        date_from: Fecha inicial inclusiva.
        date_to: Fecha final inclusiva.

    Returns:
        Lista de fuentes con sus respectivas cantidades de noticias.
    """
    if date_from and date_to and date_from > date_to:
        raise ValueError("La fecha inicial no puede superar la fecha final.")

    query = """
        SELECT
            s.rss_source_id,
            s.name AS source_name,
            COUNT(n.rss_news_id) AS news_count
        FROM rss_sources AS s
        LEFT JOIN rss_news AS n
            ON n.fk_rss_source_id = s.rss_source_id
            AND (%s::date IS NULL OR n.published_at >= %s::date)
            AND (
                %s::date IS NULL
                OR n.published_at < (%s::date + INTERVAL '1 day')
            )
        GROUP BY s.rss_source_id, s.name
        ORDER BY news_count DESC, s.rss_source_id;
    """

    parameters = (
        date_from, date_from,
        date_to, date_to,
    )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)
            columns = [column.name for column in cursor.description]
            rows = cursor.fetchall()

    return [dict(zip(columns, row)) for row in rows]



def get_sentiment_distribution(
    source_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[dict]:
    """Obtiene la distribución de sentimientos de las noticias.

    Permite filtrar por fuente RSS y período de publicación.
    Sin filtros, analiza todo el histórico disponible.

    Args:
        source_id: Identificador opcional de la fuente RSS.
        date_from: Fecha inicial inclusiva.
        date_to: Fecha final inclusiva.

    Returns:
        Cantidad y porcentaje de noticias por sentimiento.
    """
    if source_id is not None and source_id <= 0:
        raise ValueError("El identificador de fuente debe ser positivo.")

    if date_from and date_to and date_from > date_to:
        raise ValueError("La fecha inicial no puede superar la fecha final.")

    query = """
        SELECT
            s.sentiment,
            COUNT(*) AS news_count,
            ROUND(
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
                2
            ) AS percentage
        FROM rss_sentiments AS s
        JOIN rss_news AS n
            ON n.rss_news_id = s.fk_rss_news_id
        WHERE
            (%s::bigint IS NULL OR n.fk_rss_source_id = %s)
            AND (%s::date IS NULL OR n.published_at >= %s::date)
            AND (
                %s::date IS NULL
                OR n.published_at < (%s::date + INTERVAL '1 day')
            )
        GROUP BY s.sentiment
        ORDER BY news_count DESC;
    """

    parameters = (
        source_id, source_id,
        date_from, date_from,
        date_to, date_to,
    )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)
            columns = [column.name for column in cursor.description]
            rows = cursor.fetchall()

    return [dict(zip(columns, row)) for row in rows]


def get_top_entities(
    entity_type: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Obtiene las entidades identificadas en más noticias.

    Args:
        entity_type: Categoría opcional de entidad.
        limit: Número máximo de resultados (entre 1 y 100).

    Returns:
        Ranking de entidades según cantidad de noticias distintas.
    """
    allowed_types = {
        "person",
        "organization",
        "location",
        "product",
    }

    if entity_type is not None and entity_type not in allowed_types:
        raise ValueError("Tipo de entidad no válido.")

    if not 1 <= limit <= 100:
        raise ValueError("El límite debe estar entre 1 y 100.")

    query = """
        SELECT
            e.entity_text,
            e.entity_type,
            COUNT(DISTINCT e.fk_rss_news_id) AS news_count
        FROM rss_entities AS e
        WHERE (%s::text IS NULL OR e.entity_type = %s)
        GROUP BY e.entity_text, e.entity_type
        ORDER BY news_count DESC, e.entity_text
        LIMIT %s;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (entity_type, entity_type, limit),
            )
            columns = [column.name for column in cursor.description]
            rows = cursor.fetchall()

    return [dict(zip(columns, row)) for row in rows]

def get_entity_sentiment_distribution(
    entity_text: str,
    entity_type: str | None = None,
) -> list[dict]:
    """Obtiene la distribución de sentimientos de noticias que mencionan una entidad.

    Args:
        entity_text: Nombre de la entidad que se desea consultar.
        entity_type: Categoría NER opcional.

    Returns:
        Cantidad de noticias por sentimiento.
    """
    allowed_types = {"person", "organization", "location", "product"}

    entity_text = entity_text.strip()

    if not entity_text:
        raise ValueError("El nombre de la entidad no puede estar vacío.")

    if entity_type is not None and entity_type not in allowed_types:
        raise ValueError("Tipo de entidad no válido.")

    query = """
        SELECT
            s.sentiment,
            COUNT(DISTINCT n.rss_news_id) AS news_count
        FROM rss_news AS n
        JOIN rss_entities AS e
            ON e.fk_rss_news_id = n.rss_news_id
        JOIN rss_sentiments AS s
            ON s.fk_rss_news_id = n.rss_news_id
        WHERE
            LOWER(e.entity_text) = LOWER(%s)
            AND (%s::text IS NULL OR e.entity_type = %s)
        GROUP BY s.sentiment
        ORDER BY news_count DESC, s.sentiment;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (entity_text, entity_type, entity_type),
            )
            columns = [column.name for column in cursor.description]
            rows = cursor.fetchall()

    return [dict(zip(columns, row)) for row in rows]