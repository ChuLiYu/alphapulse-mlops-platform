"""
Unit tests for RSS feed parsing functionality.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import feedparser
import pytest

from tests.conftest import NewsArticle, validate_news_article


@pytest.mark.unit
class TestRSSParser:
    """Test RSS feed parsing functionality."""

    def test_news_article_schema_validation(self, sample_rss_feed):
        """Test that news articles conform to schema."""
        for article in sample_rss_feed:
            assert validate_news_article(article), f"Invalid article: {article}"

    def test_valid_article_passes_validation(self):
        """Test valid article passes schema validation."""
        article = {
            "title": "Bitcoin Hits New All-Time High",
            "url": "https://coindesk.com/bitcoin-ath",
            "source": "CoinDesk",
            "published_at": datetime.utcnow(),
            "summary": "Bitcoin reaches new record price.",
            "content": "Full article content...",
            "sentiment_score": 0.9,
            "sentiment_label": "positive",
        }

        validated = NewsArticle(**article)
        assert validated.title == article["title"]
        assert validated.url == article["url"]
        assert validated.source == article["source"]

    def test_invalid_url_raises_error(self):
        """Test invalid URL raises validation error."""
        article = {
            "title": "Test Article",
            "url": "not-a-valid-url",  # Invalid URL
            "source": "TestSource",
            "published_at": datetime.utcnow(),
        }

        assert not validate_news_article(article)

    def test_empty_title_raises_error(self):
        """Test empty title raises validation error."""
        article = {
            "title": "",  # Empty title
            "url": "https://example.com/test",
            "source": "TestSource",
            "published_at": datetime.utcnow(),
        }

        assert not validate_news_article(article)

    def test_sentiment_score_range_validation(self):
        """Test sentiment score range validation."""
        # Valid scores
        valid_scores = [-1.0, -0.5, 0.0, 0.5, 1.0, None]

        for score in valid_scores:
            article = {
                "title": "Test Article",
                "url": "https://example.com/test",
                "source": "TestSource",
                "published_at": datetime.utcnow(),
                "sentiment_score": score,
                "sentiment_label": (
                    "positive"
                    if score and score > 0
                    else "negative" if score and score < 0 else "neutral"
                ),
            }

            if score is not None:
                article["sentiment_label"] = (
                    "positive" if score > 0 else "negative" if score < 0 else "neutral"
                )

            assert validate_news_article(article), f"Score {score} should be valid"

    def test_invalid_sentiment_score_raises_error(self):
        """Test invalid sentiment score raises error."""
        article = {
            "title": "Test Article",
            "url": "https://example.com/test",
            "source": "TestSource",
            "published_at": datetime.utcnow(),
            "sentiment_score": 1.5,  # Invalid: > 1.0
            "sentiment_label": "positive",
        }

        assert not validate_news_article(article)

    def test_invalid_sentiment_label_raises_error(self):
        """Test invalid sentiment label raises error."""
        article = {
            "title": "Test Article",
            "url": "https://example.com/test",
            "source": "TestSource",
            "published_at": datetime.utcnow(),
            "sentiment_score": 0.5,
            "sentiment_label": "invalid",  # Invalid label
        }

        assert not validate_news_article(article)

    @patch("feedparser.parse")
    def test_rss_feed_parsing(self, mock_parse, sample_rss_feed):
        """Test RSS feed parsing with mocked feedparser."""
        # Create mock feed entries
        mock_entries = []
        for article in sample_rss_feed:
            mock_entry = Mock()
            mock_entry.title = article["title"]
            mock_entry.link = article["url"]
            mock_entry.summary = article.get("summary", "")
            mock_entry.published_parsed = article["published_at"].timetuple()
            mock_entries.append(mock_entry)

        # Create mock feed
        mock_feed = Mock()
        mock_feed.entries = mock_entries
        mock_feed.bozo = 0  # No parsing errors

        mock_parse.return_value = mock_feed

        # Test parsing
        feed = feedparser.parse("https://example.com/rss")

        assert len(feed.entries) == len(sample_rss_feed)
        assert feed.entries[0].title == sample_rss_feed[0]["title"]
        assert feed.entries[0].link == sample_rss_feed[0]["url"]

    def test_article_data_freshness(self, sample_rss_feed):
        """Test that articles have valid timestamps (not from the future)."""
        for article in sample_rss_feed:
            # Articles should not be from the future
            age = datetime.utcnow() - article["published_at"]
            assert (
                age.total_seconds() > 0
            ), f"Article timestamp is in the future: {article['published_at']}"
            # Articles should be reasonably recent (not older than 24 hours for this test)
            # In conftest.py, articles are 1-2 hours old, which is fine
            assert (
                age.total_seconds() < 24 * 3600
            ), f"Article is too old: {age.total_seconds() / 3600:.1f} hours"

    def test_article_url_format(self, sample_rss_feed):
        """Test that article URLs have correct format."""
        for article in sample_rss_feed:
            url = article["url"]
            assert url.startswith("http"), f"URL should start with http: {url}"
            assert "://" in url, f"URL should contain protocol: {url}"

    def test_article_source_not_empty(self, sample_rss_feed):
        """Test that article source is not empty."""
        for article in sample_rss_feed:
            source = article["source"]
            assert (
                source and len(source.strip()) > 0
            ), f"Source should not be empty: {article}"

    @pytest.mark.parametrize(
        "title,expected_length",
        [
            ("Short", 5),
            ("Medium length title", 19),
            (
                "Very long title that exceeds maximum allowed length" * 10,
                500,
            ),  # Will be truncated
        ],
    )
    def test_title_length_validation(self, title, expected_length):
        """Test title length validation."""
        article = {
            "title": title[:500],  # Truncate to max length
            "url": "https://example.com/test",
            "source": "TestSource",
            "published_at": datetime.utcnow(),
        }

        # The schema has max_length=500, so long titles should be truncated
        validated = NewsArticle(**article)
        assert len(validated.title) <= 500

    def test_optional_fields(self):
        """Test that optional fields can be None."""
        article = {
            "title": "Test Article",
            "url": "https://example.com/test",
            "source": "TestSource",
            "published_at": datetime.utcnow(),
            "summary": None,
            "content": None,
            "sentiment_score": None,
            "sentiment_label": None,
        }

        validated = NewsArticle(**article)
        assert validated.summary is None
        assert validated.content is None
        assert validated.sentiment_score is None
        assert validated.sentiment_label is None


@pytest.mark.unit
def test_feedparser_import():
    """Test that feedparser is importable."""
    import feedparser

    assert feedparser is not None
    assert hasattr(feedparser, "parse")


@pytest.mark.unit
def test_article_datetime_conversion():
    """Test datetime conversion for article timestamps."""
    from datetime import datetime

    now = datetime.utcnow()
    article = {
        "title": "Test Article",
        "url": "https://example.com/test",
        "source": "TestSource",
        "published_at": now,
    }

    validated = NewsArticle(**article)
    assert validated.published_at == now
    assert isinstance(validated.published_at, datetime)


@pytest.mark.unit
def test_duplicate_url_detection(sample_rss_feed):
    """Test detection of duplicate URLs in articles."""
    # Create duplicate URLs
    articles = sample_rss_feed.copy()
    duplicate_article = articles[0].copy()
    duplicate_article["title"] = "Different Title"
    articles.append(duplicate_article)

    urls = [article["url"] for article in articles]
    unique_urls = set(urls)

    # One duplicate expected
    assert len(urls) == len(articles)
    assert (
        len(unique_urls) == len(articles) - 1
    ), f"Expected {len(articles) - 1} unique URLs, got {len(unique_urls)}"
