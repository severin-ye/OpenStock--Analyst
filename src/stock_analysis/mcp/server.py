"""
Stock Analysis MCP Server

提供股票分析功能的 MCP 服务器实现。
包含工具、资源和提示，用于股票分析、排名计算和报告生成。
"""

from mcp.server.fastmcp import FastMCP
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Any
import json
import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from stock_analysis.registry import get_company_by_name, get_all_companies
from stock_analysis.data.fetcher import DataFetcher
from stock_analysis.ranking.greenblatt import GreenblattRanker
from stock_analysis.analysis import (
    TechnicalAnalyzer,
    InsiderAnalyzer,
    InstitutionalAnalyzer,
    EarningsAnalyzer,
    SectorAnalyzer,
    EconomicsAnalyzer,
    CompetitorAnalyzer,
    NarrativeAnalyzer,
    ResultValidator,
)


class AppContext:
    """应用上下文，存储共享资源。"""
    
    def __init__(self):
        self.fetcher = DataFetcher()
        self.ranker = GreenblattRanker()
        self.analyzers = {
            "technical": TechnicalAnalyzer(),
            "insider": InsiderAnalyzer(),
            "institutional": InstitutionalAnalyzer(),
            "earnings": EarningsAnalyzer(),
            "sector": SectorAnalyzer(),
            "economics": EconomicsAnalyzer(),
            "competitor": CompetitorAnalyzer(),
            "narrative": NarrativeAnalyzer(),
        }
        self.validator = ResultValidator()
    
    async def initialize(self):
        """初始化资源。"""
        print("Stock Analysis MCP Server initialized")


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """应用生命周期管理。"""
    context = AppContext()
    await context.initialize()
    
    try:
        yield context
    finally:
        print("Stock Analysis MCP Server cleaned up")


# 创建 MCP 服务器
mcp = FastMCP(
    name="stock-analysis",
    instructions="股票分析 MCP 服务器，提供股票分析、排名计算和报告生成功能。",
    lifespan=app_lifespan,
)


# 导入工具、资源和提示
from .tools import analysis, ranking, data, report
from .resources import companies, prices, reports
from .prompts import analysis as analysis_prompts, report as report_prompts


def main():
    """启动 MCP 服务器。"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Stock Analysis MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="传输方式 (默认: stdio)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="HTTP 传输的主机")
    parser.add_argument("--port", type=int, default=8000, help="HTTP 传输的端口")
    
    args = parser.parse_args()
    
    if args.transport == "streamable-http":
        mcp.settings.host = args.host
        mcp.settings.port = args.port
    
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
