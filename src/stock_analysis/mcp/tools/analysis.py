"""
MCP 分析工具模块

提供各种股票分析工具，包括技术分析、内部人交易分析等。
"""

import json
from typing import Optional

from mcp.server.fastmcp import Context

# 获取服务器实例
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


@mcp.tool()
async def validate_analysis(
    ticker: str,
    signal: str,
    confidence: str,
    f_score: int,
    composite_rank: str,
    ctx: Optional[Context] = None,
) -> str:
    """验证分析结果。

    Args:
        ticker: 股票代码
        signal: 信号 (BULLISH/NEUTRAL/BEARISH)
        confidence: 置信度 (VERY HIGH/HIGH/MEDIUM/LOW/VERY LOW)
        f_score: F-Score (0-9)
        composite_rank: 综合排名 (如 "#2/9")
    """
    if ctx:
        await ctx.info(f"正在验证 {ticker} 的分析结果...")

    try:
        from stock_analysis.analysis import ResultValidator
        validator = ResultValidator()
        result = validator.validate_analysis(
            ticker=ticker,
            signal=signal,
            confidence=confidence,
            f_score=f_score,
            composite_rank=composite_rank,
        )

        validation_result = {
            "ticker": ticker,
            "validation_type": "analysis_validation",
            "total_score": result.total_score,
            "tier": result.tier.value,
            "details": {
                "data_quality": result.data_quality,
                "methodology": result.methodology,
                "signal_consistency": result.signal_consistency,
                "risk_coverage": result.risk_coverage,
                "reasoning_transparency": result.reasoning_transparency,
            }
        }

        if ctx:
            await ctx.report_progress(100, 100, "分析验证完成")

        return json.dumps(validation_result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"分析验证失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def full_analysis(
    ticker: str,
    analysis_type: str = "full",
    ctx: Optional[Context] = None,
) -> str:
    """执行完整的股票分析。

    Args:
        ticker: 股票代码
        analysis_type: 分析类型 (full/quick/basic)
    """
    if ctx:
        await ctx.info(f"正在对 {ticker} 进行完整分析...")

    try:
        from stock_analysis.analysis import (
            CompetitorAnalyzer,
            EarningsAnalyzer,
            EconomicsAnalyzer,
            InsiderAnalyzer,
            InstitutionalAnalyzer,
            NarrativeAnalyzer,
            SectorAnalyzer,
            TechnicalAnalyzer,
        )

        analyzers = {
            "technical": TechnicalAnalyzer(),
            "insider": InsiderAnalyzer(),
            "institutional": InstitutionalAnalyzer(),
            "earnings": EarningsAnalyzer(),
            "sector": SectorAnalyzer(),
            "economics": EconomicsAnalyzer(),
            "competitor": CompetitorAnalyzer(),
            "narrative": NarrativeAnalyzer(),
        }

        results = {
            "ticker": ticker,
            "analysis_type": analysis_type,
            "analyses": {}
        }

        # 执行所有分析
        total = len(analyzers)

        for i, (name, analyzer) in enumerate(analyzers.items()):
            if ctx:
                await ctx.report_progress(i + 1, total, f"正在执行 {name} 分析...")

            try:
                if name == "economics":
                    signal = analyzer.analyze()
                else:
                    signal = analyzer.analyze(ticker)

                results["analyses"][name] = {
                    "signal": signal.signal,
                    "details": str(signal),
                }
            except Exception as e:
                results["analyses"][name] = {
                    "error": str(e),
                }

        if ctx:
            await ctx.report_progress(100, 100, "完整分析完成")

        return json.dumps(results, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"完整分析失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)
