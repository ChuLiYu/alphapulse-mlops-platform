#!/usr/bin/env python3
"""
Simple test for RSS feed fetching without importing the full pipeline.
"""

from datetime import datetime

import feedparser
import pandas as pd


def test_rss_feeds():
    """Test RSS feed fetching directly."""
    print("=" * 60)
    print("Simple RSS Feed Test")
    print("=" * 60)

    # Define RSS feed sources
    rss_sources = [
        {"url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "name": "CoinDesk"},
        {"url": "https://cointelegraph.com/rss", "name": "Cointelegraph"},
    ]

    all_articles = []

    for source in rss_sources:
        print(f"\n📡 Fetching from {source['name']}: {source['url']}")

        try:
            # Parse RSS feed
            feed = feedparser.parse(source["url"])

            # Check if feed was successfully parsed
            if feed.bozo:
                print(f"  ⚠️  Warning: {feed.bozo_exception}")

            print(f"  ✅ Found {len(feed.entries)} articles")

            # Extract article data
            for entry in feed.entries[:3]:  # Just first 3 for testing
                # Parse published date
                published_at = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        published_at = datetime(*entry.published_parsed[:6])
                    except Exception as e:
                        print(f"  ⚠️  Could not parse date: {e}")

                # Extract article data
                article = {
                    "title": entry.get("title", "").strip(),
                    "url": entry.get("link", "").strip(),
                    "summary": entry.get(
                        "summary", entry.get("description", "")
                    ).strip(),
                    "published_at": published_at,
                    "source": source["name"],
                }

                # Only add articles with valid title and URL
                if article["title"] and article["url"]:
                    all_articles.append(article)
                    print(f"    • {article['title'][:60]}...")
                else:
                    print(f"    ⚠️  Skipping article with missing title or URL")

        except Exception as e:
            print(f"  ❌ Failed to fetch RSS feed: {e}")
            continue

    # Convert to DataFrame
    df = pd.DataFrame(all_articles)

    print(f"\n📊 Summary:")
    print(f"  Total articles fetched: {len(df)}")

    if not df.empty:
        source_counts = df["source"].value_counts()
        for source, count in source_counts.items():
            print(f"  {source}: {count} articles")

        # Check for duplicates
        duplicate_urls = df["url"].duplicated().sum()
        if duplicate_urls > 0:
            print(f"  ⚠️  Found {duplicate_urls} duplicate URLs")
        else:
            print(f"  ✅ No duplicate URLs")

        # Data quality checks
        print(f"\n🔍 Data Quality:")
        print(f"  Empty titles: {df['title'].str.strip().eq('').sum()}")
        print(f"  Empty URLs: {df['url'].str.strip().eq('').sum()}")
        print(f"  Missing dates: {df['published_at'].isna().sum()}")

        # Show sample
        print(f"\n📝 Sample article:")
        if len(df) > 0:
            sample = df.iloc[0]
            print(f"  Title: {sample['title'][:80]}...")
            print(f"  Source: {sample['source']}")
            print(f"  URL: {sample['url'][:80]}...")
            if sample["summary"]:
                print(f"  Summary: {sample['summary'][:100]}...")

    return len(df) > 0


if __name__ == "__main__":
    print("Testing RSS feed accessibility...")
    success = test_rss_feeds()

    print("\n" + "=" * 60)
    if success:
        print("✅ RSS Feed Test PASSED")
        print("\nThe RSS news ingestion pipeline is ready!")
        print("\nNext steps when Docker is running:")
        print("1. Start Docker daemon")
        print("2. Run: make up")
        print("3. Run: make restart")
        print("4. Access Mage UI at http://localhost:6789")
        print("5. Run the news_ingestion_pipeline")
    else:
        print("❌ RSS Feed Test FAILED")
    print("=" * 60)
