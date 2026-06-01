"""
MCP 数据工具模块

提供数据获取和刷新工具。
"""

from mcp.server.fastmcp import FastMCP, Context
from typing import Optional
import json

# 获取服务器实例
from ..server import mcp


@mcp.tool()
async def refresh_data(
    ticker: Optional[str] = None,
    ctx: Context = None,
) -> str:
    """刷新价格数据。
    
    Args:
        ticker: 股票代码 (可选，不提供则刷新所有)
    """
    if ctx:
        if ticker:
            await ctx.info(f"正在刷新 {ticker} 的价格数据...")
        else:
            await ctx.info("正在刷新所有价格数据...")
    
    try:
        from ..server import AppContext
        fetcher = AppContext.fetcher
        
        if ticker:
            # 刷新单个公司
            from stock_analysis.registry import get_company_by_name
            company = get_company_by_name(ticker)
            
            if not company:
                return json.dumps({"error": f"未找到公司: {ticker}"}, ensure_ascii=False)
            
            result = fetcher.refresh_company(company)
            
            refresh_result = {
                "ticker": ticker,
                "company_name": company.get("name", ticker),
                "refresh_status": "success" if result else "failed",
                "details": result,
            }
        else:
            # 刷新所有公司
            from stock_analysis.registry import get_all_companies
            companies = get_all_companies()
            
            results = {}
            total = len(companies)
            
            for i, company in enumerate(companies):
                if ctx:
                    await ctx.report_progress(i + 1, total, f"正在刷新 {company.get('ticker', '')}...")
                
                try:
                    result = fetcher.refresh_company(company)
                    results[company.get("ticker", "")] = {
                        "status": "success" if result else "failed",
                        "details": result,
                    }
                except Exception as e:
                    results[company.get("ticker", "")] = {
                        "status": "error",
                        "error": str(e),
                    }
            
            refresh_result = {
                "refresh_type": "all",
                "total_count": total,
                "results": results,
            }
        
        if ctx:
            await ctx.report_progress(100, 100, "数据刷新完成")
        
        return json.dumps(refresh_result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"数据刷新失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def get_price_data(
    ticker: str,
    period: str = "1y",
    ctx: Context = None,
) -> str:
    """获取价格数据。
    
    Args:
        ticker: 股票代码
        period: 数据周期 (如 "1y", "6mo", "3mo", "1mo")
    """
    if ctx:
        await ctx.info(f"正在获取 {ticker} 的价格数据...")
    
    try:
        from ..server import AppContext
        fetcher = AppContext.fetcher
        
        # 获取公司信息
        from stock_analysis.registry import get_company_by_name
        company = get_company_by_name(ticker)
        
        if not company:
            return json.dumps({"error": f"未找到公司: {ticker}"}, ensure_ascii=False)
        
        # 获取价格数据
        price_data = fetcher.get_price_data(company, period=period)
        
        result = {
            "ticker": ticker,
            "company_name": company.get("name", ticker),
            "period": period,
            "data_points": len(price_data) if price_data else 0,
            "price_data": price_data,
        }
        
        if ctx:
            await ctx.report_progress(100, 100, "价格数据获取完成")
        
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"价格数据获取失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def get_financial_data(
    ticker: str,
    ctx: Context = None,
) -> str:
    """获取财务数据。
    
    Args:
        ticker: 股票代码
    """
    if ctx:
        await ctx.info(f"正在获取 {ticker} 的财务数据...")
    
    try:
        from ..server import AppContext
        fetcher = AppContext.fetcher
        
        # 获取公司信息
        from stock_analysis.registry import get_company_by_name
        company = get_company_by_name(ticker)
        
        if not company:
            return json.dumps({"error": f"未找到公司: {ticker}"}, ensure_ascii=False)
        
        # 获取财务数据
        financial_data = fetcher.get_financial_data(company)
        
        result = {
            "ticker": ticker,
            "company_name": company.get("name", ticker),
            "financial_data": financial_data,
        }
        
        if ctx:
            await ctx.report_progress(100, 100, "财务数据获取完成")
        
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"财务数据获取失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def get_market_data(
    market: str,
    ctx: Context = None,
) -> str:
    """获取市场数据。
    
    Args:
        market: 市场代码 (如 "US", "HK", "JP", "KR", "CN", "Crypto")
    """
    if ctx:
        await ctx.info(f"正在获取 {market} 市场的数据...")
    
    try:
        from stock_analysis.registry import get_all_companies
        
        # 获取所有公司
        companies = get_all_companies()
        
        # 按市场筛选
        market_companies = [c for c in companies if c.get("market", "").upper() == market.upper()]
        
        result = {
            "market": market,
            "company_count": len(market_companies),
            "companies": market_companies,
        }
        
        if ctx:
            await ctx.report_progress(100, 100, "市场数据获取完成")
        
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"市场数据获取失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)
