from datetime import datetime, date
from sqlalchemy import String, Text, Float, Integer, Date, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    category: Mapped[str] = mapped_column(String(50), nullable=True)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    related_sectors: Mapped[str] = mapped_column(Text, nullable=True)
    is_policy: Mapped[bool] = mapped_column(Boolean, default=False)
    is_international: Mapped[bool] = mapped_column(Boolean, default=False)
    keywords: Mapped[str] = mapped_column(Text, nullable=True)


class StockData(Base):
    __tablename__ = "stock_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    open_price: Mapped[float] = mapped_column(Float, nullable=True)
    close_price: Mapped[float] = mapped_column(Float, nullable=True)
    high_price: Mapped[float] = mapped_column(Float, nullable=True)
    low_price: Mapped[float] = mapped_column(Float, nullable=True)
    volume: Mapped[float] = mapped_column(Float, nullable=True)
    turnover: Mapped[float] = mapped_column(Float, nullable=True)
    change_pct: Mapped[float] = mapped_column(Float, nullable=True)
    sector: Mapped[str] = mapped_column(String(50), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prediction_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False)
    stock_name: Mapped[str] = mapped_column(String(50), nullable=False)
    sector: Mapped[str] = mapped_column(String(50), nullable=True)
    predicted_direction: Mapped[str] = mapped_column(String(10), nullable=False)
    predicted_change_pct: Mapped[float] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    reasoning: Mapped[str] = mapped_column(Text, nullable=True)
    news_factors: Mapped[str] = mapped_column(Text, nullable=True)
    technical_factors: Mapped[str] = mapped_column(Text, nullable=True)
    actual_change_pct: Mapped[float] = mapped_column(Float, nullable=True)
    is_accurate: Mapped[bool] = mapped_column(Boolean, nullable=True)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class DailyReview(Base):
    __tablename__ = "daily_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_predictions: Mapped[int] = mapped_column(Integer, default=0)
    accurate_count: Mapped[int] = mapped_column(Integer, default=0)
    accuracy_rate: Mapped[float] = mapped_column(Float, default=0.0)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    accurate_reasons: Mapped[str] = mapped_column(Text, nullable=True)
    inaccurate_reasons: Mapped[str] = mapped_column(Text, nullable=True)
    market_summary: Mapped[str] = mapped_column(Text, nullable=True)
    lessons_learned: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
