#!/usr/bin/env python3
"""
Test script for RSS news ingestion pipeline.
This tests the load_rss_feeds function without requiring Docker.
"""

import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../../mage_pipeline/alphapulse/pipelines/news_ingestion_pipeline",
        )
    ),
)

# Mock the data_loader decorator for testing
import types


def data_loader(func):
    return func


# Create a mock module for mage_ai
mock_mage_ai = types.ModuleType("mage_ai")
mock_mage_ai_data_preparation = types.ModuleType("mage_ai.data_preparation")
mock_mage_ai_data_preparation_decorators = types.ModuleType(
    "mage_ai.data_preparation.decorators"
)
mock_mage_ai_data_preparation_decorators.data_loader = data_loader
sys.modules["mage_ai"] = mock_mage_ai
sys.modules["mage_ai.data_preparation"] = mock_mage_ai_data_preparation
sys.modules["mage_ai.data_preparation.decorators"] = (
    mock_mage_ai_data_preparation_decorators
)

# Now import the actual module
## load_rss_feeds legacy import removed


def test_rss_news_ingestion():
    """Test the RSS news ingestion pipeline."""
    print("=" * 60)
    print("Testing RSS News Ingestion Pipeline")
    print("=" * 60)

    try:
        # Call the load_rss_feeds function
        print("\n📡 Fetching RSS feeds from CoinDesk and Cointelegraph...")
        df = load_rss_feeds()

        if df.empty:
            print("❌ No articles fetched!")
            return False

        print(f"✅ Successfully fetched {len(df)} articles")
        print(f"\n📊 Source distribution:")
        source_counts = df["source"].value_counts()
        for source, count in source_counts.items():
            print(f"   {source}: {count} articles")

        print(f"\n📅 Date range:")
        if df["published_at"].notna().any():
            min_date = df["published_at"].min()
            max_date = df["published_at"].max()
            print(f"   From: {min_date}")
            print(f"   To:   {max_date}")
        else:
            print("   No valid dates found")

        print(f"\n📝 Sample articles:")
        for i, row in df.head(3).iterrows():
            print(f"\n   {i+1}. {row['title'][:80]}...")
            print(f"      Source: {row['source']}")
            print(f"      URL: {row['url'][:80]}...")
            if row["summary"]:
                print(f"      Summary: {row['summary'][:100]}...")

        # Check for duplicates
        duplicate_urls = df["url"].duplicated().sum()
        if duplicate_urls > 0:
            print(f"\n⚠️  Found {duplicate_urls} duplicate URLs in current batch")
        else:
            print(f"\n✅ No duplicate URLs in current batch")

        # Data quality checks
        print(f"\n🔍 Data Quality Checks:")
        print(f"   Articles with empty title: {df['title'].str.strip().eq('').sum()}")
        print(f"   Articles with empty URL: {df['url'].str.strip().eq('').sum()}")
        print(
            f"   Articles with missing published_at: {df['published_at'].isna().sum()}"
        )

        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_rss_news_ingestion()
    print("\n" + "=" * 60)
    if success:
        print("✅ RSS News Ingestion Test PASSED")
        print("\nNext steps:")
        print(
            "1. Start Docker daemon: open Docker Desktop or run 'sudo systemctl start docker'"
        )
        print("2. Start services: make up")
        print("3. Restart Mage: make restart")
        print("4. Access Mage UI at http://localhost:6789")
        print("5. Run the news_ingestion_pipeline")
    else:
        print("❌ RSS News Ingestion Test FAILED")
    print("=" * 60)
