import logging
from datetime import datetime, date, timedelta

import pandas as pd

logger = logging.getLogger(__name__)


class StockCollector:
    """采集中国A股数据"""

    def get_market_overview(self) -> dict:
        """获取大盘概况"""
        result = {"indices": [], "hot_sectors": [], "top_gainers": [], "top_losers": []}
        try:
            import akshare as ak
            idx_df = ak.stock_zh_index_spot_em()
            if idx_df is not None and not idx_df.empty:
                key_indices = ["上证指数", "深证成指", "创业板指", "科创50", "沪深300"]
                for _, row in idx_df.iterrows():
                    name = str(row.get("名称", ""))
                    if name in key_indices:
                        result["indices"].append({
                            "name": name,
                            "code": str(row.get("代码", "")),
                            "price": float(row.get("最新价", 0)),
                            "change_pct": float(row.get("涨跌幅", 0)),
                            "volume": float(row.get("成交量", 0)),
                        })
                logger.info(f"获取到 {len(result['indices'])} 个主要指数")
        except Exception as e:
            logger.warning(f"获取大盘数据失败: {e}")

        try:
            import akshare as ak
            sector_df = ak.stock_board_concept_name_em()
            if sector_df is not None and not sector_df.empty:
                sector_df = sector_df.sort_values("涨跌幅", ascending=False)
                for _, row in sector_df.head(10).iterrows():
                    result["hot_sectors"].append({
                        "name": str(row.get("板块名称", "")),
                        "change_pct": float(row.get("涨跌幅", 0)),
                        "turnover": float(row.get("总成交额", 0)),
                    })
        except Exception as e:
            logger.warning(f"获取板块数据失败: {e}")

        return result

    def get_sector_stocks(self, sector_name: str, limit: int = 10) -> list[dict]:
        """获取板块个股"""
        stocks = []
        try:
            import akshare as ak
            df = ak.stock_board_concept_cons_em(symbol=sector_name)
            if df is not None and not df.empty:
                df = df.sort_values("涨跌幅", ascending=False)
                for _, row in df.head(limit).iterrows():
                    stocks.append({
                        "code": str(row.get("代码", "")),
                        "name": str(row.get("名称", "")),
                        "price": float(row.get("最新价", 0)),
                        "change_pct": float(row.get("涨跌幅", 0)),
                        "volume": float(row.get("成交量", 0)),
                        "turnover": float(row.get("成交额", 0)),
                        "sector": sector_name,
                    })
        except Exception as e:
            logger.warning(f"获取板块 {sector_name} 个股失败: {e}")
        return stocks

    def get_stock_history(self, code: str, days: int = 30) -> pd.DataFrame:
        """获取个股历史数据"""
        try:
            import akshare as ak
            end_date = date.today().strftime("%Y%m%d")
            start_date = (date.today() - timedelta(days=days)).strftime("%Y%m%d")
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )
            return df
        except Exception as e:
            logger.warning(f"获取股票 {code} 历史数据失败: {e}")
            return pd.DataFrame()

    def get_realtime_quotes(self) -> list[dict]:
        """获取A股实时行情快照"""
        stocks = []
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                df = df.sort_values("涨跌幅", ascending=False)
                top_up = df.head(20)
                top_down = df.tail(20)
                for _, row in pd.concat([top_up, top_down]).iterrows():
                    stocks.append({
                        "code": str(row.get("代码", "")),
                        "name": str(row.get("名称", "")),
                        "price": float(row.get("最新价", 0) or 0),
                        "change_pct": float(row.get("涨跌幅", 0) or 0),
                        "volume": float(row.get("成交量", 0) or 0),
                        "turnover": float(row.get("成交额", 0) or 0),
                    })
        except Exception as e:
            logger.warning(f"获取实时行情失败: {e}")
        return stocks
