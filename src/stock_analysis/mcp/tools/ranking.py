"""
MCP 排名工具模块

提供排名相关的工具。
"""

import json
from typing import Optional

from mcp.server.fastmcp import Context

from ..server import mcp


@mcp.tool()
async def get_rankings(
    market: Optional[str] = None,
    limit: int = 10,
    ctx: Optional[Context] = None,
) -> str:
    """获取公司列表。

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
            "note": "排名数据需要使用 full_analysis 生成完整报告后获取"
        }

        if ctx:
            await ctx.report_progress(100, 100, "公司列表获取完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"公司列表获取失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)
