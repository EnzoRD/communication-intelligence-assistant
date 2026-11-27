SELECT COUNT(*) AS total_news
FROM rss_news;

SELECT COUNT(*) AS total_news_keywords
FROM rss_news_keywords;


SELECT
    is_processed,
    COUNT(*) AS total
FROM rss_raw
GROUP BY is_processed;


SELECT
    k.keyword,
    COUNT(*) AS news_count
FROM rss_news_keywords rnk
INNER JOIN keywords k
    ON rnk.fk_keyword_id = k.keyword_id
GROUP BY
    k.keyword_id,
    k.keyword
ORDER BY news_count DESC;

INSERT INTO keywords (keyword, description, is_active)
VALUES
    -- Inteligencia artificial generativa
    ('IA generativa', 'Inteligencia artificial aplicada a la generación de contenido.', TRUE),
    ('inteligencia artificial generativa', 'Denominación completa de IA generativa.', TRUE),
    ('generative AI', 'Denominación en inglés de inteligencia artificial generativa.', TRUE),

    -- Aprendizaje profundo y redes neuronales
    ('deep learning', 'Técnicas de aprendizaje profundo.', TRUE),
    ('aprendizaje profundo', 'Denominación en español de deep learning.', TRUE),
    ('redes neuronales', 'Modelos computacionales basados en redes neuronales.', TRUE),
    ('neural networks', 'Denominación en inglés de redes neuronales.', TRUE),

    -- Procesamiento del lenguaje natural
    ('procesamiento del lenguaje natural', 'Tecnologías de procesamiento de lenguaje natural.', TRUE),
    ('NLP', 'Abreviatura de Natural Language Processing.', TRUE),

    -- Modelos y asistentes de inteligencia artificial
    ('ChatGPT', 'Asistente de inteligencia artificial de OpenAI.', TRUE),
    ('Gemini', 'Familia de modelos y asistentes de IA de Google.', TRUE),
    ('Claude', 'Familia de modelos y asistentes de IA de Anthropic.', TRUE),
    ('Copilot', 'Asistentes de inteligencia artificial de Microsoft y otros productos.', TRUE),
    ('DeepSeek', 'Familia de modelos de inteligencia artificial.', TRUE),

    -- Conceptos y aplicaciones
    ('agentes de IA', 'Sistemas de inteligencia artificial basados en agentes.', TRUE),
    ('agentes inteligentes', 'Agentes autónomos y sistemas inteligentes.', TRUE),
    ('visión por computadora', 'Aplicaciones de inteligencia artificial para el análisis de imágenes.', TRUE),
    ('computer vision', 'Denominación en inglés de visión por computadora.', TRUE)
ON CONFLICT DO NOTHING;

SELECT
    conname,
    pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE conrelid = 'rss_sentiments'::regclass;

SELECT
    con.conname AS constraint_name,
    con.contype AS constraint_type,
    pg_get_constraintdef(con.oid) AS definition
FROM pg_constraint con
WHERE con.conrelid = 'rss_entities'::regclass;


ALTER TABLE rss_entities
ADD CONSTRAINT uq_rss_entities
UNIQUE (
    fk_rss_news_id,
    entity_text,
    entity_type,
    model_name
);



SELECT *
FROM rss_sources
ORDER BY rss_source_id;

SELECT
    s.rss_source_id,
    COUNT(n.rss_news_id) AS total_noticias
FROM rss_sources s
LEFT JOIN rss_news n
    ON n.fk_rss_source_id = s.rss_source_id
GROUP BY s.rss_source_id
ORDER BY total_noticias DESC;


SELECT COUNT(*) AS total_noticias
FROM rss_news;

SELECT
    s.rss_source_id,
    s.name AS fuente,
    COUNT(n.rss_news_id) AS total_noticias
FROM rss_sources AS s
LEFT JOIN rss_news AS n
    ON n.fk_rss_source_id = s.rss_source_id
GROUP BY
    s.rss_source_id,
    s.name
ORDER BY total_noticias DESC;

SELECT
    MIN(published_at) AS primera_publicacion,
    MAX(published_at) AS ultima_publicacion,
    COUNT(*) FILTER (
        WHERE published_at IS NULL
    ) AS noticias_sin_fecha
FROM rss_news;




SELECT *
FROM rss_sentiments
LIMIT 5;

SELECT COUNT(*) AS total_registros
FROM rss_sentiments;

SELECT
    s.sentiment,
    COUNT(*) AS news_count,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    ) AS percentage
FROM rss_sentiments AS s
GROUP BY s.sentiment
ORDER BY news_count DESC;

SELECT
    COUNT(*) AS total_results,
    COUNT(DISTINCT fk_rss_news_id) AS unique_news,
    COUNT(*) FILTER (
        WHERE sentiment NOT IN ('positive', 'neutral', 'negative')
           OR sentiment IS NULL
    ) AS invalid_sentiments
FROM rss_sentiments;


SELECT
    entity_type,
    COUNT(*) AS total_entities,
    COUNT(DISTINCT fk_rss_news_id) AS news_count
FROM rss_entities
GROUP BY entity_type
ORDER BY total_entities DESC;

SELECT
    entity_text,
    entity_type,
    COUNT(DISTINCT fk_rss_news_id) AS news_count
FROM rss_entities
GROUP BY entity_text, entity_type
ORDER BY news_count DESC, entity_text
LIMIT 15;

SELECT
    s.sentiment,
    COUNT(DISTINCT n.rss_news_id) AS news_count
FROM rss_news AS n
JOIN rss_entities AS e
    ON e.fk_rss_news_id = n.rss_news_id
JOIN rss_sentiments AS s
    ON s.fk_rss_news_id = n.rss_news_id
WHERE
    e.entity_text ILIKE 'Google'
    AND e.entity_type = 'organization'
GROUP BY s.sentiment
ORDER BY news_count DESC;

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
WHERE n.rss_news_id = 3;


SELECT name, default_version, installed_version
FROM pg_available_extensions
WHERE name = 'vector';

SELECT
    version(),
    current_database(),
    current_user;

SELECT extname, extversion
FROM pg_extension
WHERE extname = 'vector';


CREATE TABLE IF NOT EXISTS rss_news_chunks (
    rss_news_chunk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fk_rss_news_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    model_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_rss_news_chunks_news
        FOREIGN KEY (fk_rss_news_id)
        REFERENCES rss_news (rss_news_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_rss_news_chunks
        UNIQUE (fk_rss_news_id, chunk_index, model_name),

    CONSTRAINT chk_rss_news_chunks_index
        CHECK (chunk_index >= 0),

    CONSTRAINT chk_rss_news_chunks_text
        CHECK (LENGTH(BTRIM(chunk_text)) > 0)
);

SELECT column_name, data_type, udt_name
FROM information_schema.columns
WHERE table_name = 'rss_news_chunks'
ORDER BY ordinal_position;

SELECT
    COUNT(*) AS total_chunks,
    COUNT(DISTINCT fk_rss_news_id) AS total_news,
    MIN(vector_dims(embedding)) AS min_dimensions,
    MAX(vector_dims(embedding)) AS max_dimensions
FROM rss_news_chunks;


SELECT
    n.rss_news_id,
    n.title,
    c.chunk_index,
    LEFT(c.chunk_text, 200) AS chunk_preview,
    ROUND(
        (1 - (c.embedding <=> reference.embedding))::numeric,
        4
    ) AS cosine_similarity
FROM rss_news_chunks AS c
JOIN rss_news AS n
    ON n.rss_news_id = c.fk_rss_news_id
CROSS JOIN (
    SELECT embedding
    FROM rss_news_chunks
    WHERE fk_rss_news_id = 3
      AND chunk_index = 0
      AND model_name = 'intfloat/multilingual-e5-small'
) AS reference
WHERE c.model_name = 'intfloat/multilingual-e5-small'
ORDER BY c.embedding <=> reference.embedding
LIMIT 5;


SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'nli_news'
ORDER BY ordinal_position;

SELECT *
FROM nli_news
LIMIT 5;


SELECT
    topic,
    keyword_match,
    nli_recovered,
    COUNT(*) AS total_news,
    ROUND(AVG(nli_score)::numeric, 4) AS avg_nli_score,
    COUNT(*) FILTER (
        WHERE nli_score >= recovery_threshold
    ) AS above_threshold
FROM nli_news
GROUP BY
    topic,
    keyword_match,
    nli_recovered
ORDER BY
    topic,
    keyword_match DESC,
    nli_recovered DESC;

SELECT
    COUNT(DISTINCT n.rss_news_id) AS relevant_news,
    COUNT(c.rss_news_chunk_id) AS relevant_chunks
FROM rss_news AS n
JOIN rss_news_chunks AS c
    ON c.fk_rss_news_id = n.rss_news_id
WHERE c.model_name = 'intfloat/multilingual-e5-small'
  AND EXISTS (
      SELECT 1
      FROM nli_news AS nl
      WHERE nl.rss_news_id = n.rss_news_id
        AND nl.topic = 'inteligencia_artificial'
        AND (
            nl.keyword_match = TRUE
            OR nl.nli_recovered = TRUE
        )
  );
