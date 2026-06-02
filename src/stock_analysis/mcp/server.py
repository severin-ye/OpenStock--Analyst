"""
Stock Analysis MCP Server

提供股票分析功能的 MCP 服务器实现。
包含工具、资源和提示，用于股票分析、排名计算和报告生成。
"""

import os
import sys

from mcp.server.fastmcp import FastMCP

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# 创建 MCP 服务器
mcp = FastMCP(
    name="stock-analysis",
    instructions="""股票分析 MCP 服务器，提供股票分析、排名计算和报告生成功能。

工具分三档：
1. 摘要型：get_price_summary, get_financial_summary, get_valuation_summary
2. 任务型：calculate_ranking, compare_stocks, generate_report, validate_analysis
3. 完整pipeline：full_analysis

专业分析：technical_analysis, insider_analysis, institutional_analysis, earnings_analysis, sector_analysis, economics_analysis, competitor_analysis, narrative_analysis""",
)


# 导入工具、资源和提示


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
