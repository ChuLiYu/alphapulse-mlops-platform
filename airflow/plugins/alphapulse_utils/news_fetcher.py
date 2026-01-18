import feedparser
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def fetch_rss_feeds():
    rss_sources = [
        {"url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "name": "CoinDesk"},
        {"url": "https://cointelegraph.com/rss", "name": "Cointelegraph"},
        {"url": "https://cryptoslate.com/feed/", "name": "CryptoSlate"},
        {"url": "https://bitcoinmagazine.com/.rss/full/", "name": "Bitcoin Magazine"},
        {"url": "https://www.newsbtc.com/feed/", "name": "NewsBTC"},
        {"url": "https://dailyhodl.com/feed/", "name": "The Daily Hodl"},
        {"url": "https://cryptopotato.com/feed/", "name": "CryptoPotato"},
        {"url": "https://beincrypto.com/feed/", "name": "BeInCrypto"},
        {"url": "https://news.bitcoin.com/feed/", "name": "Bitcoin.com"},
        {"url": "https://cryptopanic.com/news/rss/", "name": "CryptoPanic"},
        {"url": "https://www.theblock.co/rss.xml", "name": "TheBlock"},
        {"url": "https://coinjournal.net/news/feed/", "name": "CoinJournal"},
        {"url": "https://ambcrypto.com/feed/", "name": "AMBCrypto"},
        # Social Media Sources (via RSS)
        {
            "url": "https://www.reddit.com/r/CryptoCurrency/new/.rss",
            "name": "Reddit_CryptoCurrency",
        },
        {"url": "https://www.reddit.com/r/Bitcoin/new/.rss", "name": "Reddit_Bitcoin"},
        {"url": "https://www.reddit.com/r/ethdev/new/.rss", "name": "Reddit_EthDev"},
    ]

    all_articles = []

    for source in rss_sources:
        try:
            feed = feedparser.parse(source["url"])
            if not feed.entries:
                continue

            for entry in feed.entries:
                published_at = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published_at = datetime(*entry.published_parsed[:6])

                article = {
                    "title": entry.get("title", "").strip(),
                    "url": entry.get("link", "").strip(),
                    "summary": entry.get(
                        "summary", entry.get("description", "")
                    ).strip(),
                    "published_at": published_at,
                    "source": source["name"],
                }

                if article["title"] and article["url"]:
                    all_articles.append(article)

        except Exception as e:
            logger.error(f"Error fetching {source['name']}: {e}")

    df = pd.DataFrame(all_articles)
    if not df.empty:
        df = df.drop_duplicates(subset=["url"], keep="first")

    return df


def fetch_unprocessed_news():
    from operators.postgres_operator import PostgresUtils

    query = """
    SELECT 
        mn.id, mn.title, mn.summary, mn.source, mn.published_at, mn.url
    FROM market_news mn
    LEFT JOIN sentiment_scores ss ON mn.id = ss.article_id
    WHERE ss.article_id IS NULL
    ORDER BY mn.published_at DESC
    LIMIT 50
    """

    engine = PostgresUtils.get_sqlalchemy_engine()
    with engine.connect() as conn:
        df = pd.read_sql(query, conn.connection)

    if not df.empty:
        df["text_for_analysis"] = df["title"] + ". " + df["summary"].fillna("")

    return df
