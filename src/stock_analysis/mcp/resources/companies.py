"""
MCP 公司资源模块

提供公司数据资源。
"""

import json

# 获取服务器实例
from ..server import mcp


@mcp.resource("companies://list")
def get_companies_list() -> str:
    """获取所有公司列表。"""
    try:
        from stock_analysis.registry import registry
        companies = list(registry().values())
        return json.dumps(companies, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"获取公司列表失败: {str(e)}"}, ensure_ascii=False)


@mcp.resource("companies://{ticker}")
def get_company_info(ticker: str) -> str:
    """获取特定公司信息。

    Args:
        ticker: 股票代码
    """
    try:
        from stock_analysis.registry import get_by_name_zh, registry
        # 先尝试中文名查找
        company = get_by_name_zh(ticker)
        if not company:
            # 尝试ticker查找
            reg = registry()
            company = reg.get(ticker)

        if not company:
            return json.dumps({"error": f"未找到公司: {ticker}"}, ensure_ascii=False)

        return json.dumps(company, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"获取公司信息失败: {str(e)}"}, ensure_ascii=False)


@mcp.resource("companies://market/{market}")
def get_companies_by_market(market: str) -> str:
    """获取特定市场的公司列表。

    Args:
        market: 市场代码 (如 "US", "HK", "JP", "KR", "CN", "Crypto")
    """
    try:
        from stock_analysis.registry import registry
        companies = list(registry().values())

        # 按市场筛选
        market_companies = [c for c in companies if c.get("market", "").upper() == market.upper()]

        result = {
            "market": market,
            "company_count": len(market_companies),
            "companies": market_companies,
        }

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"获取市场公司列表失败: {str(e)}"}, ensure_ascii=False)


@mcp.resource("companies://search/{query}")
def search_companies(query: str) -> str:
    """搜索公司。

    Args:
        query: 搜索关键词
    """
    try:
        from stock_analysis.registry import registry
        companies = list(registry().values())

        # 搜索公司
        query_upper = query.upper()
        results = []

        for company in companies:
            # 搜索名称、代码、市场
            name = company.get("name", "").upper()
            ticker = company.get("ticker", "").upper()
            market = company.get("market", "").upper()

            if (query_upper in name or
                query_upper in ticker or
                query_upper in market):
                results.append(company)

        search_result = {
            "query": query,
            "result_count": len(results),
            "results": results,
        }

        return json.dumps(search_result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"搜索公司失败: {str(e)}"}, ensure_ascii=False)
