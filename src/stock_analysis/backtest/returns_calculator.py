"""实际持有期回报计算"""

import logging
from typing import Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def _get_price(ticker: str, target: pd.Timestamp) -> Optional[float]:
    """获取目标日期最近交易日的收盘价"""
    start = target - pd.Timedelta(days=30)
    end = target + pd.Timedelta(days=5)
    hist = yf.download(ticker, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False, auto_adjust=True)
    if hist is None or hist.empty:
        return None
    try:
        close_df = hist["Close"]
        mask = hist.index <= target
        if mask.any():
            close_df = close_df.loc[mask]
        if isinstance(close_df, pd.DataFrame):
            return float(close_df.iloc[-1, 0])
        else:
            return float(close_df.iloc[-1])
    except (KeyError, ValueError, TypeError, IndexError):
        return None


def get_returns(ticker: str, entry_date_str: str, hold_6m: int = 182, hold_1y: int = 365) -> dict:
    """计算从 entry_date 开始的持有期回报"""
    entry = pd.Timestamp(entry_date_str)
    entry_price = _get_price(ticker, entry)
    if entry_price is None:
        return {"entry_price": None, "ret_6m": None, "ret_1y": None}

    date_6m = entry + pd.Timedelta(days=hold_6m)
    price_6m = _get_price(ticker, date_6m)
    ret_6m = round((price_6m / entry_price - 1) * 100, 2) if price_6m else None

    date_1y = entry + pd.Timedelta(days=hold_1y)
    price_1y = _get_price(ticker, date_1y)
    ret_1y = round((price_1y / entry_price - 1) * 100, 2) if price_1y else None

    logger.info(f"  {ticker:10s} entry={entry_price} → 6m={ret_6m}% 1y={ret_1y}%")

    return {
        "entry_price": entry_price,
        "ret_6m": ret_6m,
        "ret_1y": ret_1y,
    }


def compute_all_returns(tickers: list[str], cutoff_str: str) -> dict[str, dict]:
    """计算所有目标公司在截止日的 entry price + 6m/1y 回报"""
    results = {}
    for ticker in tickers:
        results[ticker] = get_returns(ticker, cutoff_str)
    return results
