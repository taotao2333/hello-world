import logging
from app.config import (
    SECTOR_KEYWORDS,
    POLICY_KEYWORDS,
    SENTIMENT_POSITIVE,
    SENTIMENT_NEGATIVE,
    INTERNATIONAL_KEYWORDS,
)

logger = logging.getLogger(__name__)


class NewsAnalyzer:
    """分析新闻情感、行业关联和政策影响"""

    def analyze(self, article: dict) -> dict:
        text = f"{article.get('title', '')} {article.get('summary', '')}"

        sentiment = self._analyze_sentiment(text)
        sectors = self._identify_sectors(text)
        is_policy = self._is_policy_related(text)
        is_international = self._is_international(text)
        keywords = self._extract_keywords(text)

        return {
            **article,
            "sentiment_score": sentiment,
            "related_sectors": ",".join(sectors),
            "is_policy": is_policy,
            "is_international": is_international,
            "keywords": ",".join(keywords),
            "category": self._categorize(is_policy, is_international, sectors),
        }

    def _analyze_sentiment(self, text: str) -> float:
        pos_count = sum(1 for w in SENTIMENT_POSITIVE if w in text)
        neg_count = sum(1 for w in SENTIMENT_NEGATIVE if w in text)
        total = pos_count + neg_count
        if total == 0:
            return 0.0
        return round((pos_count - neg_count) / total, 2)

    def _identify_sectors(self, text: str) -> list[str]:
        matched = []
        for sector, keywords in SECTOR_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                matched.append(sector)
        return matched

    def _is_policy_related(self, text: str) -> bool:
        return any(kw in text for kw in POLICY_KEYWORDS)

    def _is_international(self, text: str) -> bool:
        return any(kw in text for kw in INTERNATIONAL_KEYWORDS)

    def _extract_keywords(self, text: str) -> list[str]:
        try:
            import jieba.analyse
            return jieba.analyse.extract_tags(text, topK=10)
        except Exception:
            return []

    def _categorize(self, is_policy: bool, is_international: bool, sectors: list) -> str:
        if is_policy:
            return "政策"
        if is_international:
            return "国际"
        if sectors:
            return "行业"
        return "综合"

    def aggregate_sector_sentiment(self, analyzed_articles: list[dict]) -> dict[str, dict]:
        """汇总各板块的新闻情感"""
        sector_data = {}
        for article in analyzed_articles:
            sectors = article.get("related_sectors", "").split(",")
            sentiment = article.get("sentiment_score", 0)
            for sector in sectors:
                sector = sector.strip()
                if not sector:
                    continue
                if sector not in sector_data:
                    sector_data[sector] = {
                        "count": 0,
                        "total_sentiment": 0,
                        "positive": 0,
                        "negative": 0,
                        "articles": [],
                    }
                sector_data[sector]["count"] += 1
                sector_data[sector]["total_sentiment"] += sentiment
                if sentiment > 0:
                    sector_data[sector]["positive"] += 1
                elif sentiment < 0:
                    sector_data[sector]["negative"] += 1
                sector_data[sector]["articles"].append(article.get("title", ""))

        for sector in sector_data:
            count = sector_data[sector]["count"]
            if count > 0:
                sector_data[sector]["avg_sentiment"] = round(
                    sector_data[sector]["total_sentiment"] / count, 2
                )
            else:
                sector_data[sector]["avg_sentiment"] = 0

        return sector_data
