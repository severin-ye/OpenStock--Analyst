"""
MCP 排名工具模块

提供股票排名计算工具。
"""

import json
from typing import Optional

from mcp.server.fastmcp import Context

# 获取服务器实例
from ..server import mcp


@mcp.tool()
async def calculate_ranking(
    ticker: str,
    ctx: Optional[Context] = None,
) -> str:
    """计算单个公司的指标数据。

    注意：完整排名需要整个市场的数据，此工具只返回单个公司的指标。

    Args:
        ticker: 股票代码 (如 "NVDA", "1810.HK")
    """
    if ctx:
        await ctx.info(f"正在获取 {ticker} 的指标数据...")

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

        # 获取公司ticker
        company_ticker = company.get("ticker", ticker)

        # 获取价格数据
        snapshots = fetch_yfinance([company_ticker])
        snapshot = snapshots.get(company_ticker)

        if not snapshot:
            return json.dumps({"error": f"无法获取 {ticker} 的价格数据"}, ensure_ascii=False)

        result = {
            "ticker": company_ticker,
            "company_name": company.get("name_zh", ticker),
            "market": company.get("market", "Unknown"),
            "metrics": {
                "ebit_ev": snapshot.ebit_ev,
                "roic": snapshot.roic,
                "f_score": snapshot.f_score,
                "peg": snapshot.peg_ratio,
                "revenue_growth": snapshot.revenue_growth,
                "fcf_yield": snapshot.fcf_yield,
            },
            "note": "完整排名需要使用 run_analysis 命令生成完整报告"
        }

        if ctx:
            await ctx.report_progress(100, 100, "指标数据获取完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"指标数据获取失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def get_rankings(
    market: Optional[str] = None,
    limit: int = 10,
    ctx: Optional[Context] = None,
) -> str:
    """获取公司列表（不含排名，排名需要完整分析）。

    Args:
        market: 市场筛选 (如 "US", "HK", "JP", "KR", "CN", "Crypto")
        limit: 返回数量限制
    """
    if ctx:
        await ctx.info("正在获取公司列表...")

    try:
        from stock_analysis.registry import MARKET_GROUPS, registry

        # 获取所有公司
        reg = registry()
        companies = list(reg.values())

        # 按市场筛选
        if market:
            market_upper = market.upper()
            if market_upper in MARKET_GROUPS:
                tickers = MARKET_GROUPS[market_upper]
                companies = [c for c in companies if c.get("ticker") in tickers]
            else:
                companies = [c for c in companies if c.get("market", "").upper() == market_upper]

        # 构建公司列表
        company_list = []
        for company in companies[:limit]:
            company_list.append({
                "ticker": company.get("ticker"),
                "company_name": company.get("name_zh", company.get("ticker")),
                "market": company.get("market", "Unknown"),
                "name_en": company.get("name_en"),
                "exchange": company.get("exchange"),
                "sector": company.get("sector"),
            })

        result = {
            "market": market or "All",
            "total_count": len(company_list),
            "companies": company_list,
            "note": "排名数据需要使用 run_analysis 命令生成完整报告后获取"
        }

        if ctx:
            await ctx.report_progress(100, 100, "公司列表获取完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"公司列表获取失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def compare_rankings(
    tickers: list[str],
    ctx: Optional[Context] = None,
) -> str:
    """比较多個公司的指标数据。

    Args:
        tickers: 股票代码列表 (如 ["NVDA", "AAPL", "TSLA"])
    """
    if ctx:
        await ctx.info(f"正在比较 {len(tickers)} 家公司的指标...")

    try:
        from stock_analysis.data.fetcher import fetch_yfinance
        from stock_analysis.registry import get_by_name_zh, registry

        results = {
            "comparison_count": len(tickers),
            "companies": []
        }

        for ticker in tickers:
            try:
                # 先尝试中文名查找
                company = get_by_name_zh(ticker)
                if not company:
                    # 尝试ticker查找
                    reg = registry()
                    company = reg.get(ticker)

                if not company:
                    results["companies"].append({
                        "ticker": ticker,
                        "error": f"未找到公司: {ticker}"
                    })
                    continue

                # 获取公司ticker
                company_ticker = company.get("ticker", ticker)

                # 获取价格数据
                snapshots = fetch_yfinance([company_ticker])
                snapshot = snapshots.get(company_ticker)

                if not snapshot:
                    results["companies"].append({
                        "ticker": ticker,
                        "error": "无法获取价格数据"
                    })
                    continue

                results["companies"].append({
                    "ticker": company_ticker,
                    "company_name": company.get("name_zh", ticker),
                    "market": company.get("market", "Unknown"),
                    "ebit_ev": snapshot.ebit_ev,
                    "roic": snapshot.roic,
                    "f_score": snapshot.f_score,
                    "peg": snapshot.peg_ratio,
                    "revenue_growth": snapshot.revenue_growth,
                    "fcf_yield": snapshot.fcf_yield,
                })
            except Exception as e:
                results["companies"].append({
                    "ticker": ticker,
                    "error": str(e)
                })

        # 简单按 EBIT/EV 排序（近似排名）
        valid_companies = [c for c in results["companies"] if "error" not in c]
        try:
            valid_companies.sort(
                key=lambda x: float(x.get("ebit_ev", "0").rstrip("%")) if x.get("ebit_ev") else 0,
                reverse=True
            )
        except (ValueError, AttributeError):
            pass

        for i, company in enumerate(valid_companies):
            company["ebit_ev_rank"] = i + 1

        if ctx:
            await ctx.report_progress(100, 100, "公司比较完成")

        return json.dumps(results, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"公司比较失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)
