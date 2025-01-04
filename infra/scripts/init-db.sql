-- ================================================================================
-- AlphaPulse Database Initialization Script
-- ================================================================================
-- This script initializes the PostgreSQL database schema for AlphaPulse
-- It creates all necessary tables, indexes, and constraints
--
-- Usage: Automatically executed by docker-compose on first startup
-- ================================================================================

-- Create database if not exists (handled by POSTGRES_DB env var in docker-compose)

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search optimization

-- ================================================================================
-- Table: prices
-- Purpose: Store historical cryptocurrency price data
-- ================================================================================
CREATE TABLE IF NOT EXISTS prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,  -- Use DECIMAL for financial precision
    volume DECIMAL(20, 8),
    market_cap DECIMAL(25, 2),
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR(50) DEFAULT 'yahoo_finance',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_symbol_timestamp UNIQUE (symbol, timestamp),
    CONSTRAINT positive_price CHECK (price > 0),
    CONSTRAINT positive_volume CHECK (volume >= 0)
);

-- Indexes for prices table
CREATE INDEX IF NOT EXISTS idx_prices_symbol ON prices(symbol);
CREATE INDEX IF NOT EXISTS idx_prices_timestamp ON prices(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_prices_symbol_timestamp ON prices(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_prices_created_at ON prices(created_at DESC);

-- ================================================================================
-- Table: technical_indicators
-- Purpose: Store calculated technical indicators (RSI, MACD, Bollinger Bands, etc.)
-- ================================================================================
CREATE TABLE IF NOT EXISTS technical_indicators (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    
    -- Moving Averages
    sma_7 DECIMAL(20, 8),
    sma_25 DECIMAL(20, 8),
    sma_99 DECIMAL(20, 8),
    ema_12 DECIMAL(20, 8),
    ema_26 DECIMAL(20, 8),
    
    -- Momentum Indicators
    rsi_14 DECIMAL(10, 4),          -- Relative Strength Index
    macd DECIMAL(20, 8),            -- MACD line
    macd_signal DECIMAL(20, 8),     -- Signal line
    macd_histogram DECIMAL(20, 8),  -- MACD histogram
    
    -- Volatility Indicators
    bb_upper DECIMAL(20, 8),        -- Bollinger Band Upper
    bb_middle DECIMAL(20, 8),       -- Bollinger Band Middle
    bb_lower DECIMAL(20, 8),        -- Bollinger Band Lower
    atr_14 DECIMAL(20, 8),          -- Average True Range
    
    -- Volume Indicators
    obv DECIMAL(25, 2),             -- On-Balance Volume
    
    -- Trend Indicators
    adx_14 DECIMAL(10, 4),          -- Average Directional Index
    
    -- Metadata
    calculation_version VARCHAR(10) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_indicator_symbol_timestamp UNIQUE (symbol, timestamp),
    CONSTRAINT valid_rsi CHECK (rsi_14 >= 0 AND rsi_14 <= 100),
    CONSTRAINT valid_adx CHECK (adx_14 >= 0 AND adx_14 <= 100),
    
    -- Foreign key to prices table
    FOREIGN KEY (symbol, timestamp) 
        REFERENCES prices(symbol, timestamp) 
        ON DELETE CASCADE
);

-- Indexes for technical_indicators table
CREATE INDEX IF NOT EXISTS idx_indicators_symbol ON technical_indicators(symbol);
CREATE INDEX IF NOT EXISTS idx_indicators_timestamp ON technical_indicators(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_indicators_symbol_timestamp ON technical_indicators(symbol, timestamp DESC);

-- ================================================================================
-- Table: trading_signals
-- Purpose: Store generated trading signals (BUY, SELL, HOLD)
-- ================================================================================
CREATE TABLE IF NOT EXISTS trading_signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(10) NOT NULL,  -- 'BUY', 'SELL', 'HOLD'
    confidence DECIMAL(5, 4) NOT NULL, -- 0.0000 to 1.0000
    price_at_signal DECIMAL(20, 8) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    
    -- Signal metadata
    strategy_name VARCHAR(100),
    reasoning TEXT,
    indicators_used JSONB,
    
    -- Performance tracking
    executed BOOLEAN DEFAULT FALSE,
    execution_price DECIMAL(20, 8),
    execution_timestamp TIMESTAMP,
    profit_loss DECIMAL(20, 8),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_signal_type CHECK (signal_type IN ('BUY', 'SELL', 'HOLD')),
    CONSTRAINT valid_confidence CHECK (confidence >= 0 AND confidence <= 1),
    CONSTRAINT positive_signal_price CHECK (price_at_signal > 0)
);

-- Indexes for trading_signals table
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON trading_signals(symbol);
CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON trading_signals(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_type ON trading_signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_signals_executed ON trading_signals(executed);
CREATE INDEX IF NOT EXISTS idx_signals_symbol_timestamp ON trading_signals(symbol, timestamp DESC);

-- ================================================================================
-- Table: news_sentiment
-- Purpose: Store news articles and their sentiment analysis results
-- ================================================================================
CREATE TABLE IF NOT EXISTS news_sentiment (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    url TEXT UNIQUE,
    source VARCHAR(100),
    
    -- Sentiment analysis results
    sentiment_score DECIMAL(5, 4),  -- -1.0000 (negative) to 1.0000 (positive)
    sentiment_label VARCHAR(20),     -- 'positive', 'negative', 'neutral'
    sentiment_confidence DECIMAL(5, 4),
    
    -- Metadata
    published_at TIMESTAMP,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_sentiment_score CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    CONSTRAINT valid_sentiment_label CHECK (sentiment_label IN ('positive', 'negative', 'neutral'))
);

-- Indexes for news_sentiment table
CREATE INDEX IF NOT EXISTS idx_news_symbol ON news_sentiment(symbol);
CREATE INDEX IF NOT EXISTS idx_news_published ON news_sentiment(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_sentiment ON news_sentiment(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_news_url ON news_sentiment(url);


-- ================================================================================
-- Table: model_predictions
-- Purpose: Store ML model predictions and their performance
-- ================================================================================
CREATE TABLE IF NOT EXISTS model_predictions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20),
    
    -- Prediction
    predicted_price DECIMAL(20, 8) NOT NULL,
    prediction_horizon_hours INTEGER NOT NULL,  -- How many hours ahead
    confidence DECIMAL(5, 4),
    
    -- Actual outcome (filled later)
    actual_price DECIMAL(20, 8),
    prediction_error DECIMAL(20, 8),
    
    -- Timestamps
    prediction_timestamp TIMESTAMP NOT NULL,
    target_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT positive_predicted_price CHECK (predicted_price > 0),
    CONSTRAINT positive_horizon CHECK (prediction_horizon_hours > 0)
);

-- Indexes for model_predictions table
CREATE INDEX IF NOT EXISTS idx_predictions_symbol ON model_predictions(symbol);
CREATE INDEX IF NOT EXISTS idx_predictions_model ON model_predictions(model_name);
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON model_predictions(prediction_timestamp DESC);

-- ================================================================================
-- Table: pipeline_runs
-- Purpose: Track Airflow pipeline execution history
-- ================================================================================
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    run_id VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL,  -- 'running', 'completed', 'failed'
    
    -- Execution details
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    
    -- Metrics
    records_processed INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- Metadata
    triggered_by VARCHAR(50) DEFAULT 'scheduler',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_pipeline_status CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
);

-- Indexes for pipeline_runs table
CREATE INDEX IF NOT EXISTS idx_pipeline_name ON pipeline_runs(pipeline_name);
CREATE INDEX IF NOT EXISTS idx_pipeline_status ON pipeline_runs(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_start_time ON pipeline_runs(start_time DESC);

-- ================================================================================
-- Airflow Pipeline Compatibility Tables
-- ================================================================================

-- Table: btc_price_data (for Mage BTC price pipeline compatibility)
CREATE TABLE IF NOT EXISTS btc_price_data (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    open DECIMAL(20, 8),
    high DECIMAL(20, 8),
    low DECIMAL(20, 8),
    close DECIMAL(20, 8),
    volume DECIMAL(20, 8),
    daily_return DECIMAL(10, 6),
    log_return DECIMAL(10, 6),
    sma_7 DECIMAL(20, 8),
    sma_20 DECIMAL(20, 8),
    sma_50 DECIMAL(20, 8),
    sma_200 DECIMAL(20, 8),
    ema_12 DECIMAL(20, 8),
    ema_26 DECIMAL(20, 8),
    rsi_14 DECIMAL(10, 4),
    bb_upper DECIMAL(20, 8),
    bb_middle DECIMAL(20, 8),
    bb_lower DECIMAL(20, 8),
    bb_width DECIMAL(10, 6),
    bb_position DECIMAL(10, 6),
    macd_line DECIMAL(20, 8),
    macd_signal DECIMAL(20, 8),
    macd_histogram DECIMAL(20, 8),
    volume_sma_20 DECIMAL(20, 8),
    volume_ratio DECIMAL(10, 6),
    daily_volatility DECIMAL(10, 6),
    atr DECIMAL(20, 8),
    resistance_20 DECIMAL(20, 8),
    support_20 DECIMAL(20, 8),
    price_position DECIMAL(10, 6),
    trend_sma INTEGER,
    trend_ema INTEGER,
    momentum_10 DECIMAL(10, 6),
    roc_10 DECIMAL(10, 6),
    data_source VARCHAR(50),
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT uq_btc_price_date_ticker UNIQUE (date, ticker)
);

-- Indexes for btc_price_data table
CREATE INDEX IF NOT EXISTS idx_btc_price_date ON btc_price_data(date DESC);
CREATE INDEX IF NOT EXISTS idx_btc_price_ticker ON btc_price_data(ticker);
CREATE INDEX IF NOT EXISTS idx_btc_price_date_ticker ON btc_price_data(date DESC, ticker);

-- Table: market_news (for Mage news ingestion pipeline compatibility)
CREATE TABLE IF NOT EXISTS market_news (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    summary TEXT,
    published_at TIMESTAMP,
    source TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for market_news table
CREATE INDEX IF NOT EXISTS idx_market_news_source ON market_news(source);
CREATE INDEX IF NOT EXISTS idx_market_news_published_at ON market_news(published_at DESC);

-- Table: model_features (for Mage feature integration pipeline compatibility)
CREATE TABLE IF NOT EXISTS model_features (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    
    -- Price and volume features
    close FLOAT,
    volume FLOAT,
    price_change_1d FLOAT,
    price_change_7d FLOAT,
    price_change_30d FLOAT,
    volume_change_1d FLOAT,
    volume_change_7d FLOAT,
    
    -- Technical indicators
    rsi_14 FLOAT,
    rsi_overbought INTEGER,
    rsi_oversold INTEGER,
    rsi_neutral INTEGER,
    macd_line FLOAT,
    macd_signal FLOAT,
    macd_histogram FLOAT,
    macd_bullish INTEGER,
    macd_bearish INTEGER,
    bb_width FLOAT,
    bb_position FLOAT,
    bb_squeeze INTEGER,
    bb_breakout_upper INTEGER,
    bb_breakout_lower INTEGER,
    sma_7 FLOAT,
    sma_20 FLOAT,
    sma_50 FLOAT,
    sma_200 FLOAT,
    ema_12 FLOAT,
    ema_26 FLOAT,
    sma_crossover_7_20 INTEGER,
    sma_crossover_20_50 INTEGER,
    ema_crossover INTEGER,
    daily_volatility FLOAT,
    atr FLOAT,
    trend_sma INTEGER,
    trend_ema INTEGER,
    momentum_10 FLOAT,
    roc_10 FLOAT,
    
    -- News frequency features
    news_count_1h INTEGER,
    news_count_3h INTEGER,
    news_count_6h INTEGER,
    news_count_12h INTEGER,
    news_count_24h INTEGER,
    news_count_1d INTEGER,
    news_count_3d INTEGER,
    news_count_7d INTEGER,
    news_count_30d INTEGER,
    news_velocity_1h FLOAT,
    news_velocity_3h FLOAT,
    news_velocity_6h FLOAT,
    news_gap_mean FLOAT,
    news_gap_std FLOAT,
    news_source_coindesk INTEGER,
    news_source_cointelegraph INTEGER,
    news_source_other INTEGER,
    news_source_diversity FLOAT,
    sentiment_volume_24h INTEGER,
    avg_sentiment_24h FLOAT,
    
    -- Sentiment features
    sentiment_avg_1h FLOAT,
    sentiment_avg_3h FLOAT,
    sentiment_avg_6h FLOAT,
    sentiment_avg_12h FLOAT,
    sentiment_avg_24h FLOAT,
    sentiment_volatility_1h FLOAT,
    sentiment_volatility_3h FLOAT,
    sentiment_volatility_6h FLOAT,
    sentiment_volatility_12h FLOAT,
    sentiment_volatility_24h FLOAT,
    sentiment_positive_ratio_24h FLOAT,
    sentiment_neutral_ratio_24h FLOAT,
    sentiment_negative_ratio_24h FLOAT,
    sentiment_bullish_ratio_24h FLOAT,
    sentiment_bearish_ratio_24h FLOAT,
    sentiment_momentum_1h FLOAT,
    sentiment_momentum_3h FLOAT,
    sentiment_momentum_6h FLOAT,
    sentiment_momentum_12h FLOAT,
    sentiment_momentum_24h FLOAT,
    sentiment_extreme_positive_24h INTEGER,
    sentiment_extreme_negative_24h INTEGER,
    sentiment_max_24h FLOAT,
    sentiment_min_24h FLOAT,
    sentiment_range_24h FLOAT,
    
    -- Interaction features
    news_volatility_interaction FLOAT,
    news_per_volatility FLOAT,
    volatility_amplified_by_news FLOAT,
    high_volatility_high_news INTEGER,
    sentiment_rsi_alignment FLOAT,
    sentiment_rsi_alignment_strength FLOAT,
    sentiment_rsi_divergence FLOAT,
    bullish_confluence INTEGER,
    bearish_confluence INTEGER,
    mixed_signals INTEGER,
    news_price_interaction FLOAT,
    news_price_interaction_magnitude FLOAT,
    news_acceleration_during_uptrend FLOAT,
    news_acceleration_during_downtrend FLOAT,
    price_sensitivity_to_news FLOAT,
    high_news_large_move INTEGER,
    sentiment_volume_interaction FLOAT,
    volume_weighted_sentiment FLOAT,
    high_volume_strong_sentiment INTEGER,
    sentiment_volume_divergence INTEGER,
    sentiment_confirmed_by_volume INTEGER,
    news_sentiment_composite FLOAT,
    market_sentiment_index FLOAT,
    alpha_score FLOAT,
    risk_adjusted_sentiment FLOAT,
    news_impact_lag_1 FLOAT,
    news_impact_lag_2 FLOAT,
    news_impact_lag_3 FLOAT,
    sentiment_persistence_1 FLOAT,
    sentiment_persistence_2 FLOAT,
    sentiment_rsi_lag_1 FLOAT,
    cumulative_news_3d INTEGER,
    cumulative_sentiment_3d FLOAT,
    news_sentiment_momentum FLOAT,
    sentiment_per_news FLOAT,
    rsi_sentiment_ratio FLOAT,
    volume_per_news FLOAT,
    price_change_per_sentiment FLOAT,
    news_sentiment_efficiency FLOAT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    feature_set_version VARCHAR(20) DEFAULT 'v1.0',
    data_source VARCHAR(50) DEFAULT 'alphapulse_pipeline'
);

-- Indexes for model_features table
CREATE INDEX IF NOT EXISTS idx_model_features_date ON model_features(date DESC);
CREATE INDEX IF NOT EXISTS idx_model_features_ticker ON model_features(ticker);
CREATE INDEX IF NOT EXISTS idx_model_features_date_ticker ON model_features(date DESC, ticker);

-- ================================================================================
-- Views: Useful aggregated data views
-- ================================================================================

-- View: Latest prices for each symbol
CREATE OR REPLACE VIEW latest_prices AS
SELECT DISTINCT ON (symbol)
    symbol,
    price,
    volume,
    timestamp,
    source
FROM prices
ORDER BY symbol, timestamp DESC;

-- View: Latest signals for each symbol
CREATE OR REPLACE VIEW latest_signals AS
SELECT DISTINCT ON (symbol)
    symbol,
    signal_type,
    confidence,
    price_at_signal,
    timestamp,
    strategy_name
FROM trading_signals
ORDER BY symbol, timestamp DESC;

-- View: Price changes (24h)
CREATE OR REPLACE VIEW price_changes_24h AS
WITH current_prices AS (
    SELECT DISTINCT ON (symbol)
        symbol,
        price as current_price,
        timestamp as current_timestamp
    FROM prices
    ORDER BY symbol, timestamp DESC
),
old_prices AS (
    SELECT DISTINCT ON (symbol)
        symbol,
        price as old_price
    FROM prices
    WHERE timestamp <= NOW() - INTERVAL '24 hours'
    ORDER BY symbol, timestamp DESC
)
SELECT 
    c.symbol,
    c.current_price,
    o.old_price,
    (c.current_price - o.old_price) as price_change,
    ((c.current_price - o.old_price) / o.old_price * 100) as price_change_percent,
    c.current_timestamp
FROM current_prices c
LEFT JOIN old_prices o ON c.symbol = o.symbol;

-- ================================================================================
-- Functions: Utility functions
-- ================================================================================

-- Function: Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update_updated_at trigger to relevant tables
CREATE TRIGGER update_prices_updated_at
    BEFORE UPDATE ON prices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_indicators_updated_at
    BEFORE UPDATE ON technical_indicators
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_signals_updated_at
    BEFORE UPDATE ON trading_signals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ================================================================================
-- Seed Data (Optional - for testing)
-- ================================================================================
-- Uncomment to insert sample data for testing

-- INSERT INTO prices (symbol, price, volume, timestamp) VALUES
-- ('BTC-USD', 45123.50, 1234567.89, NOW() - INTERVAL '1 hour'),
-- ('BTC-USD', 45200.00, 1345678.90, NOW() - INTERVAL '30 minutes'),
-- ('BTC-USD', 45180.25, 1456789.01, NOW());

-- ================================================================================
-- Grants: Ensure proper permissions
-- ================================================================================
-- Grant usage on sequences (needed for SERIAL columns)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Grant all privileges on tables to application user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;

-- ================================================================================
-- Completion
-- ================================================================================
\echo 'Database schema initialized successfully!'
\echo 'Tables created:'
\echo '  - prices'
\echo '  - technical_indicators'
\echo '  - trading_signals'
\echo '  - news_sentiment'
\echo '  - model_predictions'
\echo '  - pipeline_runs'
\echo '  - btc_price_data (Airflow pipeline compatibility)'
\echo '  - market_news (Airflow pipeline compatibility)'
\echo '  - model_features (Airflow pipeline compatibility)'
\echo ''
\echo 'Views created:'
\echo '  - latest_prices'
\echo '  - latest_signals'
\echo '  - price_changes_24h'
\echo ''
\echo 'Ready for data ingestion!'
