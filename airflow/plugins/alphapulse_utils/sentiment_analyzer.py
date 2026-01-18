import pandas as pd
import requests
import json
import re
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    def __init__(self, model="llama3.2:3b", host=None):
        self.model = model
        self.host = host or os.getenv("OLLAMA_HOST", "http://ollama:11434")

    def _clean_json(self, raw_output):
        # Similar logic to original regex fixes
        json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if not json_match:
            return None
        return json_match.group(0)

    def classify_text(self, text):
        truncated_text = text[:1000]
        prompt = f"""
        Analyze sentiment of this cryptocurrency news article.
        Return ONLY valid JSON: {{"sentiment_score": -1.0 to 1.0, "confidence": 0.0 to 1.0, "label": "positive"/"neutral"/"negative"}}
        Article: {truncated_text}
        """

        try:
            # First ensure model is pulled (basic check, usually done at setup)
            # For this execution we assume model exists or we trigger pull

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",  # Ollama supports json mode now
            }

            response = requests.post(
                f"{self.host}/api/generate", json=payload, timeout=60
            )
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.text}")
                return {"sentiment_score": 0.0, "confidence": 0.0, "label": "neutral"}

            data = response.json()
            response_text = data.get("response", "")

            try:
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                # Fallback to regex cleaning if JSON mode failed or returned extra text
                cleaned = self._clean_json(response_text)
                if cleaned:
                    return json.loads(cleaned)
                return {"sentiment_score": 0.0, "confidence": 0.0, "label": "neutral"}

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {"sentiment_score": 0.0, "confidence": 0.0, "label": "neutral"}

    def analyze_dataframe(self, df):
        if df.empty:
            return df

        results = []
        for idx, row in df.iterrows():
            text = row.get("text_for_analysis") or (
                row.get("title", "") + ". " + row.get("summary", "")
            )
            res = self.classify_text(text)
            results.append(res)

        result_df = pd.DataFrame(
            {
                "article_id": df["id"].values,
                "sentiment_score": [r.get("sentiment_score", 0) for r in results],
                "confidence": [r.get("confidence", 0) for r in results],
                "label": [r.get("label", "neutral") for r in results],
                "analyzed_at": datetime.now(),
            }
        )

        return result_df
