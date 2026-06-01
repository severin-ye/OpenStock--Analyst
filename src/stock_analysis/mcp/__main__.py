"""
Stock Analysis MCP Server 入口点

允许通过 python -m stock_analysis.mcp 运行服务器。
"""

from .server import main

if __name__ == "__main__":
    main()
