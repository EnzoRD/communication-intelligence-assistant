-- ============================================================
-- Communication Intelligence Assistant
-- Initial PostgreSQL database schema
-- Database: cia_db
-- ============================================================


-- ============================================================
-- 1. RSS SOURCES
-- Stores the RSS feeds monitored by the application.
-- ============================================================

CREATE TABLE rss_sources (
    rss_source_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    feed_url TEXT NOT NULL,
    website_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_rss_sources_feed_url UNIQUE (feed_url)
);


-- ============================================================
-- 2. RSS RAW
-- Stores the raw XML retrieved from RSS feeds.
-- Allows traceability and reprocessing of source data.
-- ============================================================

CREATE TABLE rss_raw (
    rss_raw_id BIGSERIAL PRIMARY KEY,
    fk_rss_source_id BIGINT NOT NULL,
    raw_content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_processed BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT fk_rss_raw_rss_source
        FOREIGN KEY (fk_rss_source_id)
        REFERENCES rss_sources (rss_source_id),

    CONSTRAINT uq_rss_raw_source_hash
        UNIQUE (fk_rss_source_id, content_hash)
);


-- ============================================================
-- 3. RSS NEWS
-- Stores parsed, cleaned and normalized RSS articles.
-- One record represents one unique news article.
-- ============================================================

CREATE TABLE rss_news (
    rss_news_id BIGSERIAL PRIMARY KEY,
    fk_rss_source_id BIGINT NOT NULL,
    fk_rss_raw_id BIGINT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    content TEXT,
    url TEXT NOT NULL,
    author VARCHAR(255),
    published_at TIMESTAMPTZ,
    content_hash VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_rss_news_rss_source
        FOREIGN KEY (fk_rss_source_id)
        REFERENCES rss_sources (rss_source_id),

    CONSTRAINT fk_rss_news_rss_raw
        FOREIGN KEY (fk_rss_raw_id)
        REFERENCES rss_raw (rss_raw_id),

    CONSTRAINT uq_rss_news_url UNIQUE (url)
);


-- ============================================================
-- 4. KEYWORDS
-- Stores the terms monitored by the application.
-- ============================================================

CREATE TABLE keywords (
    keyword_id BIGSERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_keywords_keyword UNIQUE (keyword)
);


-- ============================================================
-- 5. RSS NEWS - KEYWORDS
-- Many-to-many relationship between news and keywords.
-- ============================================================

CREATE TABLE rss_news_keywords (
    rss_news_keyword_id BIGSERIAL PRIMARY KEY,
    fk_rss_news_id BIGINT NOT NULL,
    fk_keyword_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_rss_news_keywords_news
        FOREIGN KEY (fk_rss_news_id)
        REFERENCES rss_news (rss_news_id),

    CONSTRAINT fk_rss_news_keywords_keyword
        FOREIGN KEY (fk_keyword_id)
        REFERENCES keywords (keyword_id),

    CONSTRAINT uq_rss_news_keywords
        UNIQUE (fk_rss_news_id, fk_keyword_id)
);


-- ============================================================
-- 6. RSS SENTIMENTS
-- Stores NLP sentiment analysis results for each article.
-- ============================================================

CREATE TABLE rss_sentiments (
    rss_sentiment_id BIGSERIAL PRIMARY KEY,
    fk_rss_news_id BIGINT NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    positive_score REAL,
    neutral_score REAL,
    negative_score REAL,
    model_name VARCHAR(255) NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_rss_sentiments_news
        FOREIGN KEY (fk_rss_news_id)
        REFERENCES rss_news (rss_news_id),

    CONSTRAINT uq_rss_sentiments_news
        UNIQUE (fk_rss_news_id),

    CONSTRAINT ck_rss_sentiments_sentiment
        CHECK (sentiment IN ('positive', 'neutral', 'negative')),

    CONSTRAINT ck_rss_sentiments_positive_score
        CHECK (positive_score BETWEEN 0 AND 1),

    CONSTRAINT ck_rss_sentiments_neutral_score
        CHECK (neutral_score BETWEEN 0 AND 1),

    CONSTRAINT ck_rss_sentiments_negative_score
        CHECK (negative_score BETWEEN 0 AND 1)
);


-- ============================================================
-- 7. RSS ENTITIES
-- Stores entities detected by the NLP process.
-- A news article can contain multiple entities.
-- ============================================================

CREATE TABLE rss_entities (
    rss_entity_id BIGSERIAL PRIMARY KEY,
    fk_rss_news_id BIGINT NOT NULL,
    entity_text TEXT NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    confidence_score REAL,
    model_name VARCHAR(255) NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_rss_entities_news
        FOREIGN KEY (fk_rss_news_id)
        REFERENCES rss_news (rss_news_id),

    CONSTRAINT ck_rss_entities_confidence_score
        CHECK (confidence_score BETWEEN 0 AND 1)
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_rss_raw_source
    ON rss_raw (fk_rss_source_id);

CREATE INDEX idx_rss_raw_processed
    ON rss_raw (is_processed);

CREATE INDEX idx_rss_news_source
    ON rss_news (fk_rss_source_id);

CREATE INDEX idx_rss_news_published_at
    ON rss_news (published_at);

CREATE INDEX idx_rss_news_keywords_news
    ON rss_news_keywords (fk_rss_news_id);

CREATE INDEX idx_rss_news_keywords_keyword
    ON rss_news_keywords (fk_keyword_id);

CREATE INDEX idx_rss_entities_news
    ON rss_entities (fk_rss_news_id);

CREATE INDEX idx_rss_entities_type
    ON rss_entities (entity_type);