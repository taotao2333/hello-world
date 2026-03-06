import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import dashboard, predictions, news, reviews

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="股智先知 - A股智能分析预测系统", version="1.0.0")

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(dashboard.router)
app.include_router(predictions.router)
app.include_router(news.router)
app.include_router(reviews.router)


@app.on_event("startup")
async def startup():
    logger.info("初始化数据库...")
    init_db()
    logger.info("股智先知启动完成！")


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "股智先知"}
