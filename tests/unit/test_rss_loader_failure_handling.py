"""
Unit tests for RSS feed loader with silent failure prevention.

Tests that the loader properly handles and reports failures instead of
silently returning empty data.
"""

from unittest.mock import Mock, patch

import feedparser
import pandas as pd
import pytest


class TestRSSFeedLoaderErrorMessages:
    """測試錯誤訊息的品質"""

    # Mage pipeline legacy import removed
    def test_error_message_includes_source_names(self, mock_parse):
        """
        Test: Error message should include the names of failed sources
        """
        mock_parse.side_effect = Exception("Connection timeout")

        from mage_pipeline.alphapulse.data_loaders.load_rss_feeds import load_rss_feeds

        with pytest.raises(RuntimeError) as exc_info:
            load_rss_feeds()

        error_message = str(exc_info.value)

        # 驗證錯誤訊息包含重要資訊
        assert "CoinDesk" in error_message
        assert "Cointelegraph" in error_message
        assert "2/2" in error_message  # 顯示失敗比例

    @patch("feedparser.parse")
    def test_success_message_includes_statistics(self, mock_parse, caplog):
        """
        測試：成功訊息應該包含統計資訊
        """
        mock_feed = Mock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                "title": "Article 1",
                "link": "https://example.com/1",
                "summary": "Summary 1",
                # Mage pipeline legacy import removed
            }
        ]

        mock_parse.return_value = mock_feed

        from mage_pipeline.alphapulse.data_loaders.load_rss_feeds import load_rss_feeds

        with caplog.at_level("INFO"):
            df = load_rss_feeds()

        # 驗證日誌包含統計資訊
        log_messages = [record.message for record in caplog.records]

        # 應該包含文章數量
        assert any("Successfully loaded" in msg for msg in log_messages)
        # 應該包含來源分布
        assert any("Source distribution" in msg for msg in log_messages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
