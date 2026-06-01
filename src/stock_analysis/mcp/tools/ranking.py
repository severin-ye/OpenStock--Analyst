"""
MCP 排名工具模块

提供股票排名计算工具。
"""

from mcp.server.fastmcp import FastMCP, Context
import json

# 获取服务器实例
from ..server import mcp


@mcp.tool()
async def calculate_ranking(
    ticker: str,
    ctx: Context = None,
) -> str:
    """计算单个公司的排名。
    
    Args:
        ticker: 股票代码 (如 "NVDA", "1810.HK")
    """
    if ctx:
        await ctx.info(f"正在计算 {ticker} 的排名...")
    
    try:
        from stock_analysis.registry import get_by_name_zh, registry
        from stock_analysis.ranking.greenblatt import compute_greenblatt
        from stock_analysis.data.fetcher import fetch_yfinance, PriceSnapshot
        
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
        snapshot = fetch_yfinance(company_ticker)
        
        if not snapshot:
            return json.dumps({"error": f"无法获取 {ticker} 的价格数据"}, ensure_ascii=False)
        
        # 计算排名
        ranking_result = compute_greenblatt(snapshot)
        
        result = {
            "ticker": company_ticker,
            "company_name": company.get("name_zh", ticker),
            "market": company.get("market", "Unknown"),
            "ranking": {
                "composite_rank": ranking_result.composite_rank if ranking_result else None,
                "score_10": ranking_result.score_10 if ranking_result else None,
                "l1_rank": ranking_result.l1_rank if ranking_result else None,
                "l2_rank": ranking_result.l2_rank if ranking_result else None,
                "l3_rank": ranking_result.l3_rank if ranking_result else None,
                "l4_rank": ranking_result.l4_rank if ranking_result else None,
            },
            "metrics": {
                "ebit_ev": snapshot.ebit_ev,
                "roic": snapshot.roic,
                "f_score": snapshot.f_score,
                "peg": snapshot.peg_ratio,
            }
        }
        
        if ctx:
            await ctx.report_progress(100, 100, "排名计算完成")
        
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"排名计算失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def get_rankings(
    market: str = None,
    limit: int = 10,
    ctx: Context = None,
) -> str:
    """获取公司排名列表。
    
    Args:
        market: 市场筛选 (如 "US", "HK", "JP", "KR", "CN", "Crypto")
        limit: 返回数量限制
    """
    if ctx:
        await ctx.info(f"正在获取排名数据...")
    
    try:
        from stock_analysis.registry import registry, MARKET_GROUPS
        from stock_analysis.ranking.greenblatt import compute_greenblatt
        from stock_analysis.data.fetcher import fetch_yfinance
        
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
        
        # 计算排名
        rankings = []
        for company in companies[:limit]:  # 限制处理数量
            try:
                ticker = company.get("ticker")
                snapshot = fetch_yfinance(ticker)
                if snapshot:
                    ranking_result = compute_greenblatt(snapshot)
                    if ranking_result:
                        rankings.append({
                            "ticker": ticker,
                            "company_name": company.get("name_zh", ticker),
                            "market": company.get("market", "Unknown"),
                            "composite_rank": ranking_result.composite_rank,
                            "score_10": ranking_result.score_10,
                            "ebit_ev": snapshot.ebit_ev,
                            "roic": snapshot.roic,
                            "f_score": snapshot.f_score,
                            "peg": snapshot.peg_ratio,
                        })
            except Exception:
                continue
        
        # 按综合排名排序
        rankings.sort(key=lambda x: x.get("composite_rank", float("inf")))
        
        result = {
            "market": market or "All",
            "total_count": len(rankings),
            "rankings": rankings[:limit]
        }
        
        if ctx:
            await ctx.report_progress(100, 100, "排名数据获取完成")
        
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"排名数据获取失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def compare_rankings(
    tickers: list[str],
    ctx: Context = None,
) -> str:
    """比较多個公司的排名。
    
    Args:
        tickers: 股票代码列表 (如 ["NVDA", "AAPL", "TSLA"])
    """
    if ctx:
        await ctx.info(f"正在比较 {len(tickers)} 家公司的排名...")
    
    try:
        from stock_analysis.registry import get_by_name_zh, registry
        from stock_analysis.ranking.greenblatt import compute_greenblatt
        from stock_analysis.data.fetcher import fetch_yfinance
        
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
                snapshot = fetch_yfinance(company_ticker)
                
                if not snapshot:
                    results["companies"].append({
                        "ticker": ticker,
                        "error": f"无法获取价格数据"
                    })
                    continue
                
                # 计算排名
                ranking_result = compute_greenblatt(snapshot)
                
                results["companies"].append({
                    "ticker": company_ticker,
                    "company_name": company.get("name_zh", ticker),
                    "market": company.get("market", "Unknown"),
                    "composite_rank": ranking_result.composite_rank if ranking_result else None,
                    "score_10": ranking_result.score_10 if ranking_result else None,
                    "ebit_ev": snapshot.ebit_ev,
                    "roic": snapshot.roic,
                    "f_score": snapshot.f_score,
                    "peg": snapshot.peg_ratio,
                })
            except Exception as e:
                results["companies"].append({
                    "ticker": ticker,
                    "error": str(e)
                })
        
        # 按综合排名排序
        valid_companies = [c for c in results["companies"] if "error" not in c]
        valid_companies.sort(key=lambda x: x.get("composite_rank", float("inf")))
        
        for i, company in enumerate(valid_companies):
            company["rank"] = i + 1
        
        if ctx:
            await ctx.report_progress(100, 100, "排名比较完成")
        
        return json.dumps(results, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"排名比较失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)
