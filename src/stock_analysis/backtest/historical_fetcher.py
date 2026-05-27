"""从 yfinance 构建历史财报快照（严格避免前瞻偏差）

对每个截止日期 D:
  1. 价格: D 的最近交易日收盘价
  2. 财报: 只取 fiscal_date ≤ D - 90d 的期次
  3. F-Score: 需 ≥2 期前值算 Δ
  4. PEG: PE / (收入增速×100)
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

from stock_analysis.data.fetcher import PriceSnapshot

logger = logging.getLogger(__name__)

YF_CURRENCY = {"USD": "$", "HKD": "HK$", "JPY": "¥", "KRW": "₩", "CNY": "¥"}


def _safe(v):
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _g(row, key):
    """取 DataFrame 行中的 key，安全返回 float"""
    if row is None:
        return None
    if key in row.index:
        return _safe(row[key])
    return None


def _fmt(val, cur_sym):
    if val is None:
        return ""
    if abs(val) >= 1e12:
        return f"{cur_sym}{val / 1e12:.2f}T"
    if abs(val) >= 1e9:
        return f"{cur_sym}{val / 1e9:.2f}B"
    return f"{cur_sym}{val:,.0f}"


def get_price_at_date(ticker: str, cutoff_str: str) -> Optional[float]:
    """获取截止日的最近交易日收盘价（避免前瞻偏差）"""
    cutoff = pd.Timestamp(cutoff_str)
    start = cutoff - pd.Timedelta(days=30)
    hist = yf.download(ticker, start=start.strftime("%Y-%m-%d"), end=cutoff_str, progress=False, auto_adjust=True)
    if hist is None or hist.empty:
        return None
    mask = hist.index <= cutoff
    if not mask.any():
        return None
    try:
        close_df = hist.loc[mask, "Close"]
        if isinstance(close_df, pd.DataFrame):
            close_val = float(close_df.iloc[-1, 0])
        else:
            close_val = float(close_df.iloc[-1])
        return round(close_val, 2)
    except (KeyError, ValueError, TypeError, IndexError) as e:
        logger.warning(f"  get_price failed {ticker} @{cutoff_str}: {e}")
        return None


def _latest_shares(ticker: str, cutoff_dt: pd.Timestamp) -> Optional[float]:
    """从截止日之前最新的 balance sheet 取流通股数"""
    t = yf.Ticker(ticker)
    bs = t.balance_sheet
    if bs is None or bs.empty:
        return None
    avail = bs.loc[:, bs.columns <= cutoff_dt]
    if avail.empty:
        return None
    cur = avail.iloc[:, 0]
    return _g(cur, "Ordinary Shares Number")


def build_snapshot_at_date(ticker: str, cutoff_str: str, price: float, currency: str = "$") -> Optional[PriceSnapshot]:
    """构建截止某日的 PriceSnapshot（仅用当日之前已公开的财报）"""
    cutoff_dt = pd.Timestamp(cutoff_str)
    avail_dt = cutoff_dt - pd.Timedelta(days=90)

    t = yf.Ticker(ticker)

    cur_sym = YF_CURRENCY.get(currency, "$")

    # ── 价格 + 股数 → 市值 ──
    shares = _latest_shares(ticker, avail_dt)
    mkt_cap_val = price * shares if shares else 0.0
    cap_str = _fmt(mkt_cap_val, cur_sym) if mkt_cap_val else ""

    # ── 财报 DataFrame（统一使用年度数据，确保 BS/FS/CF 列对齐）──
    bs = t.balance_sheet if t.balance_sheet is not None and not t.balance_sheet.empty else None
    fs = t.financials if t.financials is not None and not t.financials.empty else None
    cf = t.cashflow if t.cashflow is not None and not t.cashflow.empty else None

    if bs is None or fs is None or bs.empty or fs.empty:
        return None

    avail_bs = bs.loc[:, bs.columns <= avail_dt]
    avail_fs = fs.loc[:, fs.columns <= avail_dt]
    avail_cf = cf.loc[:, cf.columns <= avail_dt] if cf is not None else None

    if avail_bs.empty or avail_fs.empty:
        return None

    cur_bs = avail_bs.iloc[:, 0]
    prev_bs = avail_bs.iloc[:, 1] if avail_bs.shape[1] > 1 else None
    cur_fs = avail_fs.iloc[:, 0]
    prev_fs = avail_fs.iloc[:, 1] if avail_fs.shape[1] > 1 else None
    cur_cf = avail_cf.iloc[:, 0] if avail_cf is not None and not avail_cf.empty else None

    # ════════════════ 财报数据提取 ════════════════
    total_assets = _g(cur_bs, "Total Assets")
    total_debt = _g(cur_bs, "Total Debt")
    equity = _g(cur_bs, "Total Equity Gross Minority Interest") or _g(cur_bs, "Stockholders Equity") or 0
    cash = _g(cur_bs, "Cash And Cash Equivalents") or _g(cur_bs, "Cash Cash Equivalents And Short Term Investments") or 0
    ca = _g(cur_bs, "Current Assets")
    cl = _g(cur_bs, "Current Liabilities")
    ltd = _g(cur_bs, "Long Term Debt")

    ebit = _g(cur_fs, "EBIT")
    ni = _g(cur_fs, "Net Income")
    rev = _g(cur_fs, "Total Revenue") or _g(cur_fs, "Operating Revenue")
    gp = _g(cur_fs, "Gross Profit")
    pretax = _g(cur_fs, "Pretax Income")
    tax = _g(cur_fs, "Tax Provision")

    opcf = _g(cur_cf, "Operating Cash Flow") if cur_cf is not None else None
    fcf = _g(cur_cf, "Free Cash Flow") if cur_cf is not None else None

    prev_total_assets = _g(prev_bs, "Total Assets")
    prev_ltd = _g(prev_bs, "Long Term Debt")
    prev_ca = _g(prev_bs, "Current Assets")
    prev_cl = _g(prev_bs, "Current Liabilities")
    prev_shares = _g(prev_bs, "Ordinary Shares Number")
    prev_ni = _g(prev_fs, "Net Income")
    prev_rev = _g(prev_fs, "Total Revenue") or _g(prev_fs, "Operating Revenue")
    prev_gp = _g(prev_fs, "Gross Profit")

    # ════════════════ EV ════════════════
    ev = mkt_cap_val + (total_debt or 0) - (cash or 0)

    # ════════════════ EBIT/EV ════════════════
    ebit_ev = None
    if ebit and ev and ev > 0:
        ebit_ev = ebit / ev
        ebit_ev_pct = f"{ebit_ev * 100:.2f}%"
    else:
        ebit_ev_pct = ""

    # ════════════════ ROIC ════════════════
    roic = None
    roic_pct = ""
    if ebit and equity and total_debt is not None:
        rate = tax / pretax if pretax and pretax != 0 else 0.25
        rate = max(0.0, min(float(rate), 0.5))
        ic = equity + total_debt - cash
        if ic and ic > 0:
            roic = ebit * (1 - rate) / ic
            roic_pct = f"{roic * 100:.2f}%"

    # ════════════════ FCF Yield ════════════════
    fcf_yield_pct = ""
    if fcf and mkt_cap_val > 0:
        fcf_yield_pct = f"{fcf / mkt_cap_val * 100:.2f}%"

    # ════════════════ Revenue Growth ════════════════
    rev_growth = None
    rev_growth_pct = ""
    if rev and prev_rev and prev_rev > 0:
        rev_growth = rev / prev_rev - 1
        rev_growth_pct = f"{rev_growth * 100:+.1f}%"

    # ════════════════ F-Score 9 项 ════════════════
    fs_total = 0
    roa = ni / total_assets if ni and total_assets else -1
    fs_total += 1 if roa > 0 else 0
    fs_total += 1 if opcf and opcf > 0 else 0
    prev_roa = prev_ni / prev_total_assets if prev_ni and prev_total_assets else -1
    fs_total += 1 if roa > prev_roa else 0
    fs_total += 1 if opcf and ni and opcf > ni else 0
    fs_total += 1 if ltd is not None and prev_ltd is not None and ltd < prev_ltd else 0
    cr_cur = ca / cl if ca and cl else -1
    cr_prev = prev_ca / prev_cl if prev_ca and prev_cl else -1
    fs_total += 1 if cr_cur > cr_prev else 0
    fs_total += 1 if shares and prev_shares and shares <= prev_shares * 1.02 else 0
    gm_cur = gp / rev if gp and rev else -1
    gm_prev = prev_gp / prev_rev if prev_gp and prev_rev else -1
    fs_total += 1 if gm_cur > gm_prev else 0
    at_cur = rev / total_assets if rev and total_assets else -1
    at_prev = prev_rev / prev_total_assets if prev_rev and prev_total_assets else -1
    fs_total += 1 if at_cur > at_prev else 0

    # ════════════════ PEG ════════════════
    eps = ni / shares if ni and shares else None
    pe = price / eps if eps and eps != 0 else None
    peg_val = None
    peg_str = ""
    if pe and rev_growth and rev_growth > 0:
        peg_val = pe / (rev_growth * 100)
        peg_str = f"{peg_val:.2f}"
    elif pe and rev_growth and rev_growth != 0:
        peg_val = pe / (abs(rev_growth) * 100)
        peg_str = f"{peg_val:.2f}"

    # ════════════════ 结果构建 ════════════════
    snap = PriceSnapshot(
        ticker=ticker,
        price=price,
        currency=cur_sym,
        market_cap=cap_str,
        enterprise_value=_fmt(ev, cur_sym) if ev else "",
        ebit_ev=ebit_ev_pct,
        roic=roic_pct,
        f_score=fs_total,
        fcf_yield=fcf_yield_pct,
        revenue_growth=rev_growth_pct,
        revenue=_fmt(rev, cur_sym) if rev else "",
        ebit=_fmt(ebit, cur_sym) if ebit else "",
        net_income=_fmt(ni, cur_sym) if ni else "",
        peg_ratio=peg_str,
        pe_ratio=f"{pe:.2f}" if pe else "",
        source="yfinance_backtest",
    )

    logger.info(
        f"  {ticker:10s} @{cutoff_str}: "
        f"PE={pe or 'N/A'} EBIT/EV={ebit_ev_pct or 'N/A'} ROIC={roic_pct or 'N/A'} "
        f"F={fs_total}/9 RevG={rev_growth_pct or 'N/A'} PEG={peg_str or 'N/A'} "
        f"#FY={avail_bs.shape[1]}"
    )

    return snap


def build_all_snapshots(tickers: list[str], cutoff_str: str, prices: dict[str, float]) -> dict[str, PriceSnapshot]:
    """为所有 ticker 构建截止某日的快照"""
    results = {}
    for ticker in tickers:
        price = prices.get(ticker, 0.0)
        if not price:
            continue
        cur_sym = "USD"
        if ticker == "1810.HK":
            cur_sym = "HKD"
        snap = build_snapshot_at_date(ticker, cutoff_str, price, currency=cur_sym)
        if snap is not None:
            results[ticker] = snap
    return results
