-- ================================================================================
-- Create sentiment_scores table
-- Purpose: Store sentiment analysis scores from market news
-- ================================================================================

CREATE TABLE IF NOT EXISTS sentiment_scores (
    id SERIAL PRIMARY KEY,
    news_id INTEGER REFERENCES market_news(id) ON DELETE CASCADE,
    
    -- Sentiment analysis results
    sentiment_score DECIMAL(5, 4) NOT NULL,  -- -1.0000 (negative) to 1.0000 (positive)
    confidence DECIMAL(5, 4),                -- Confidence level of the prediction
    label VARCHAR(20),                        -- 'positive', 'negative', 'neutral'
    
    -- Metadata
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50) DEFAULT 'v1.0',
    
    -- Constraints
    CONSTRAINT valid_sentiment_score CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    CONSTRAINT valid_confidence CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    CONSTRAINT valid_label CHECK (label IN ('positive', 'negative', 'neutral'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sentiment_scores_news_id ON sentiment_scores(news_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_scores_analyzed_at ON sentiment_scores(analyzed_at DESC);
CREATE INDEX IF NOT EXISTS idx_sentiment_scores_label ON sentiment_scores(label);

\echo 'sentiment_scores table created successfully!'
