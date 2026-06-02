"""
MCP 数据工具模块

提供股票数据获取工具，按三档设计：
- 摘要型：get_price_summary, get_financial_summary, get_valuation_summary
- 任务型：calculate_ranking, compare_stocks, generate_report, validate_analysis
- 完整pipeline：full_analysis
"""

import json
from typing import Optional

from mcp.server.fastmcp import Context

from ..server import mcp


# ============ 摘要型工具 ============


@mcp.tool()
async def get_price_summary(
    ticker: str,
    ctx: Optional[Context] = None,
) -> str:
    """获取股票价格摘要。

    返回当前价格、市值、52周高低、PE等关键价格指标。

    Args:
        ticker: 股票代码 (如 "NVDA", "1810.HK", "小米")
    """
    if ctx:
        await ctx.info(f"正在获取 {ticker} 的价格摘要...")

    try:
        from stock_analysis.data.fetcher import fetch_yfinance
        from stock_analysis.registry import get_by_name_zh, registry

        # 查找公司
        company = get_by_name_zh(ticker)
        if not company:
            reg = registry()
            company = reg.get(ticker)

        if not company:
            return json.dumps({"error": f"未找到公司: {ticker}"}, ensure_ascii=False)

        company_ticker = company.get("ticker", ticker)
        snapshots = fetch_yfinance([company_ticker])
        snapshot = snapshots.get(company_ticker)

        if not snapshot:
            return json.dumps({"error": f"无法获取 {ticker} 的价格数据"}, ensure_ascii=False)

        result = {
            "ticker": company_ticker,
            "company_name": company.get("name_zh", ticker),
            "market": company.get("market", "Unknown"),
            "price_info": {
                "current_price": snapshot.price,
                "currency": snapshot.currency,
                "market_cap": snapshot.market_cap,
                "ytd_change": snapshot.ytd_change_pct,
                "week52_low": snapshot.week52_low,
                "week52_high": snapshot.week52_high,
                "pe_ratio": snapshot.pe_ratio,
                "forward_pe": snapshot.forward_pe,
                "beta": snapshot.beta,
            }
        }

        if ctx:
            await ctx.report_progress(100, 100, "价格摘要获取完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"价格摘要获取失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def get_financial_summary(
    ticker: str,
    ctx: Optional[Context] = None,
) -> str:
    """获取财务数据摘要。

    返回营收、利润、现金流等关键财务指标。

    Args:
        ticker: 股票代码
    """
    if ctx:
        await ctx.info(f"正在获取 {ticker} 的财务摘要...")

    try:
        from stock_analysis.data.fetcher import fetch_yfinance
        from stock_analysis.registry import get_by_name_zh, registry

        # 查找公司
        company = get_by_name_zh(ticker)
        if not company:
            reg = registry()
            company = reg.get(ticker)

        if not company:
            return json.dumps({"error": f"未找到公司: {ticker}"}, ensure_ascii=False)

        company_ticker = company.get("ticker", ticker)
        snapshots = fetch_yfinance([company_ticker])
        snapshot = snapshots.get(company_ticker)

        if not snapshot:
            return json.dumps({"error": f"无法获取 {ticker} 的财务数据"}, ensure_ascii=False)

        result = {
            "ticker": company_ticker,
            "company_name": company.get("name_zh", ticker),
            "financial_info": {
                "revenue": snapshot.revenue,
                "ebit": snapshot.ebit,
                "net_income": snapshot.net_income,
                "revenue_growth": snapshot.revenue_growth,
                "fcf_yield": snapshot.fcf_yield,
            }
        }

        if ctx:
            await ctx.report_progress(100, 100, "财务摘要获取完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"财务摘要获取失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def get_valuation_summary(
    ticker: str,
    ctx: Optional[Context] = None,
) -> str:
    """获取估值指标摘要。

    返回 EBIT/EV、ROIC、F-Score、PEG 等估值指标。

    Args:
        ticker: 股票代码
    """
    if ctx:
        await ctx.info(f"正在获取 {ticker} 的估值指标...")

    try:
        from stock_analysis.data.fetcher import fetch_yfinance
        from stock_analysis.registry import get_by_name_zh, registry

        # 查找公司
        company = get_by_name_zh(ticker)
        if not company:
            reg = registry()
            company = reg.get(ticker)

        if not company:
            return json.dumps({"error": f"未找到公司: {ticker}"}, ensure_ascii=False)

        company_ticker = company.get("ticker", ticker)
        snapshots = fetch_yfinance([company_ticker])
        snapshot = snapshots.get(company_ticker)

        if not snapshot:
            return json.dumps({"error": f"无法获取 {ticker} 的估值数据"}, ensure_ascii=False)

        result = {
            "ticker": company_ticker,
            "company_name": company.get("name_zh", ticker),
            "valuation_metrics": {
                "ebit_ev": snapshot.ebit_ev,
                "roic": snapshot.roic,
                "f_score": snapshot.f_score,
                "peg_ratio": snapshot.peg_ratio,
                "pe_ratio": snapshot.pe_ratio,
                "forward_pe": snapshot.forward_pe,
            },
            "note": "完整排名分析请使用 calculate_ranking 或 full_analysis"
        }

        if ctx:
            await ctx.report_progress(100, 100, "估值指标获取完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"估值指标获取失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# ============ 任务型工具 ============


@mcp.tool()
async def calculate_ranking(
    ticker: str,
    ctx: Optional[Context] = None,
) -> str:
    """计算单个公司的排名指标。

    返回 EBIT/EV、ROIC、F-Score、PEG 等指标，用于排名计算。

    Args:
        ticker: 股票代码
    """
    if ctx:
        await ctx.info(f"正在计算 {ticker} 的排名指标...")

    try:
        from stock_analysis.data.fetcher import fetch_yfinance
        from stock_analysis.registry import get_by_name_zh, registry

        # 查找公司
        company = get_by_name_zh(ticker)
        if not company:
            reg = registry()
            company = reg.get(ticker)

        if not company:
            return json.dumps({"error": f"未找到公司: {ticker}"}, ensure_ascii=False)

        company_ticker = company.get("ticker", ticker)
        snapshots = fetch_yfinance([company_ticker])
        snapshot = snapshots.get(company_ticker)

        if not snapshot:
            return json.dumps({"error": f"无法获取 {ticker} 的数据"}, ensure_ascii=False)

        result = {
            "ticker": company_ticker,
            "company_name": company.get("name_zh", ticker),
            "market": company.get("market", "Unknown"),
            "ranking_metrics": {
                "ebit_ev": snapshot.ebit_ev,
                "roic": snapshot.roic,
                "f_score": snapshot.f_score,
                "peg_ratio": snapshot.peg_ratio,
                "revenue_growth": snapshot.revenue_growth,
                "fcf_yield": snapshot.fcf_yield,
            },
            "note": "完整排名需要使用 full_analysis 生成完整报告"
        }

        if ctx:
            await ctx.report_progress(100, 100, "排名指标计算完成")

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"排名指标计算失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


@mcp.tool()
async def compare_stocks(
    tickers: list[str],
    ctx: Optional[Context] = None,
) -> str:
    """比较多個公司的指标数据。

    Args:
        tickers: 股票代码列表 (如 ["NVDA", "AAPL", "TSLA"])
    """
    if ctx:
        await ctx.info(f"正在比较 {len(tickers)} 家公司...")

    try:
        from stock_analysis.data.fetcher import fetch_yfinance
        from stock_analysis.registry import get_by_name_zh, registry

        results = {
            "comparison_count": len(tickers),
            "companies": []
        }

        for ticker in tickers:
            try:
                # 查找公司
                company = get_by_name_zh(ticker)
                if not company:
                    reg = registry()
                    company = reg.get(ticker)

                if not company:
                    results["companies"].append({
                        "ticker": ticker,
                        "error": f"未找到公司: {ticker}"
                    })
                    continue

                company_ticker = company.get("ticker", ticker)
                snapshots = fetch_yfinance([company_ticker])
                snapshot = snapshots.get(company_ticker)

                if not snapshot:
                    results["companies"].append({
                        "ticker": ticker,
                        "error": "无法获取数据"
                    })
                    continue

                results["companies"].append({
                    "ticker": company_ticker,
                    "company_name": company.get("name_zh", ticker),
                    "market": company.get("market", "Unknown"),
                    "price": snapshot.price,
                    "market_cap": snapshot.market_cap,
                    "pe_ratio": snapshot.pe_ratio,
                    "ebit_ev": snapshot.ebit_ev,
                    "roic": snapshot.roic,
                    "f_score": snapshot.f_score,
                    "peg_ratio": snapshot.peg_ratio,
                })
            except Exception as e:
                results["companies"].append({
                    "ticker": ticker,
                    "error": str(e)
                })

        # 按 EBIT/EV 排序
        valid_companies = [c for c in results["companies"] if "error" not in c]
        try:
            valid_companies.sort(
                key=lambda x: float(x.get("ebit_ev", "0").rstrip("%")) if x.get("ebit_ev") else 0,
                reverse=True
            )
        except (ValueError, AttributeError):
            pass

        for i, company in enumerate(valid_companies):
            company["ebit_ev_rank"] = i + 1

        if ctx:
            await ctx.report_progress(100, 100, "公司比较完成")

        return json.dumps(results, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"公司比较失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# ============ 完整pipeline工具 ============


@mcp.tool()
async def full_analysis(
    ticker: str,
    dry_run: bool = False,
    ctx: Optional[Context] = None,
) -> str:
    """执行完整的股票分析。

    这是完整的分析pipeline，包括数据获取、排名计算、报告生成等所有步骤。

    Args:
        ticker: 股票代码或中文名
        dry_run: 是否只获取数据和排名，不调用LLM生成报告
    """
    if ctx:
        await ctx.info(f"正在对 {ticker} 进行完整分析...")

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
        result = run_analysis(company_name, dry_run=dry_run)

        if result:
            response = {
                "ticker": ticker,
                "company_name": company_name,
                "status": "success",
                "dry_run": dry_run,
                "message": "分析完成" if not dry_run else "数据获取和排名计算完成（dry_run模式）",
                "output_dir": f"output/{company_name}",
            }
        else:
            response = {
                "ticker": ticker,
                "company_name": company_name,
                "status": "failed",
                "message": "分析失败，请检查日志",
            }

        if ctx:
            await ctx.report_progress(100, 100, "完整分析完成")

        return json.dumps(response, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"完整分析失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)
