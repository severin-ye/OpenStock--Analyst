"""
MCP 分析工具模块

提供完整的股票分析工具。
"""

import json
from typing import Optional

from mcp.server.fastmcp import Context

from ..server import mcp


@mcp.tool()
async def technical_analysis(
    ticker: str,
    period: str = "1y",
    ctx: Optional[Context] = None,
) -> str:
    """执行技术分析。

    Args:
        ticker: 股票代码 (如 "NVDA", "1810.HK")
        period: 分析周期 (如 "1y", "6mo", "3mo")
    """
    if ctx:
        await ctx.info(f"正在对 {ticker} 进行技术分析...")

    try:
        from stock_analysis.analysis import TechnicalAnalyzer
        analyzer = TechnicalAnalyzer()
        signal = analyzer.analyze(ticker, period=period)

        result = {
            "ticker": ticker,
            "analysis_type": "technical",
            "signal": signal.signal,
            "mtf_score": signal.mtf_score,
            "details": {
                "trend": signal.trend,
                "support": signal.support,
                "resistance": signal.resistance,
                "rsi": signal.rsi,
                "macd": signal.macd,
            }
        }

        if ctx:
            await ctx.report_progress(100, 100, "技术分析完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"技术分析失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def insider_analysis(
    ticker: str,
    ctx: Optional[Context] = None,
) -> str:
    """执行内部人交易分析。

    Args:
        ticker: 股票代码
    """
    if ctx:
        await ctx.info(f"正在分析 {ticker} 的内部人交易...")

    try:
        from stock_analysis.analysis import InsiderAnalyzer
        analyzer = InsiderAnalyzer()
        signal = analyzer.analyze(ticker)

        result = {
            "ticker": ticker,
            "analysis_type": "insider",
            "signal": signal.signal,
            "net_sentiment": signal.net_sentiment,
            "details": {
                "buy_count": signal.buy_count,
                "sell_count": signal.sell_count,
                "total_amount": signal.total_amount,
                "significant_trades": signal.significant_trades,
            }
        }

        if ctx:
            await ctx.report_progress(100, 100, "内部人交易分析完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"内部人交易分析失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def institutional_analysis(
    ticker: str,
    ctx: Optional[Context] = None,
) -> str:
    """执行机构持仓分析。

    Args:
        ticker: 股票代码
    """
    if ctx:
        await ctx.info(f"正在分析 {ticker} 的机构持仓...")

    try:
        from stock_analysis.analysis import InstitutionalAnalyzer
        analyzer = InstitutionalAnalyzer()
        signal = analyzer.analyze(ticker)

        result = {
            "ticker": ticker,
            "analysis_type": "institutional",
            "signal": signal.signal,
            "institutional_ownership_pct": signal.institutional_ownership_pct,
            "details": {
                "holder_count": signal.holder_count,
                "top10_concentration": signal.top10_concentration,
                "trend": signal.trend,
                "smart_money_signal": signal.smart_money_signal,
            }
        }

        if ctx:
            await ctx.report_progress(100, 100, "机构持仓分析完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"机构持仓分析失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def earnings_analysis(
    ticker: str,
    ctx: Optional[Context] = None,
) -> str:
    """执行财报分析。

    Args:
        ticker: 股票代码
    """
    if ctx:
        await ctx.info(f"正在分析 {ticker} 的财报...")

    try:
        from stock_analysis.analysis import EarningsAnalyzer
        analyzer = EarningsAnalyzer()
        signal = analyzer.analyze(ticker)

        result = {
            "ticker": ticker,
            "analysis_type": "earnings",
            "signal": signal.signal,
            "management_tone": signal.management_tone.value,
            "details": {
                "guidance_change": signal.guidance_change,
                "key_themes": signal.key_themes,
                "red_flags": signal.red_flags,
            }
        }

        if ctx:
            await ctx.report_progress(100, 100, "财报分析完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"财报分析失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def sector_analysis(
    ticker: str,
    ctx: Optional[Context] = None,
) -> str:
    """执行行业分析。

    Args:
        ticker: 股票代码
    """
    if ctx:
        await ctx.info(f"正在分析 {ticker} 的行业情况...")

    try:
        from stock_analysis.analysis import SectorAnalyzer
        analyzer = SectorAnalyzer()
        signal = analyzer.analyze(ticker)

        result = {
            "ticker": ticker,
            "analysis_type": "sector",
            "signal": signal.signal,
            "sector_score": signal.sector_score,
            "details": {
                "sector": signal.sector,
                "sub_sector": signal.sub_sector,
                "economic_cycle": signal.economic_cycle,
                "sector_pe": signal.sector_pe,
                "ytd_return": signal.ytd_return,
            }
        }

        if ctx:
            await ctx.report_progress(100, 100, "行业分析完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"行业分析失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def economics_analysis(
    ctx: Optional[Context] = None,
) -> str:
    """执行宏观经济分析。"""
    if ctx:
        await ctx.info("正在分析宏观经济情况...")

    try:
        from stock_analysis.analysis import EconomicsAnalyzer
        analyzer = EconomicsAnalyzer()
        signal = analyzer.analyze()

        result = {
            "analysis_type": "economics",
            "signal": signal.signal,
            "phase": signal.phase.value,
            "details": {
                "monetary_policy": signal.monetary_policy,
                "yield_curve": signal.yield_curve,
                "vix": signal.vix,
                "gdp_growth": signal.gdp_growth,
            }
        }

        if ctx:
            await ctx.report_progress(100, 100, "宏观经济分析完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"宏观经济分析失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def competitor_analysis(
    ticker: str,
    ctx: Optional[Context] = None,
) -> str:
    """执行竞争分析。

    Args:
        ticker: 股票代码
    """
    if ctx:
        await ctx.info(f"正在分析 {ticker} 的竞争情况...")

    try:
        from stock_analysis.analysis import CompetitorAnalyzer
        analyzer = CompetitorAnalyzer()
        signal = analyzer.analyze(ticker)

        result = {
            "ticker": ticker,
            "analysis_type": "competitor",
            "signal": signal.signal,
            "moat_width": signal.moat_width.value,
            "details": {
                "moat_trend": signal.moat_trend,
                "industry_rivalry": signal.industry_rivalry,
                "new_entrants": signal.new_entrants,
                "supplier_power": signal.supplier_power,
                "buyer_power": signal.buyer_power,
                "substitutes": signal.substitutes,
                "roic_vs_wacc": signal.roic_vs_wacc,
            }
        }

        if ctx:
            await ctx.report_progress(100, 100, "竞争分析完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"竞争分析失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def narrative_analysis(
    ticker: str,
    ctx: Optional[Context] = None,
) -> str:
    """执行叙事分析。

    Args:
        ticker: 股票代码
    """
    if ctx:
        await ctx.info(f"正在分析 {ticker} 的叙事情况...")

    try:
        from stock_analysis.analysis import NarrativeAnalyzer
        analyzer = NarrativeAnalyzer()
        signal = analyzer.analyze(ticker)

        result = {
            "ticker": ticker,
            "analysis_type": "narrative",
            "signal": signal.signal,
            "narrative_strength": signal.narrative_strength.value,
            "details": {
                "themes": signal.themes,
                "news_sentiment": signal.news_sentiment,
                "social_sentiment": signal.social_sentiment,
            }
        }

        if ctx:
            await ctx.report_progress(100, 100, "叙事分析完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"叙事分析失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)
