"""
MCP 价格资源模块

提供价格数据资源。
"""

import json
import os

# 获取服务器实例
from ..server import mcp


@mcp.resource("prices://{ticker}")
def get_price_data(ticker: str) -> str:
    """获取价格数据。

    Args:
        ticker: 股票代码
    """
    try:
        # 从 prices.json 缓存中获取数据
        prices_file = os.path.join(os.getcwd(), "data", "prices.json")

        if not os.path.exists(prices_file):
            return json.dumps({"error": "价格数据文件不存在"}, ensure_ascii=False)

        with open(prices_file, "r", encoding="utf-8") as f:
            prices_data = json.load(f)

        # 查找特定公司的价格数据
        ticker_upper = ticker.upper()
        price_info = None

        for company_data in prices_data:
            if company_data.get("ticker", "").upper() == ticker_upper:
                price_info = company_data
                break

        if not price_info:
            return json.dumps({"error": f"未找到 {ticker} 的价格数据"}, ensure_ascii=False)

        return json.dumps(price_info, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"获取价格数据失败: {str(e)}"}, ensure_ascii=False)


@mcp.resource("prices://all")
def get_all_prices() -> str:
    """获取所有价格数据。"""
    try:
        # 从 prices.json 缓存中获取数据
        prices_file = os.path.join(os.getcwd(), "data", "prices.json")

        if not os.path.exists(prices_file):
            return json.dumps({"error": "价格数据文件不存在"}, ensure_ascii=False)

        with open(prices_file, "r", encoding="utf-8") as f:
            prices_data = json.load(f)

        result = {
            "total_count": len(prices_data),
            "prices": prices_data,
        }

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"获取价格数据失败: {str(e)}"}, ensure_ascii=False)


@mcp.resource("prices://market/{market}")
def get_prices_by_market(market: str) -> str:
    """获取特定市场的价格数据。

    Args:
        market: 市场代码 (如 "US", "HK", "JP", "KR", "CN", "Crypto")
    """
    try:
        # 从 prices.json 缓存中获取数据
        prices_file = os.path.join(os.getcwd(), "data", "prices.json")

        if not os.path.exists(prices_file):
            return json.dumps({"error": "价格数据文件不存在"}, ensure_ascii=False)

        with open(prices_file, "r", encoding="utf-8") as f:
            prices_data = json.load(f)

        # 按市场筛选
        market_prices = []
        for company_data in prices_data:
            # 这里需要根据实际情况判断市场
            # 简单示例：根据 ticker 后缀判断
            ticker = company_data.get("ticker", "")
            if market.upper() == "US" and "." not in ticker:
                market_prices.append(company_data)
            elif market.upper() == "HK" and ".HK" in ticker:
                market_prices.append(company_data)
            elif market.upper() == "JP" and ".T" in ticker:
                market_prices.append(company_data)
            elif market.upper() == "KR" and ".KS" in ticker:
                market_prices.append(company_data)
            elif market.upper() == "CN" and ".SS" in ticker:
                market_prices.append(company_data)
            elif market.upper() == "CRYPTO" and ticker in ["BTC", "ETH", "SOL", "BNB"]:
                market_prices.append(company_data)

        result = {
            "market": market,
            "company_count": len(market_prices),
            "prices": market_prices,
        }

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"获取市场价格数据失败: {str(e)}"}, ensure_ascii=False)
