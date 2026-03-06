import logging
from datetime import date

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.reviewers.review import PredictionReviewer

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

_latest_review = None


@router.get("/review", response_class=HTMLResponse)
async def review_page(request: Request, db: Session = Depends(get_db)):
    reviewer = PredictionReviewer()
    history = reviewer.get_history(db)
    return templates.TemplateResponse("review.html", {
        "request": request,
        "active": "review",
        "review": _latest_review,
        "history": history,
    })


@router.post("/api/review")
async def execute_review(db: Session = Depends(get_db)):
    global _latest_review
    try:
        reviewer = PredictionReviewer()
        result = reviewer.review_predictions(db, target_date=date.today())
        _latest_review = result
        logger.info(f"复盘完成: {result.get('total_predictions', 0)} 条预测")
    except Exception as e:
        logger.error(f"复盘失败: {e}", exc_info=True)

    return RedirectResponse(url="/review", status_code=303)


@router.get("/api/review")
async def get_review_api(db: Session = Depends(get_db)):
    return _latest_review or {"message": "暂无复盘数据"}
