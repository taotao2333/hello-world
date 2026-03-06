import pytest
from app.config import SECTOR_KEYWORDS, SENTIMENT_POSITIVE, SENTIMENT_NEGATIVE
from app.analyzers.news_analyzer import NewsAnalyzer
from app.analyzers.stock_analyzer import StockAnalyzer
import pandas as pd
import numpy as np


class TestNewsAnalyzer:
    def setup_method(self):
        self.analyzer = NewsAnalyzer()

    def test_positive_sentiment(self):
        article = {"title": "新能源行业迎来利好政策 增长加速", "summary": "国务院发布支持新能源发展意见"}
        result = self.analyzer.analyze(article)
        assert result["sentiment_score"] > 0
        assert "新能源" in result["related_sectors"]
        assert result["is_policy"] is True

    def test_negative_sentiment(self):
        article = {"title": "某公司涉嫌违规被处罚 股价暴跌", "summary": "证监会调查发现亏损严重"}
        result = self.analyzer.analyze(article)
        assert result["sentiment_score"] < 0

    def test_neutral_sentiment(self):
        article = {"title": "今日天气晴朗", "summary": "适合出行"}
        result = self.analyzer.analyze(article)
        assert result["sentiment_score"] == 0.0

    def test_sector_identification(self):
        article = {"title": "芯片半导体行业迎来新机遇", "summary": ""}
        result = self.analyzer.analyze(article)
        assert "半导体" in result["related_sectors"]

    def test_international_detection(self):
        article = {"title": "美联储宣布加息25基点", "summary": "美元走强"}
        result = self.analyzer.analyze(article)
        assert result["is_international"] is True

    def test_sector_sentiment_aggregation(self):
        articles = [
            self.analyzer.analyze({"title": "新能源利好 增长", "summary": ""}),
            self.analyzer.analyze({"title": "新能源政策支持", "summary": ""}),
            self.analyzer.analyze({"title": "光伏下跌 亏损", "summary": ""}),
        ]
        agg = self.analyzer.aggregate_sector_sentiment(articles)
        assert "新能源" in agg
        assert agg["新能源"]["count"] == 3


class TestStockAnalyzer:
    def setup_method(self):
        self.analyzer = StockAnalyzer()

    def test_empty_dataframe(self):
        result = self.analyzer.analyze_stock(pd.DataFrame())
        assert result["valid"] is False

    def test_valid_analysis(self):
        dates = pd.date_range("2024-01-01", periods=30)
        prices = np.random.uniform(10, 15, 30)
        prices = np.sort(prices)
        df = pd.DataFrame({
            "日期": dates,
            "收盘": prices,
            "最高": prices + 0.5,
            "最低": prices - 0.5,
            "成交量": np.random.uniform(1000, 5000, 30),
        })
        result = self.analyzer.analyze_stock(df)
        assert result["valid"] is True
        assert "latest_close" in result
        assert "rsi" in result
        assert "trend" in result

    def test_technical_signal(self):
        analysis = {
            "valid": True,
            "rsi": 25,
            "macd_hist": 0.5,
            "trend": "金叉突破",
            "vol_ratio": 3.0,
        }
        signal = self.analyzer.generate_technical_signal(analysis)
        assert signal["signal"] == "看多"
        assert signal["score"] > 0

    def test_bearish_signal(self):
        analysis = {
            "valid": True,
            "rsi": 75,
            "macd_hist": -0.5,
            "trend": "死叉回落",
            "vol_ratio": 1.0,
        }
        signal = self.analyzer.generate_technical_signal(analysis)
        assert signal["signal"] == "看空"
        assert signal["score"] < 0


class TestConfig:
    def test_sector_keywords_not_empty(self):
        assert len(SECTOR_KEYWORDS) > 0
        for sector, keywords in SECTOR_KEYWORDS.items():
            assert len(keywords) > 0

    def test_sentiment_words(self):
        assert len(SENTIMENT_POSITIVE) > 0
        assert len(SENTIMENT_NEGATIVE) > 0
