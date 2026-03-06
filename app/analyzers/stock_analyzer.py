import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class StockAnalyzer:
    """股票技术面分析"""

    def analyze_stock(self, df: pd.DataFrame) -> dict:
        if df is None or df.empty or len(df) < 5:
            return {"valid": False}

        try:
            close_col = "收盘" if "收盘" in df.columns else "close"
            high_col = "最高" if "最高" in df.columns else "high"
            low_col = "最低" if "最低" in df.columns else "low"
            vol_col = "成交量" if "成交量" in df.columns else "volume"

            close = df[close_col].astype(float)
            high = df[high_col].astype(float)
            low = df[low_col].astype(float)
            volume = df[vol_col].astype(float)

            ma5 = close.rolling(5).mean()
            ma10 = close.rolling(10).mean()
            ma20 = close.rolling(20).mean()

            latest_close = close.iloc[-1]
            prev_close = close.iloc[-2] if len(close) > 1 else latest_close

            rsi = self._calc_rsi(close, 14)
            macd_line, signal_line, macd_hist = self._calc_macd(close)
            vol_ratio = volume.iloc[-1] / volume.rolling(5).mean().iloc[-1] if volume.rolling(5).mean().iloc[-1] > 0 else 1

            trend = "上涨"
            if len(ma5) > 1 and ma5.iloc[-1] < ma5.iloc[-2]:
                trend = "下跌"
            if len(ma5) > 0 and len(ma10) > 0:
                if ma5.iloc[-1] > ma10.iloc[-1] and (len(ma5) < 2 or ma5.iloc[-2] <= ma10.iloc[-2]):
                    trend = "金叉突破"
                elif ma5.iloc[-1] < ma10.iloc[-1] and (len(ma5) < 2 or ma5.iloc[-2] >= ma10.iloc[-2]):
                    trend = "死叉回落"

            support = low.tail(20).min()
            resistance = high.tail(20).max()

            return {
                "valid": True,
                "latest_close": round(latest_close, 2),
                "change_1d": round((latest_close - prev_close) / prev_close * 100, 2),
                "ma5": round(ma5.iloc[-1], 2) if not np.isnan(ma5.iloc[-1]) else None,
                "ma10": round(ma10.iloc[-1], 2) if len(ma10) > 0 and not np.isnan(ma10.iloc[-1]) else None,
                "ma20": round(ma20.iloc[-1], 2) if len(ma20) > 0 and not np.isnan(ma20.iloc[-1]) else None,
                "rsi": round(rsi, 2) if rsi is not None else None,
                "macd_hist": round(macd_hist, 4) if macd_hist is not None else None,
                "vol_ratio": round(vol_ratio, 2),
                "trend": trend,
                "support": round(support, 2),
                "resistance": round(resistance, 2),
            }
        except Exception as e:
            logger.error(f"技术分析失败: {e}")
            return {"valid": False}

    def _calc_rsi(self, series: pd.Series, period: int = 14) -> float | None:
        if len(series) < period + 1:
            return None
        delta = series.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain.iloc[-1] / loss.iloc[-1] if loss.iloc[-1] != 0 else 100
        return 100 - (100 / (1 + rs))

    def _calc_macd(self, series: pd.Series) -> tuple:
        if len(series) < 26:
            return None, None, None
        ema12 = series.ewm(span=12).mean()
        ema26 = series.ewm(span=26).mean()
        macd_line = ema12 - ema26
        signal = macd_line.ewm(span=9).mean()
        hist = macd_line - signal
        return macd_line.iloc[-1], signal.iloc[-1], hist.iloc[-1]

    def generate_technical_signal(self, analysis: dict) -> dict:
        if not analysis.get("valid"):
            return {"signal": "无数据", "score": 0}

        score = 0
        factors = []

        rsi = analysis.get("rsi")
        if rsi is not None:
            if rsi < 30:
                score += 2
                factors.append(f"RSI={rsi}，超卖区间，可能反弹")
            elif rsi > 70:
                score -= 2
                factors.append(f"RSI={rsi}，超买区间，注意回调")
            elif rsi > 50:
                score += 1
                factors.append(f"RSI={rsi}，多头区间")

        macd = analysis.get("macd_hist")
        if macd is not None:
            if macd > 0:
                score += 1
                factors.append("MACD柱线为正，多头动能")
            else:
                score -= 1
                factors.append("MACD柱线为负，空头动能")

        trend = analysis.get("trend", "")
        if "金叉" in trend:
            score += 2
            factors.append("MA5/MA10金叉，短期看多")
        elif "死叉" in trend:
            score -= 2
            factors.append("MA5/MA10死叉，短期看空")

        vol_ratio = analysis.get("vol_ratio", 1)
        if vol_ratio > 2:
            factors.append(f"量比={vol_ratio}，放量明显")
            if score > 0:
                score += 1

        if score >= 2:
            signal = "看多"
        elif score <= -2:
            signal = "看空"
        else:
            signal = "中性"

        return {"signal": signal, "score": score, "factors": factors}
