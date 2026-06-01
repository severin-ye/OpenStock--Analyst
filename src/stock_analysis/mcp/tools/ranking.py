"""
MCP 排名工具模块

提供股票排名计算工具。
"""

from mcp.server.fastmcp import FastMCP, Context
from typing import Optional
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
        from ..server import AppContext
        ranker = AppContext.ranker
        
        # 获取公司数据
        from stock_analysis.registry import get_company_by_name
        company = get_company_by_name(ticker)
        
        if not company:
            return json.dumps({"error": f"未找到公司: {ticker}"}, ensure_ascii=False)
        
        # 计算排名
        ranking_result = ranker.rank_single(company)
        
        result = {
            "ticker": ticker,
            "company_name": company.get("name", ticker),
            "market": company.get("market", "Unknown"),
            "ranking": {
                "composite_rank": ranking_result.get("composite_rank"),
                "score_10": ranking_result.get("score_10"),
                "l1_rank": ranking_result.get("l1_rank"),
                "l2_rank": ranking_result.get("l2_rank"),
                "l3_rank": ranking_result.get("l3_rank"),
                "l4_rank": ranking_result.get("l4_rank"),
            },
            "metrics": {
                "ebit_ev": ranking_result.get("ebit_ev"),
                "roic": ranking_result.get("roic"),
                "f_score": ranking_result.get("f_score"),
                "peg": ranking_result.get("peg"),
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
    market: Optional[str] = None,
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
        from ..server import AppContext
        ranker = AppContext.ranker
        
        # 获取所有公司
        from stock_analysis.registry import get_all_companies
        companies = get_all_companies()
        
        # 按市场筛选
        if market:
            companies = [c for c in companies if c.get("market", "").upper() == market.upper()]
        
        # 计算排名
        rankings = ranker.rank_batch(companies)
        
        # 限制数量
        rankings = rankings[:limit]
        
        result = {
            "market": market or "All",
            "total_count": len(rankings),
            "rankings": []
        }
        
        for i, ranking in enumerate(rankings):
            result["rankings"].append({
                "rank": i + 1,
                "ticker": ranking.get("ticker"),
                "company_name": ranking.get("company_name"),
                "market": ranking.get("market"),
                "composite_rank": ranking.get("composite_rank"),
                "score_10": ranking.get("score_10"),
                "ebit_ev": ranking.get("ebit_ev"),
                "roic": ranking.get("roic"),
                "f_score": ranking.get("f_score"),
                "peg": ranking.get("peg"),
            })
        
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
        from ..server import AppContext
        ranker = AppContext.ranker
        
        results = {
            "comparison_count": len(tickers),
            "companies": []
        }
        
        for ticker in tickers:
            try:
                # 获取公司数据
                from stock_analysis.registry import get_company_by_name
                company = get_company_by_name(ticker)
                
                if not company:
                    results["companies"].append({
                        "ticker": ticker,
                        "error": f"未找到公司: {ticker}"
                    })
                    continue
                
                # 计算排名
                ranking_result = ranker.rank_single(company)
                
                results["companies"].append({
                    "ticker": ticker,
                    "company_name": company.get("name", ticker),
                    "market": company.get("market", "Unknown"),
                    "composite_rank": ranking_result.get("composite_rank"),
                    "score_10": ranking_result.get("score_10"),
                    "ebit_ev": ranking_result.get("ebit_ev"),
                    "roic": ranking_result.get("roic"),
                    "f_score": ranking_result.get("f_score"),
                    "peg": ranking_result.get("peg"),
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
