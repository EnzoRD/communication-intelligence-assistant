
"""Repositorio de consultas de búsqueda semántica sobre noticias."""

from pgvector.psycopg import register_vector

from src.database.connection import get_connection
from src.embeddings.embedding_service import MODEL_NAME, encode_query


# Umbral inicial para recuperar noticias complementarias.
# Este valor deberá evaluarse experimentalmente.
COMPLEMENTARY_MIN_SIMILARITY = 0.75


def search_similar_news(
    query_text: str,
    limit: int = 5,
) -> list[dict]:
    """Busca fragmentos de noticias mediante similitud semántica.

    Args:
        query_text: Consulta en lenguaje natural.
        limit: Cantidad máxima de fragmentos recuperados.

    Returns:
        Lista de fragmentos ordenados por similitud coseno.

    Raises:
        ValueError: Si los parámetros son inválidos.
    """
    if not 1 <= limit <= 20:
        raise ValueError("El límite debe estar entre 1 y 20.")

    query_embedding = encode_query(query_text)

    query = """
        SELECT
            n.rss_news_id,
            n.title,
            c.chunk_index,
            c.chunk_text,
            n.url,
            n.published_at,
            1 - (c.embedding <=> %s) AS cosine_similarity
        FROM rss_news_chunks AS c
        JOIN rss_news AS n
            ON n.rss_news_id = c.fk_rss_news_id
        WHERE c.model_name = %s
        ORDER BY c.embedding <=> %s
        LIMIT %s;
    """

    with get_connection() as connection:
        register_vector(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (
                    query_embedding,
                    MODEL_NAME,
                    query_embedding,
                    limit,
                ),
            )

            columns = [
                column.name for column in cursor.description
            ]
            rows = cursor.fetchall()

    return [dict(zip(columns, row)) for row in rows]


def search_topic_news(
    query_text: str,
    topic: str,
    limit: int = 3,
) -> dict:
    """Recupera noticias principales y complementarias por similitud.

    La búsqueda principal utiliza las noticias seleccionadas
    mediante palabras clave o NLI para la temática indicada.

    La búsqueda complementaria utiliza noticias no seleccionadas
    por ese filtro y aplica un umbral mínimo de similitud coseno.

    Args:
        query_text: Consulta en lenguaje natural.
        topic: Temática obligatoria previamente evaluada mediante NLI.
        limit: Cantidad máxima de fragmentos principales.

    Returns:
        Diccionario con temática, resultados principales
        y resultados complementarios.

    Raises:
        ValueError: Si los parámetros son inválidos o la temática
            no tiene clasificaciones NLI disponibles.
    """
    if not query_text or not query_text.strip():
        raise ValueError("La consulta no puede estar vacía.")

    if not topic or not topic.strip():
        raise ValueError("La temática no puede estar vacía.")

    if not 1 <= limit <= 20:
        raise ValueError("El límite debe estar entre 1 y 20.")

    topic = topic.strip()

    # Verificar que la temática tenga clasificaciones NLI disponibles.
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM nli_news
                    WHERE topic = %s
                );
                """,
                (topic,),
            )
            topic_exists = cursor.fetchone()[0]

    if not topic_exists:
        raise ValueError(
            f"La temática '{topic}' no tiene "
            "clasificaciones NLI disponibles."
        )

    # Generar el embedding de la consulta.
    query_embedding = encode_query(query_text)

    base_query = """
        SELECT
            n.rss_news_id,
            n.title,
            c.chunk_index,
            c.chunk_text,
            n.url,
            n.published_at,
            1 - (c.embedding <=> %s) AS cosine_similarity
        FROM rss_news_chunks AS c
        JOIN rss_news AS n
            ON n.rss_news_id = c.fk_rss_news_id
        WHERE
            c.model_name = %s
            AND {relevance_condition}
            {similarity_condition}
        ORDER BY c.embedding <=> %s
        LIMIT %s;
    """

    relevance_condition = """
        EXISTS (
            SELECT 1
            FROM nli_news AS nl
            WHERE nl.rss_news_id = n.rss_news_id
              AND nl.topic = %s
              AND (nl.keyword_match OR nl.nli_recovered)
        )
    """

    # Noticias seleccionadas por el filtro temático.
    main_query = base_query.format(
        relevance_condition=relevance_condition,
        similarity_condition="",
    )

    # Noticias no seleccionadas por el filtro temático.
    complementary_query = base_query.format(
        relevance_condition=f"NOT ({relevance_condition})",
        similarity_condition="""
            AND 1 - (c.embedding <=> %s) >= %s
        """,
    )

    with get_connection() as connection:
        register_vector(connection)

        with connection.cursor() as cursor:
            # Recuperar los fragmentos principales.
            cursor.execute(
                main_query,
                (
                    query_embedding,
                    MODEL_NAME,
                    topic,
                    query_embedding,
                    limit,
                ),
            )

            columns = [
                column.name for column in cursor.description
            ]
            main_results = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

            # Recuperar como máximo un fragmento complementario.
            cursor.execute(
                complementary_query,
                (
                    query_embedding,
                    MODEL_NAME,
                    topic,
                    query_embedding,
                    COMPLEMENTARY_MIN_SIMILARITY,
                    query_embedding,
                    1,
                ),
            )

            columns = [
                column.name for column in cursor.description
            ]
            complementary_results = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

    return {
        "topic": topic,
        "main_results": main_results,
        "complementary_results": complementary_results,
    }
