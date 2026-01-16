#!/usr/bin/env python3
"""
Test script to verify RSS pipeline end-to-end integration.
This script tests the complete flow from RSS feed fetching to PostgreSQL storage.
"""

import logging
import os
import sys

import pandas as pd
from sqlalchemy import create_engine, text

# Add mage_pipeline to path
sys.path.append(os.path.join(os.path.dirname(__file__), "mage_pipeline"))

from pipelines.news_ingestion_pipeline.export_to_postgres import export_to_postgres

# Import the pipeline functions
## pipelines legacy import removed

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_rss_pipeline():
    """Test the complete RSS pipeline end-to-end."""
    logger.info("Starting RSS pipeline end-to-end test...")

    try:
        # Step 1: Load RSS feeds
        logger.info("Step 1: Loading RSS feeds...")
        df = load_rss_feeds()

        if df is None or df.empty:
            logger.error("Failed to load RSS feeds - DataFrame is empty")
            return False

        logger.info(f"Successfully loaded {len(df)} articles from RSS feeds")
        logger.info(f"Columns: {df.columns.tolist()}")
        logger.info(f"Sample data:\n{df.head(2)}")

        # Step 2: Export to PostgreSQL
        logger.info("Step 2: Exporting to PostgreSQL...")

        # Create database connection
        db_url = "postgresql://postgres:postgres@localhost:5432/alphapulse"
        engine = create_engine(db_url)

        # First, check if table exists
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'market_news'
                );
            """
                )
            )
            table_exists = result.scalar()

            if not table_exists:
                logger.info(
                    "Table 'market_news' does not exist yet - will be created by pipeline"
                )

        # Run the export function
        export_to_postgres(df)

        # Step 3: Verify data in PostgreSQL
        logger.info("Step 3: Verifying data in PostgreSQL...")

        with engine.connect() as conn:
            # Check table now exists
            result = conn.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'market_news'
                );
            """
                )
            )
            table_exists = result.scalar()

            if not table_exists:
                logger.error("Table 'market_news' was not created")
                return False

            logger.info("Table 'market_news' created successfully")

            # Count rows
            result = conn.execute(text("SELECT COUNT(*) FROM market_news;"))
            row_count = result.scalar()
            logger.info(f"Total rows in market_news: {row_count}")

            # Check sample data
            result = conn.execute(
                text(
                    """
                SELECT source, COUNT(*) as article_count, 
                       MIN(published_at) as earliest, MAX(published_at) as latest
                FROM market_news 
                GROUP BY source;
            """
                )
            )

            logger.info("Data distribution by source:")
            for row in result:
                logger.info(
                    f"  {row.source}: {row.article_count} articles, "
                    f"from {row.earliest} to {row.latest}"
                )

            # Show sample articles
            result = conn.execute(
                text(
                    """
                SELECT title, source, published_at, url 
                FROM market_news 
                ORDER BY published_at DESC 
                LIMIT 3;
            """
                )
            )

            logger.info("Sample articles (most recent):")
            for row in result:
                logger.info(f"  Title: {row.title[:60]}...")
                logger.info(f"    Source: {row.source}, Published: {row.published_at}")
                logger.info(f"    URL: {row.url[:80]}...")

        logger.info("✅ RSS pipeline end-to-end test PASSED!")
        return True

    except Exception as e:
        logger.error(f"❌ RSS pipeline test FAILED: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def test_database_connection():
    """Test PostgreSQL database connection."""
    logger.info("Testing PostgreSQL connection...")

    try:
        db_url = "postgresql://postgres:postgres@localhost:5432/alphapulse"
        engine = create_engine(db_url)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            logger.info(f"PostgreSQL version: {version}")

            # List all tables
            result = conn.execute(
                text(
                    """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """
                )
            )

            tables = [row[0] for row in result]
            logger.info(f"Existing tables: {tables}")

        return True

    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("RSS Pipeline Integration Test")
    logger.info("=" * 60)

    # Test database connection first
    if not test_database_connection():
        logger.error("Cannot proceed - database connection failed")
        sys.exit(1)

    # Run the pipeline test
    success = test_rss_pipeline()

    if success:
        logger.info("✅ All tests passed!")
        sys.exit(0)
    else:
        logger.error("❌ Tests failed")
        sys.exit(1)
