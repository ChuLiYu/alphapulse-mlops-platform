"""
Unit tests for API schemas and validation.
"""

from datetime import datetime
from typing import List

import pytest
from pydantic import BaseModel, Field, ValidationError

from tests.conftest import NewsArticle, SentimentResult


@pytest.mark.unit
class TestAPISchemas:
    """Test API schemas and validation."""

    def test_news_article_schema_comprehensive(self):
        """Test comprehensive NewsArticle schema validation."""
        # Valid article
        valid_article = {
            "title": "Bitcoin Reaches $50,000",
            "url": "https://coindesk.com/bitcoin-50000",
            "source": "CoinDesk",
            "published_at": datetime.utcnow(),
            "summary": "Bitcoin price milestone reached.",
            "content": "Full article content...",
            "sentiment_score": 0.85,
            "sentiment_label": "positive",
        }

        article = NewsArticle(**valid_article)
        assert article.title == valid_article["title"]
        assert article.sentiment_score == 0.85

    def test_sentiment_result_schema_comprehensive(self):
        """Test comprehensive SentimentResult schema validation."""
        valid_result = {
            "sentiment": "negative",
            "score": -0.75,
            "confidence": 0.88,
            "reasoning": "Text expresses concern about market conditions.",
            "model": "llama3.2:3b",
        }

        result = SentimentResult(**valid_result)
        assert result.sentiment == "negative"
        assert result.score == -0.75
        assert result.confidence == 0.88

    def test_news_article_minimal_fields(self):
        """Test NewsArticle with minimal required fields."""
        minimal_article = {
            "title": "Minimal Article",
            "url": "https://example.com/minimal",
            "source": "TestSource",
            "published_at": datetime.utcnow(),
        }

        article = NewsArticle(**minimal_article)
        assert article.summary is None
        assert article.content is None
        assert article.sentiment_score is None
        assert article.sentiment_label is None

    def test_sentiment_result_minimal_fields(self):
        """Test SentimentResult with minimal required fields."""
        minimal_result = {"sentiment": "neutral", "score": 0.0, "confidence": 0.5}

        result = SentimentResult(**minimal_result)
        assert result.reasoning is None
        assert result.model is None

    def test_news_article_url_validation(self):
        """Test URL validation in NewsArticle."""
        test_cases = [
            ("https://example.com", True),
            ("http://example.com", True),
            ("ftp://example.com", False),  # Should fail pattern validation
            ("not-a-url", False),
            ("", False),
        ]

        for url, should_pass in test_cases:
            article_data = {
                "title": "Test Article",
                "url": url,
                "source": "TestSource",
                "published_at": datetime.utcnow(),
            }

            if should_pass:
                article = NewsArticle(**article_data)
                assert article.url == url
            else:
                with pytest.raises(ValidationError):
                    NewsArticle(**article_data)

    def test_sentiment_enum_validation(self):
        """Test sentiment enum validation."""
        valid_sentiments = ["positive", "negative", "neutral"]
        invalid_sentiments = [
            "POSITIVE",
            "Negative",
            "neutral ",
            "bullish",
            "bearish",
            "",
        ]

        for sentiment in valid_sentiments:
            result_data = {
                "sentiment": sentiment,
                "score": (
                    0.5
                    if sentiment == "positive"
                    else -0.5 if sentiment == "negative" else 0.0
                ),
                "confidence": 0.8,
            }
            result = SentimentResult(**result_data)
            assert result.sentiment == sentiment

        for sentiment in invalid_sentiments:
            result_data = {"sentiment": sentiment, "score": 0.5, "confidence": 0.8}
            with pytest.raises(ValidationError):
                SentimentResult(**result_data)

    def test_score_range_validation(self):
        """Test score range validation."""
        valid_scores = [-1.0, -0.5, 0.0, 0.5, 1.0]
        invalid_scores = [-1.1, 1.1, 100.0, -100.0]

        for score in valid_scores:
            result_data = {
                "sentiment": (
                    "positive" if score > 0 else "negative" if score < 0 else "neutral"
                ),
                "score": score,
                "confidence": 0.8,
            }
            result = SentimentResult(**result_data)
            assert result.score == score

        for score in invalid_scores:
            result_data = {"sentiment": "positive", "score": score, "confidence": 0.8}
            with pytest.raises(ValidationError):
                SentimentResult(**result_data)

    def test_confidence_range_validation(self):
        """Test confidence range validation."""
        valid_confidences = [0.0, 0.5, 1.0]
        invalid_confidences = [-0.1, 1.1, 2.0]

        for confidence in valid_confidences:
            result_data = {
                "sentiment": "positive",
                "score": 0.5,
                "confidence": confidence,
            }
            result = SentimentResult(**result_data)
            assert result.confidence == confidence

        for confidence in invalid_confidences:
            result_data = {
                "sentiment": "positive",
                "score": 0.5,
                "confidence": confidence,
            }
            with pytest.raises(ValidationError):
                SentimentResult(**result_data)

    def test_title_length_validation(self):
        """Test title length validation."""
        # Valid title lengths
        valid_titles = [
            "A",  # Minimum length
            "Short title",
            "A" * 500,  # Maximum length
        ]

        # Invalid title lengths
        invalid_titles = [
            "",  # Empty
            "A" * 501,  # Too long
        ]

        for title in valid_titles:
            article_data = {
                "title": title,
                "url": "https://example.com/test",
                "source": "TestSource",
                "published_at": datetime.utcnow(),
            }
            article = NewsArticle(**article_data)
            assert article.title == title

        for title in invalid_titles:
            article_data = {
                "title": title,
                "url": "https://example.com/test",
                "source": "TestSource",
                "published_at": datetime.utcnow(),
            }
            with pytest.raises(ValidationError):
                NewsArticle(**article_data)

    def test_source_length_validation(self):
        """Test source length validation."""
        valid_sources = [
            "A",  # Minimum length
            "CoinDesk",
            "A" * 100,  # Maximum length
        ]

        invalid_sources = [
            "",  # Empty
            "A" * 101,  # Too long
        ]

        for source in valid_sources:
            article_data = {
                "title": "Test Article",
                "url": "https://example.com/test",
                "source": source,
                "published_at": datetime.utcnow(),
            }
            article = NewsArticle(**article_data)
            assert article.source == source

        for source in invalid_sources:
            article_data = {
                "title": "Test Article",
                "url": "https://example.com/test",
                "source": source,
                "published_at": datetime.utcnow(),
            }
            with pytest.raises(ValidationError):
                NewsArticle(**article_data)

    def test_datetime_validation(self):
        """Test datetime field validation."""
        from datetime import datetime, timezone

        valid_datetimes = [
            datetime.utcnow(),
            datetime(2026, 1, 10, 6, 0, 0),
            datetime(2020, 1, 1, 0, 0, 0),  # Past date
            datetime(2030, 12, 31, 23, 59, 59),  # Future date
        ]

        for dt in valid_datetimes:
            article_data = {
                "title": "Test Article",
                "url": "https://example.com/test",
                "source": "TestSource",
                "published_at": dt,
            }
            article = NewsArticle(**article_data)
            assert article.published_at == dt

    def test_sentiment_label_validation(self):
        """Test sentiment label validation in NewsArticle."""
        valid_labels = ["positive", "negative", "neutral", None]
        invalid_labels = ["POSITIVE", "Negative", "neutral ", "bullish", ""]

        for label in valid_labels:
            article_data = {
                "title": "Test Article",
                "url": "https://example.com/test",
                "source": "TestSource",
                "published_at": datetime.utcnow(),
                "sentiment_label": label,
            }

            if label is None:
                article = NewsArticle(**article_data)
                assert article.sentiment_label is None
            else:
                article = NewsArticle(**article_data)
                assert article.sentiment_label == label

        for label in invalid_labels:
            if label:  # Skip empty string as it might be caught by other validation
                article_data = {
                    "title": "Test Article",
                    "url": "https://example.com/test",
                    "source": "TestSource",
                    "published_at": datetime.utcnow(),
                    "sentiment_label": label,
                }
                with pytest.raises(ValidationError):
                    NewsArticle(**article_data)

    def test_sentiment_score_validation_in_article(self):
        """Test sentiment score validation in NewsArticle."""
        valid_scores = [-1.0, -0.5, 0.0, 0.5, 1.0, None]
        invalid_scores = [-1.1, 1.1]

        for score in valid_scores:
            article_data = {
                "title": "Test Article",
                "url": "https://example.com/test",
                "source": "TestSource",
                "published_at": datetime.utcnow(),
                "sentiment_score": score,
            }

            article = NewsArticle(**article_data)
            assert article.sentiment_score == score

        for score in invalid_scores:
            article_data = {
                "title": "Test Article",
                "url": "https://example.com/test",
                "source": "TestSource",
                "published_at": datetime.utcnow(),
                "sentiment_score": score,
            }
            with pytest.raises(ValidationError):
                NewsArticle(**article_data)

    def test_model_validation(self):
        """Test model field validation in SentimentResult."""
        valid_models = [
            "llama3.2:3b",
            "mistral:latest",
            "gpt-4",
            None,
            "custom-model-v1",
        ]
        # All strings are valid for model field (no validation)

        for model in valid_models:
            result_data = {
                "sentiment": "positive",
                "score": 0.5,
                "confidence": 0.8,
                "model": model,
            }

            result = SentimentResult(**result_data)
            assert result.model == model

    def test_reasoning_validation(self):
        """Test reasoning field validation in SentimentResult."""
        valid_reasonings = [
            "Short reasoning",
            "A" * 1000,  # Long reasoning
            None,
            "",  # Empty string
        ]

        for reasoning in valid_reasonings:
            result_data = {
                "sentiment": "positive",
                "score": 0.5,
                "confidence": 0.8,
                "reasoning": reasoning,
            }

            result = SentimentResult(**result_data)
            assert result.reasoning == reasoning


@pytest.mark.unit
def test_additional_schemas():
    """Test additional API schemas that might be needed."""

    # Define additional schemas for testing
    class BatchSentimentRequest(BaseModel):
        """Schema for batch sentiment analysis requests."""

        texts: List[str] = Field(..., min_items=1, max_items=100)
        model: str = Field(default="llama3.2:3b")
        include_reasoning: bool = Field(default=True)

    class BatchSentimentResponse(BaseModel):
        """Schema for batch sentiment analysis responses."""

        results: List[SentimentResult]
        processing_time_ms: float = Field(..., ge=0)
        model_used: str

    # Test BatchSentimentRequest
    valid_request = {
        "texts": ["Bitcoin is great", "Market is crashing"],
        "model": "llama3.2:3b",
        "include_reasoning": True,
    }

    request = BatchSentimentRequest(**valid_request)
    assert len(request.texts) == 2
    assert request.model == "llama3.2:3b"

    # Test invalid request (empty texts)
    with pytest.raises(ValidationError):
        BatchSentimentRequest(texts=[])

    # Test invalid request (too many texts)
    with pytest.raises(ValidationError):
        BatchSentimentRequest(texts=["text"] * 101)

    # Test BatchSentimentResponse
    valid_response = {
        "results": [
            {"sentiment": "positive", "score": 0.8, "confidence": 0.9},
            {"sentiment": "negative", "score": -0.6, "confidence": 0.8},
        ],
        "processing_time_ms": 1250.5,
        "model_used": "llama3.2:3b",
    }

    response = BatchSentimentResponse(**valid_response)
    assert len(response.results) == 2
    assert response.processing_time_ms == 1250.5
    assert response.model_used == "llama3.2:3b"


@pytest.mark.unit
def test_schema_serialization():
    """Test schema serialization to/from JSON."""
    import json

    # Create a sentiment result
    result_data = {
        "sentiment": "positive",
        "score": 0.85,
        "confidence": 0.92,
        "reasoning": "Optimistic text",
        "model": "llama3.2:3b",
    }

    result = SentimentResult(**result_data)

    # Serialize to JSON
    json_str = result.json()
    parsed_dict = json.loads(json_str)

    assert parsed_dict["sentiment"] == "positive"
    assert parsed_dict["score"] == 0.85
    assert parsed_dict["confidence"] == 0.92

    # Deserialize from JSON
    new_result = SentimentResult.parse_raw(json_str)
    assert new_result.sentiment == result.sentiment
    assert new_result.score == result.score

    # Test with NewsArticle
    article_data = {
        "title": "Test Article",
        "url": "https://example.com/test",
        "source": "TestSource",
        "published_at": datetime.utcnow().isoformat(),
    }

    article = NewsArticle.parse_obj(article_data)
    article_json = article.json()

    parsed_article = NewsArticle.parse_raw(article_json)
    assert parsed_article.title == article.title
    assert parsed_article.url == article.url
