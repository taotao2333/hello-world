import logging
from datetime import datetime

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NewsArticle
from app.collectors.news_collector import NewsCollector
from app.analyzers.news_analyzer import NewsAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

_latest_analyzed_news = []
_latest_sector_sentiment = {}


@router.get("/news", response_class=HTMLResponse)
async def news_page(request: Request, db: Session = Depends(get_db)):
    articles = _latest_analyzed_news
    sector_sentiment = _latest_sector_sentiment

    if not articles:
        db_articles = (
            db.query(NewsArticle)
            .order_by(NewsArticle.collected_at.desc())
            .limit(100)
            .all()
        )
        articles = [
            {
                "title": a.title,
                "summary": a.summary,
                "source": a.source,
                "sentiment_score": a.sentiment_score,
                "related_sectors": a.related_sectors or "",
                "is_policy": a.is_policy,
                "is_international": a.is_international,
                "category": a.category,
            }
            for a in db_articles
        ]

    return templates.TemplateResponse("news.html", {
        "request": request,
        "active": "news",
        "articles": articles,
        "sector_sentiment": sector_sentiment,
    })


@router.post("/api/collect")
async def collect_news(db: Session = Depends(get_db)):
    global _latest_analyzed_news, _latest_sector_sentiment
    try:
        collector = NewsCollector()
        analyzer = NewsAnalyzer()

        raw = collector.collect_all()
        analyzed = [analyzer.analyze(a) for a in raw]

        for a in analyzed:
            article = NewsArticle(
                title=a.get("title", ""),
                summary=a.get("summary", ""),
                source=a.get("source", ""),
                url=a.get("url", ""),
                published_at=a.get("published_at"),
                collected_at=datetime.now(),
                category=a.get("category", "综合"),
                sentiment_score=a.get("sentiment_score", 0),
                related_sectors=a.get("related_sectors", ""),
                is_policy=a.get("is_policy", False),
                is_international=a.get("is_international", False),
                keywords=a.get("keywords", ""),
            )
            db.add(article)
        db.commit()

        _latest_analyzed_news = analyzed
        _latest_sector_sentiment = analyzer.aggregate_sector_sentiment(analyzed)

        logger.info(f"采集并分析了 {len(analyzed)} 条新闻")
    except Exception as e:
        logger.error(f"采集新闻失败: {e}", exc_info=True)

    return RedirectResponse(url="/news", status_code=303)
