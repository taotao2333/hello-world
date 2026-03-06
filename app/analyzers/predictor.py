import logging
from datetime import date, datetime

from app.analyzers.news_analyzer import NewsAnalyzer
from app.analyzers.stock_analyzer import StockAnalyzer
from app.collectors.news_collector import NewsCollector
from app.collectors.stock_collector import StockCollector

logger = logging.getLogger(__name__)


class StockPredictor:
    """综合新闻面和技术面生成预测"""

    def __init__(self):
        self.news_collector = NewsCollector()
        self.news_analyzer = NewsAnalyzer()
        self.stock_collector = StockCollector()
        self.stock_analyzer = StockAnalyzer()

    def generate_predictions(self) -> dict:
        logger.info("开始生成预测...")

        raw_news = self.news_collector.collect_all()
        analyzed_news = [self.news_analyzer.analyze(a) for a in raw_news]
        sector_sentiment = self.news_analyzer.aggregate_sector_sentiment(analyzed_news)

        market = self.stock_collector.get_market_overview()

        predictions = []
        sector_analyses = {}

        for sector_name, sentiment_data in sector_sentiment.items():
            avg_sentiment = sentiment_data.get("avg_sentiment", 0)
            news_count = sentiment_data.get("count", 0)

            hot_sectors = market.get("hot_sectors", [])
            market_sector = next(
                (s for s in hot_sectors if sector_name in s.get("name", "")),
                None,
            )

            stocks = self.stock_collector.get_sector_stocks(sector_name, limit=5)
            if not stocks and market_sector:
                stocks = self.stock_collector.get_sector_stocks(
                    market_sector.get("name", ""), limit=5
                )

            stock_predictions = []
            for stock in stocks[:3]:
                hist = self.stock_collector.get_stock_history(stock["code"], days=30)
                tech = self.stock_analyzer.analyze_stock(hist)
                signal = self.stock_analyzer.generate_technical_signal(tech)

                combined_score = self._combine_scores(
                    avg_sentiment, signal.get("score", 0), news_count
                )

                direction = "涨" if combined_score > 0 else "跌" if combined_score < 0 else "平"
                pct = self._estimate_change(combined_score, tech)

                reasoning = self._build_reasoning(
                    sector_name, avg_sentiment, signal, sentiment_data, stock
                )

                pred = {
                    "prediction_date": date.today().isoformat(),
                    "target_date": self._next_trading_day().isoformat(),
                    "stock_code": stock["code"],
                    "stock_name": stock["name"],
                    "sector": sector_name,
                    "predicted_direction": direction,
                    "predicted_change_pct": pct,
                    "confidence": min(abs(combined_score) / 5, 1.0),
                    "reasoning": reasoning,
                    "news_factors": "; ".join(sentiment_data.get("articles", [])[:3]),
                    "technical_factors": "; ".join(signal.get("factors", [])),
                    "current_price": stock.get("price", 0),
                    "today_change": stock.get("change_pct", 0),
                }
                stock_predictions.append(pred)
                predictions.append(pred)

            sector_analyses[sector_name] = {
                "sentiment": avg_sentiment,
                "news_count": news_count,
                "stocks": stock_predictions,
            }

        predictions.sort(key=lambda x: abs(x.get("predicted_change_pct", 0)), reverse=True)

        policy_news = [a for a in analyzed_news if a.get("is_policy")]
        intl_news = [a for a in analyzed_news if a.get("is_international")]

        return {
            "date": date.today().isoformat(),
            "market_overview": market,
            "total_news": len(analyzed_news),
            "policy_news_count": len(policy_news),
            "international_news_count": len(intl_news),
            "sector_analyses": sector_analyses,
            "predictions": predictions[:20],
            "policy_news": [{"title": n["title"], "sentiment": n["sentiment_score"]} for n in policy_news[:10]],
            "international_news": [{"title": n["title"], "sentiment": n["sentiment_score"]} for n in intl_news[:10]],
            "generated_at": datetime.now().isoformat(),
        }

    def _combine_scores(self, sentiment: float, tech_score: int, news_count: int) -> float:
        news_weight = min(news_count / 5, 1.0) * 0.4
        tech_weight = 0.6
        combined = sentiment * news_weight * 5 + tech_score * tech_weight
        return round(combined, 2)

    def _estimate_change(self, score: float, tech: dict) -> float:
        base = score * 0.5
        if tech.get("valid"):
            vol_ratio = tech.get("vol_ratio", 1)
            if vol_ratio > 2:
                base *= 1.3
        return round(max(min(base, 5.0), -5.0), 2)

    def _next_trading_day(self) -> date:
        from datetime import timedelta
        d = date.today() + timedelta(days=1)
        while d.weekday() >= 5:
            d += timedelta(days=1)
        return d

    def _build_reasoning(self, sector, sentiment, signal, sentiment_data, stock) -> str:
        parts = []
        parts.append(f"【板块】{sector}")
        parts.append(f"【新闻情感】平均情感分 {sentiment:.2f}，"
                     f"正面 {sentiment_data.get('positive', 0)} 条，"
                     f"负面 {sentiment_data.get('negative', 0)} 条")
        parts.append(f"【技术信号】{signal.get('signal', '无')}（分数 {signal.get('score', 0)}）")
        if signal.get("factors"):
            parts.append(f"【技术因素】{'；'.join(signal['factors'])}")
        parts.append(f"【当前价格】{stock.get('price', 0)} 元，今日涨跌 {stock.get('change_pct', 0)}%")
        return "\n".join(parts)
