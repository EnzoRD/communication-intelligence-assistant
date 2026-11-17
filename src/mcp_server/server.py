from datetime import date

"""Servidor MCP del Communication Intelligence Assistant."""

from mcp.server.mcpserver import MCPServer

from src.database.repositories.news_repository import (
    get_latest_news,
    search_news,
    get_news_by_id,
)

from src.database.repositories.analytics_repository import (
    get_news_count_by_source,
    get_sentiment_distribution,
    get_top_entities,
    get_entity_sentiment_distribution,
)

from src.database.repositories.semantic_repository import (
    search_similar_news,
    search_topic_news,
)

mcp = MCPServer("Communication Intelligence Assistant")


@mcp.tool()
def latest_news(limit: int = 10) -> list[dict]:
    """Recupera las noticias más recientes de la base de datos.

    Args:
        limit: Cantidad máxima de noticias (entre 1 y 100).

    Returns:
        Lista de noticias con identificador, título, fecha y URL.
    """
    return get_latest_news(limit=limit)

@mcp.tool()
def search_news_by_text(
    search_text: str | None = None,
    source_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 10,
) -> list[dict]:
    """Busca noticias por texto, fuente y período de publicación.

    Utiliza esta herramienta cuando el usuario solicita noticias
    sobre un tema, de una fuente específica o de un período.

    No utilizar latest_news si el usuario especifica filtros.

    Args:
        search_text: Palabra o frase que debe aparecer en la noticia.
        source_id: Identificador de la fuente RSS.
        date_from: Fecha inicial inclusiva (AAAA-MM-DD).
        date_to: Fecha final inclusiva (AAAA-MM-DD).
        limit: Cantidad máxima de resultados, entre 1 y 100.

    Returns:
        Noticias coincidentes con título, fecha, URL y fuente.
    """
    return search_news(
        search_text=search_text,
        source_id=source_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )

@mcp.tool()
def news_count_by_source(
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[dict]:
    """Obtiene la cantidad de noticias almacenadas por fuente RSS.

    IMPORTANTE:
    - Los parámetros date_from y date_to son OPCIONALES.
    - Si el usuario no especifica fechas, ejecutar SIN argumentos.
    - Sin fechas, la herramienta consulta TODO el histórico.
    - No solicitar fechas al usuario salvo que necesite filtrar un período.
    - Utilizar esta herramienta para estadísticas y comparaciones
      de cantidad de noticias por medio.

    Args:
        date_from: Fecha inicial opcional (AAAA-MM-DD).
        date_to: Fecha final opcional (AAAA-MM-DD).

    Returns:
        Fuentes con identificador, nombre y cantidad de noticias.
    """
    return get_news_count_by_source(
        date_from=date_from,
        date_to=date_to,
    )
    
@mcp.tool()
def news_count_by_source() -> list[dict]:
    """Obtiene la cantidad de noticias por fuente de TODO el histórico.

    No aplica filtros temporales.
    Utilizar cuando el usuario no indique un período específico.
    """
    return get_news_count_by_source()

@mcp.tool()
def news_count_by_source_period(
    date_from: date,
    date_to: date,
) -> list[dict]:
    """Obtiene estadísticas de noticias por fuente dentro de un período.

    Utilizar exclusivamente cuando el usuario indique fechas
    o solicite un período temporal específico.
    """
    return get_news_count_by_source(
        date_from=date_from,
        date_to=date_to,
    )
    
@mcp.tool()
def sentiment_distribution(
    source_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[dict]:
    """Obtiene la distribución de sentimientos de las noticias.

    Utilizar esta herramienta para consultas sobre cantidades,
    porcentajes o proporciones de noticias positivas, neutrales
    y negativas.

    IMPORTANTE:
    - Todos los parámetros son opcionales.
    - Sin argumentos, analiza todo el histórico.
    - Las fechas filtran por publicación, no por procesamiento.
    - No solicitar fechas si el usuario no especifica un período.
    - Las categorías representan el sentimiento general de la
      noticia, no necesariamente hacia una entidad particular.

    Args:
        source_id: ID opcional de la fuente RSS.
        date_from: Fecha inicial inclusiva (AAAA-MM-DD).
        date_to: Fecha final inclusiva (AAAA-MM-DD).

    Returns:
        Cantidad y porcentaje de noticias por sentimiento.
    """
    return get_sentiment_distribution(
        source_id=source_id,
        date_from=date_from,
        date_to=date_to,
    )

@mcp.tool()
def top_entities(
    entity_type: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Obtiene las entidades detectadas en más noticias.

    Utilizar cuando el usuario pregunta qué personas, organizaciones,
    lugares o productos aparecen con mayor frecuencia en las noticias.

    IMPORTANTE:
    - Sin entity_type, consulta todas las categorías.
    - entity_type puede ser: person, organization, location o product.
    - La frecuencia representa noticias distintas, no menciones totales.
    - Son predicciones del modelo NER, no entidades verificadas manualmente.
    - No utilizar latest_news para responder rankings de entidades.

    Args:
        entity_type: Categoría opcional de entidad.
        limit: Número máximo de resultados (entre 1 y 100).

    Returns:
        Ranking de entidades con categoría y cantidad de noticias.
    """
    return get_top_entities(
        entity_type=entity_type,
        limit=limit,
    )

@mcp.tool()
def entity_sentiment_distribution(
    entity_text: str,
    entity_type: str | None = None,
) -> list[dict]:
    """Obtiene los sentimientos de noticias que mencionan una entidad.

    Utilizar cuando el usuario pregunta por la distribución de
    sentimientos de noticias relacionadas con una persona,
    organización, lugar o producto específico.

    IMPORTANTE:
    - entity_text es obligatorio y debe coincidir con el nombre
      de la entidad detectada por NER.
    - entity_type es opcional.
    - Se cuentan noticias distintas.
    - El sentimiento corresponde a la noticia completa, NO
      necesariamente a la opinión sobre la entidad.
    - No inventar resultados si la entidad no está registrada.

    Args:
        entity_text: Nombre de la entidad, por ejemplo, Google.
        entity_type: Categoría opcional: person, organization,
            location o product.

    Returns:
        Cantidad de noticias positivas, neutrales y negativas
        que mencionan la entidad.
    """
    return get_entity_sentiment_distribution(
        entity_text=entity_text,
        entity_type=entity_type,
    )

@mcp.tool()
def news_by_id(rss_news_id: int) -> dict | None:
    """Recupera una noticia completa mediante su identificador.

    Utilizar cuando el usuario solicita detalles, explicaciones
    o resúmenes de una noticia específica.

    IMPORTANTE:
    - Requiere el identificador de una noticia existente.
    - Devuelve título, descripción, contenido completo y metadatos.
    - Utilizar el contenido recuperado para fundamentar respuestas.
    - Citar la URL original de la noticia.
    - No inventar información que no esté presente en el contenido.

    Args:
        rss_news_id: Identificador único de la noticia.

    Returns:
        Datos completos de la noticia o None si no existe.
    """
    return get_news_by_id(rss_news_id)



@mcp.tool()
def semantic_search(
    query_text: str,
    limit: int = 5,
) -> list[dict]:
    """Busca fragmentos de noticias mediante similitud semántica.

    Utilizar cuando el usuario realiza preguntas abiertas sobre
    temas, acontecimientos o conceptos presentes en las noticias.

    La búsqueda utiliza embeddings multilingües E5 y pgvector.

    IMPORTANTE:
    - Recupera fragmentos, no necesariamente noticias únicas.
    - Los resultados están ordenados por similitud coseno.
    - El sentimiento y la relevancia temática no se infieren
      de la puntuación de similitud.
    - Responder únicamente con información respaldada por los
      fragmentos recuperados.
    - Citar las URL originales de las noticias.
    - Si los resultados no permiten responder, indicar que
      no se encontró información suficiente.

    Args:
        query_text: Pregunta o texto de búsqueda en lenguaje natural.
        limit: Cantidad máxima de fragmentos (entre 1 y 20).

    Returns:
        Fragmentos recuperados con título, contenido,
        URL, fecha y puntuación de similitud coseno.
    """
    return search_similar_news(
        query_text=query_text,
        limit=limit,
    )



@mcp.tool()
def topic_semantic_search(
    query_text: str,
    topic: str,
    limit: int = 3,
) -> dict:
    """Busca noticias de una temática previamente clasificada.

    Utilizar cuando el usuario consulta sobre una temática
    de seguimiento identificada en el sistema.

    Recupera dos grupos:
    - Principales: noticias seleccionadas mediante keywords o NLI.
    - Complementarios: noticias no seleccionadas por el filtro
      temático, pero relacionadas mediante similitud semántica.

    IMPORTANTE:
    - La temática es obligatoria y debe existir en nli_news.
    - No asumir una temática predeterminada.
    - No inventar temáticas ni clasificaciones.
    - El umbral complementario se controla internamente.
    - Priorizar los resultados principales.
    - Presentar los complementarios por separado, indicando
      que podrían no pertenecer a la temática.
    - Citar las URL originales de las noticias.
    - No interpretar la similitud coseno como probabilidad.
    - No inventar información ausente de los fragmentos.

    Args:
        query_text: Consulta en lenguaje natural.
        topic: Identificador exacto de una temática clasificada.
        limit: Cantidad máxima de fragmentos principales (1 a 20).

    Returns:
        Resultados principales y complementarios con sus fuentes.
    """
    return search_topic_news(
        query_text=query_text,
        topic=topic,
        limit=limit,
    )



if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
        stateless_http=True,
        json_response=True,
    )