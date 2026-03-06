import json
import logging
from datetime import date

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Prediction
from app.analyzers.predictor import StockPredictor

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

_latest_prediction_data = {}


@router.get("/predictions", response_class=HTMLResponse)
async def predictions_page(request: Request, db: Session = Depends(get_db)):
    global _latest_prediction_data
    data = _latest_prediction_data if _latest_prediction_data else {}
    return templates.TemplateResponse("predictions.html", {
        "request": request,
        "active": "predictions",
        "data": data,
    })


@router.post("/api/predict")
async def generate_predictions(db: Session = Depends(get_db)):
    global _latest_prediction_data
    try:
        predictor = StockPredictor()
        result = predictor.generate_predictions()

        for p in result.get("predictions", []):
            pred = Prediction(
                prediction_date=date.fromisoformat(p["prediction_date"]),
                target_date=date.fromisoformat(p["target_date"]),
                stock_code=p["stock_code"],
                stock_name=p["stock_name"],
                sector=p.get("sector", ""),
                predicted_direction=p["predicted_direction"],
                predicted_change_pct=p.get("predicted_change_pct", 0),
                confidence=p.get("confidence", 0.5),
                reasoning=p.get("reasoning", ""),
                news_factors=p.get("news_factors", ""),
                technical_factors=p.get("technical_factors", ""),
            )
            db.add(pred)
        db.commit()

        _latest_prediction_data = result
        logger.info(f"生成了 {len(result.get('predictions', []))} 条预测")
    except Exception as e:
        logger.error(f"生成预测失败: {e}", exc_info=True)

    return RedirectResponse(url="/predictions", status_code=303)


@router.get("/api/predictions")
async def get_predictions_api(db: Session = Depends(get_db)):
    global _latest_prediction_data
    return _latest_prediction_data or {"message": "暂无预测数据"}
