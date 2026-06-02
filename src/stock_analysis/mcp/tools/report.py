"""
MCP 报告工具模块

提供报告生成工具。
"""

import json
import os
from typing import Optional

from mcp.server.fastmcp import Context

# 获取服务器实例
from ..server import mcp


@mcp.tool()
async def generate_report(
    ticker: str,
    report_type: str = "html",
    output_dir: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> str:
    """生成股票分析报告。

    Args:
        ticker: 股票代码
        report_type: 报告类型 (html/markdown)
        output_dir: 输出目录 (可选)
    """
    if ctx:
        await ctx.info(f"正在生成 {ticker} 的分析报告...")

    try:
        from stock_analysis.cli import run_analysis
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
        company_name = company.get("name_zh", ticker)

        # 使用CLI的分析功能
        try:
            run_analysis(company_name, dry_run=False)

            # 确定输出路径
            if not output_dir:
                output_dir = os.path.join(os.getcwd(), "分析输出", company_name)

            # 查找生成的报告
            report_files = []
            if os.path.exists(output_dir):
                for f in os.listdir(output_dir):
                    if f.endswith(".html"):
                        report_files.append(os.path.join(output_dir, f))

            result = {
                "ticker": company_ticker,
                "company_name": company_name,
                "report_type": report_type,
                "status": "success",
                "output_dir": output_dir,
                "report_files": report_files,
            }
        except Exception as e:
            result = {
                "ticker": company_ticker,
                "company_name": company_name,
                "report_type": report_type,
                "status": "error",
                "error": str(e),
            }

        if ctx:
            await ctx.report_progress(100, 100, "报告生成完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"报告生成失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def list_reports(
    ticker: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> str:
    """列出分析报告。

    Args:
        ticker: 股票代码 (可选)
    """
    if ctx:
        await ctx.info("正在列出分析报告...")

    try:
        # 分析输出目录
        output_dir = os.path.join(os.getcwd(), "分析输出")

        if not os.path.exists(output_dir):
            return json.dumps({"reports": [], "message": "分析输出目录不存在"}, ensure_ascii=False)

        reports = []

        # 遍历目录
        for company_dir in os.listdir(output_dir):
            company_path = os.path.join(output_dir, company_dir)

            if not os.path.isdir(company_path):
                continue

            # 如果指定了 ticker，只列出该公司的报告
            if ticker and ticker.upper() not in company_dir.upper():
                continue

            # 列出该公司的所有报告
            for filename in os.listdir(company_path):
                filepath = os.path.join(company_path, filename)

                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    reports.append({
                        "company": company_dir,
                        "filename": filename,
                        "filepath": filepath,
                        "file_size": stat.st_size,
                        "modified_time": stat.st_mtime,
                    })

        # 按修改时间排序
        reports.sort(key=lambda x: x["modified_time"], reverse=True)

        result = {
            "ticker": ticker,
            "report_count": len(reports),
            "reports": reports,
        }

        if ctx:
            await ctx.report_progress(100, 100, "报告列表获取完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"报告列表获取失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)
