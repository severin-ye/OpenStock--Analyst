"""
MCP 数据工具模块

提供数据获取和刷新工具。
"""

import json

from mcp.server.fastmcp import Context

# 获取服务器实例
from ..server import mcp


@mcp.tool()
async def refresh_data(
    ticker: str = None,
    ctx: Context = None,
) -> str:
    """刷新价格数据。

    Args:
        ticker: 股票代码 (可选，不提供则刷新所有)
    """
    if ctx:
        if ticker:
            await ctx.info(f"正在刷新 {ticker} 的价格数据...")
        else:
            await ctx.info("正在刷新所有价格数据...")

    try:
        from stock_analysis.data.fetcher import fetch_all_8, fetch_yfinance
        from stock_analysis.registry import get_by_name_zh, registry

        if ticker:
            # 刷新单个公司
            # 先尝试中文名查找
            company = get_by_name_zh(ticker)
            if not company:
                # 尝试ticker查找
                reg = registry()
                company = reg.get(ticker)

            if not company:
                return json.dumps({"error": f"未找到公司: {ticker}"}, ensure_ascii=False)

            company_ticker = company.get("ticker", ticker)
            snapshot = fetch_yfinance(company_ticker)

            refresh_result = {
                "ticker": company_ticker,
                "company_name": company.get("name_zh", ticker),
                "refresh_status": "success" if snapshot else "failed",
                "details": {
                    "price": snapshot.price if snapshot else None,
                    "market_cap": snapshot.market_cap if snapshot else None,
                } if snapshot else None,
            }
        else:
            # 刷新所有公司
            fetch_all_8()
            refresh_result = {
                "refresh_type": "all",
                "status": "success",
                "message": "已触发全量数据刷新",
            }

        if ctx:
            await ctx.report_progress(100, 100, "数据刷新完成")

        return json.dumps(refresh_result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"数据刷新失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def get_price_data(
    ticker: str,
    period: str = "1y",
    ctx: Context = None,
) -> str:
    """获取价格数据。

    Args:
        ticker: 股票代码
        period: 数据周期 (如 "1y", "6mo", "3mo", "1mo")
    """
    if ctx:
        await ctx.info(f"正在获取 {ticker} 的价格数据...")

    try:
        from stock_analysis.data.fetcher import fetch_yfinance
        from stock_analysis.registry import get_by_name_zh, registry

        # 先尝试中文名查找
        company = get_by_name_zh(ticker)
        if not company:
            # 尝试ticker查找
            reg = registry()
            company = reg.get(ticker)

        if not company:
            return json.dumps({"error": f"未找到公司: {ticker}"}, ensure_ascii=False)

        company_ticker = company.get("ticker", ticker)

        # 获取价格数据
        snapshot = fetch_yfinance(company_ticker)

        if not snapshot:
            return json.dumps({"error": f"无法获取 {ticker} 的价格数据"}, ensure_ascii=False)

        result = {
            "ticker": company_ticker,
            "company_name": company.get("name_zh", ticker),
            "price": snapshot.price,
            "currency": snapshot.currency,
            "market_cap": snapshot.market_cap,
            "ytd_change_pct": snapshot.ytd_change_pct,
            "pe_ratio": snapshot.pe_ratio,
            "forward_pe": snapshot.forward_pe,
            "peg_ratio": snapshot.peg_ratio,
            "week52_low": snapshot.week52_low,
            "week52_high": snapshot.week52_high,
        }

        if ctx:
            await ctx.report_progress(100, 100, "价格数据获取完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"价格数据获取失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def get_financial_data(
    ticker: str,
    ctx: Context = None,
) -> str:
    """获取财务数据。

    Args:
        ticker: 股票代码
    """
    if ctx:
        await ctx.info(f"正在获取 {ticker} 的财务数据...")

    try:
        from stock_analysis.data.fetcher import fetch_yfinance
        from stock_analysis.registry import get_by_name_zh, registry

        # 先尝试中文名查找
        company = get_by_name_zh(ticker)
        if not company:
            # 尝试ticker查找
            reg = registry()
            company = reg.get(ticker)

        if not company:
            return json.dumps({"error": f"未找到公司: {ticker}"}, ensure_ascii=False)

        company_ticker = company.get("ticker", ticker)

        # 获取财务数据
        snapshot = fetch_yfinance(company_ticker)

        if not snapshot:
            return json.dumps({"error": f"无法获取 {ticker} 的财务数据"}, ensure_ascii=False)

        result = {
            "ticker": company_ticker,
            "company_name": company.get("name_zh", ticker),
            "financial_data": {
                "revenue": snapshot.revenue,
                "ebit": snapshot.ebit,
                "net_income": snapshot.net_income,
                "ebit_ev": snapshot.ebit_ev,
                "roic": snapshot.roic,
                "f_score": snapshot.f_score,
                "fcf_yield": snapshot.fcf_yield,
                "revenue_growth": snapshot.revenue_growth,
                "beta": snapshot.beta,
            }
        }

        if ctx:
            await ctx.report_progress(100, 100, "财务数据获取完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"财务数据获取失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def get_market_data(
    market: str,
    ctx: Context = None,
) -> str:
    """获取市场数据。

    Args:
        market: 市场代码 (如 "US", "HK", "JP", "KR", "CN", "Crypto")
    """
    if ctx:
        await ctx.info(f"正在获取 {market} 市场的数据...")

    try:
        from stock_analysis.registry import MARKET_GROUPS, registry

        # 获取所有公司
        reg = registry()
        companies = list(reg.values())

        # 按市场筛选
        market_upper = market.upper()
        if market_upper in MARKET_GROUPS:
            tickers = MARKET_GROUPS[market_upper]
            market_companies = [c for c in companies if c.get("ticker") in tickers]
        else:
            market_companies = [c for c in companies if c.get("market", "").upper() == market_upper]

        result = {
            "market": market,
            "company_count": len(market_companies),
            "companies": [{
                "ticker": c.get("ticker"),
                "name_zh": c.get("name_zh"),
                "name_en": c.get("name_en"),
                "exchange": c.get("exchange"),
                "sector": c.get("sector"),
            } for c in market_companies],
        }

        if ctx:
            await ctx.report_progress(100, 100, "市场数据获取完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"市场数据获取失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)
