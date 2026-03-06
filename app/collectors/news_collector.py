import logging
from datetime import datetime
from typing import Optional

import feedparser
import httpx

from app.config import NEWS_RSS_FEEDS
from app.models import NewsArticle

logger = logging.getLogger(__name__)


class NewsCollector:
    """采集新闻和政策信息"""

    def __init__(self):
        self.client = httpx.Client(timeout=15.0, follow_redirects=True)

    def collect_from_rss(self) -> list[dict]:
        articles = []
        for source_name, feed_url in NEWS_RSS_FEEDS.items():
            try:
                items = self._parse_feed(feed_url, source_name)
                articles.extend(items)
                logger.info(f"从 {source_name} 采集到 {len(items)} 条新闻")
            except Exception as e:
                logger.warning(f"采集 {source_name} 失败: {e}")
        return articles

    def _parse_feed(self, feed_url: str, source_name: str) -> list[dict]:
        try:
            resp = self.client.get(feed_url)
            feed = feedparser.parse(resp.text)
        except Exception:
            feed = feedparser.parse(feed_url)

        items = []
        for entry in feed.entries[:20]:
            published = self._parse_date(entry.get("published", ""))
            items.append({
                "title": entry.get("title", "").strip(),
                "summary": entry.get("summary", "").strip()[:500],
                "source": source_name,
                "url": entry.get("link", ""),
                "published_at": published,
                "collected_at": datetime.now(),
            })
        return items

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            pass
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d %H:%M"]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    def collect_from_search(self, keywords: list[str] = None) -> list[dict]:
        """通过关键词搜索收集热点新闻（使用 akshare 新闻接口）"""
        articles = []
        try:
            import akshare as ak
            df = ak.stock_news_em(symbol="全部")
            if df is not None and not df.empty:
                for _, row in df.head(50).iterrows():
                    articles.append({
                        "title": str(row.get("新闻标题", "")),
                        "summary": str(row.get("新闻内容", ""))[:500],
                        "source": str(row.get("文章来源", "东方财富")),
                        "url": str(row.get("新闻链接", "")),
                        "published_at": self._parse_date(str(row.get("发布时间", ""))),
                        "collected_at": datetime.now(),
                    })
                logger.info(f"从财经搜索采集到 {len(articles)} 条新闻")
        except Exception as e:
            logger.warning(f"财经新闻搜索失败: {e}")
        return articles

    def collect_all(self) -> list[dict]:
        all_articles = []
        all_articles.extend(self.collect_from_rss())
        all_articles.extend(self.collect_from_search())
        seen_titles = set()
        unique = []
        for a in all_articles:
            if a["title"] and a["title"] not in seen_titles:
                seen_titles.add(a["title"])
                unique.append(a)
        logger.info(f"总共采集到 {len(unique)} 条去重新闻")
        return unique
