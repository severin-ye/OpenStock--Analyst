"""
MCP 报告工具模块

提供报告生成工具。
"""

import json
import os
from typing import Optional

from mcp.server.fastmcp import Context

from ..server import mcp


@mcp.tool()
async def generate_report(
    ticker: str,
    ctx: Optional[Context] = None,
) -> str:
    """生成股票分析报告。

    调用完整的分析pipeline生成HTML报告。

    Args:
        ticker: 股票代码或中文名
    """
    if ctx:
        await ctx.info(f"正在生成 {ticker} 的分析报告...")

    try:
        from stock_analysis.cli import run_analysis
        from stock_analysis.registry import get_by_name_zh, registry

        # 查找公司
        company = get_by_name_zh(ticker)
        if not company:
            reg = registry()
            company = reg.get(ticker)

        company_name = company.get("name_zh", ticker) if company else ticker

        # 执行完整分析
        result = run_analysis(company_name, dry_run=False)

        if result:
            output_dir = os.path.join(os.getcwd(), "output", company_name)
            report_files = []
            if os.path.exists(output_dir):
                for f in os.listdir(output_dir):
                    if f.endswith(".html"):
                        report_files.append(os.path.join(output_dir, f))

            response = {
                "ticker": ticker,
                "company_name": company_name,
                "status": "success",
                "output_dir": output_dir,
                "report_files": report_files,
            }
        else:
            response = {
                "ticker": ticker,
                "company_name": company_name,
                "status": "failed",
                "message": "报告生成失败，请检查日志",
            }

        if ctx:
            await ctx.report_progress(100, 100, "报告生成完成")

        return json.dumps(response, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"报告生成失败: {str(e)}"
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
