import logging
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models import Prediction, DailyReview
from app.collectors.stock_collector import StockCollector

logger = logging.getLogger(__name__)


class PredictionReviewer:
    """每日复盘：对比预测与实际结果"""

    def __init__(self):
        self.stock_collector = StockCollector()

    def review_predictions(self, db: Session, target_date: date = None) -> dict:
        if target_date is None:
            target_date = date.today()

        predictions = (
            db.query(Prediction)
            .filter(Prediction.target_date == target_date, Prediction.reviewed == False)
            .all()
        )

        if not predictions:
            return {
                "target_date": target_date.isoformat(),
                "message": "没有找到待复盘的预测",
                "predictions": [],
            }

        results = []
        accurate_count = 0
        accurate_reasons = []
        inaccurate_reasons = []

        for pred in predictions:
            actual = self._get_actual_change(pred.stock_code, target_date)
            if actual is None:
                continue

            pred.actual_change_pct = actual
            is_accurate = self._check_accuracy(pred.predicted_direction, actual)
            pred.is_accurate = is_accurate
            pred.reviewed = True

            if is_accurate:
                accurate_count += 1

            reason = self._analyze_reason(pred, actual, is_accurate)

            if is_accurate:
                accurate_reasons.append(reason)
            else:
                inaccurate_reasons.append(reason)

            results.append({
                "stock_code": pred.stock_code,
                "stock_name": pred.stock_name,
                "sector": pred.sector,
                "predicted_direction": pred.predicted_direction,
                "predicted_change_pct": pred.predicted_change_pct,
                "actual_change_pct": actual,
                "is_accurate": is_accurate,
                "reason": reason,
            })

        total = len(results)
        accuracy = round(accurate_count / total * 100, 1) if total > 0 else 0

        review = DailyReview(
            review_date=date.today(),
            target_date=target_date,
            total_predictions=total,
            accurate_count=accurate_count,
            accuracy_rate=accuracy,
            summary=f"共 {total} 条预测，准确 {accurate_count} 条，准确率 {accuracy}%",
            accurate_reasons="\n".join(accurate_reasons),
            inaccurate_reasons="\n".join(inaccurate_reasons),
            market_summary=self._get_market_summary(),
            lessons_learned=self._extract_lessons(results),
        )
        db.add(review)
        db.commit()

        return {
            "target_date": target_date.isoformat(),
            "total_predictions": total,
            "accurate_count": accurate_count,
            "accuracy_rate": accuracy,
            "results": results,
            "accurate_reasons": accurate_reasons,
            "inaccurate_reasons": inaccurate_reasons,
            "market_summary": review.market_summary,
            "lessons_learned": review.lessons_learned,
        }

    def _get_actual_change(self, code: str, target_date: date) -> float | None:
        try:
            hist = self.stock_collector.get_stock_history(code, days=5)
            if hist is None or hist.empty:
                return None
            date_col = "日期" if "日期" in hist.columns else "date"
            change_col = "涨跌幅" if "涨跌幅" in hist.columns else "change_pct"
            hist[date_col] = hist[date_col].astype(str)
            target_str = target_date.strftime("%Y-%m-%d")
            row = hist[hist[date_col] == target_str]
            if not row.empty:
                return float(row[change_col].iloc[0])
            if not hist.empty:
                return float(hist[change_col].iloc[-1])
        except Exception as e:
            logger.warning(f"获取 {code} 实际涨跌失败: {e}")
        return None

    def _check_accuracy(self, predicted_dir: str, actual: float) -> bool:
        if predicted_dir == "涨" and actual > 0:
            return True
        if predicted_dir == "跌" and actual < 0:
            return True
        if predicted_dir == "平" and abs(actual) < 0.5:
            return True
        return False

    def _analyze_reason(self, pred: Prediction, actual: float, is_accurate: bool) -> str:
        parts = [f"[{pred.stock_name}({pred.stock_code})]"]
        parts.append(f"预测{pred.predicted_direction}{abs(pred.predicted_change_pct or 0):.1f}%，"
                     f"实际{'涨' if actual > 0 else '跌'}{abs(actual):.2f}%")

        if is_accurate:
            parts.append("✅ 预测准确")
            if pred.reasoning:
                reasons = pred.reasoning.split("\n")
                key_reason = next((r for r in reasons if "新闻情感" in r or "技术信号" in r), "")
                if key_reason:
                    parts.append(f"准确原因: {key_reason.strip()}")
        else:
            parts.append("❌ 预测不准确")
            if pred.predicted_direction == "涨" and actual < 0:
                parts.append("不准确原因: 可能受到盘中利空消息影响，或技术面阻力位压制")
            elif pred.predicted_direction == "跌" and actual > 0:
                parts.append("不准确原因: 可能有新的利好刺激，或超跌后技术性反弹")
            else:
                parts.append("不准确原因: 市场波动超出预期范围")

        return " | ".join(parts)

    def _get_market_summary(self) -> str:
        try:
            market = self.stock_collector.get_market_overview()
            indices = market.get("indices", [])
            parts = []
            for idx in indices:
                parts.append(f"{idx['name']}: {idx['price']} ({idx['change_pct']:+.2f}%)")
            return " | ".join(parts) if parts else "无市场数据"
        except Exception:
            return "获取市场概况失败"

    def _extract_lessons(self, results: list[dict]) -> str:
        if not results:
            return "无数据"
        accurate = [r for r in results if r["is_accurate"]]
        inaccurate = [r for r in results if not r["is_accurate"]]
        lessons = []
        if accurate:
            sectors = set(r.get("sector", "") for r in accurate)
            lessons.append(f"准确板块: {', '.join(sectors)}")
        if inaccurate:
            sectors = set(r.get("sector", "") for r in inaccurate)
            lessons.append(f"失误板块: {', '.join(sectors)}")
        total = len(results)
        acc = len(accurate)
        lessons.append(f"总体准确率: {acc}/{total} = {acc/total*100:.1f}%")
        return "; ".join(lessons)

    def get_history(self, db: Session, limit: int = 30) -> list[dict]:
        reviews = (
            db.query(DailyReview)
            .order_by(DailyReview.review_date.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "review_date": r.review_date.isoformat(),
                "target_date": r.target_date.isoformat(),
                "total_predictions": r.total_predictions,
                "accurate_count": r.accurate_count,
                "accuracy_rate": r.accuracy_rate,
                "summary": r.summary,
                "lessons_learned": r.lessons_learned,
            }
            for r in reviews
        ]
