import logging
from datetime import date

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NewsArticle, Prediction, DailyReview
from app.collectors.stock_collector import StockCollector

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    total_news = db.query(NewsArticle).count()
    total_predictions = db.query(Prediction).filter(
        Prediction.prediction_date == date.today()
    ).count()
    latest_review = (
        db.query(DailyReview).order_by(DailyReview.review_date.desc()).first()
    )
    accuracy_rate = latest_review.accuracy_rate if latest_review else "--"

    market = {}
    try:
        sc = StockCollector()
        market = sc.get_market_overview()
    except Exception as e:
        logger.warning(f"获取大盘数据失败: {e}")

    return templates.TemplateResponse("index.html", {
        "request": request,
        "active": "home",
        "stats": {
            "total_news": total_news,
            "total_predictions": total_predictions,
            "accuracy_rate": accuracy_rate,
        },
        "market": market,
    })
