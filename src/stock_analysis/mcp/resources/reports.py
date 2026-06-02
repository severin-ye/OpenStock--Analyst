"""
MCP 报告资源模块

提供分析报告资源。
"""

import json
import os

# 获取服务器实例
from ..server import mcp


@mcp.resource("reports://list")
def get_reports_list() -> str:
    """获取所有报告列表。"""
    try:
        # 输出目录
        output_dir = os.path.join(os.getcwd(), "output")

        if not os.path.exists(output_dir):
            return json.dumps({"reports": [], "message": "输出目录不存在"}, ensure_ascii=False)

        reports = []

        # 遍历目录
        for company_dir in os.listdir(output_dir):
            company_path = os.path.join(output_dir, company_dir)

            if not os.path.isdir(company_path):
                continue

            # 列出该公司的所有报告
            for filename in os.listdir(company_path):
                filepath = os.path.join(company_path, filename)

                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    reports.append({
                        "company": company_dir,
                        "filename": filename,
                        "filepath": filepath,
                        "file_size": stat.st_size,
                        "modified_time": stat.st_mtime,
                    })

        # 按修改时间排序
        reports.sort(key=lambda x: x["modified_time"], reverse=True)

        result = {
            "report_count": len(reports),
            "reports": reports,
        }

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"获取报告列表失败: {str(e)}"}, ensure_ascii=False)


@mcp.resource("reports://{ticker}")
def get_reports_by_ticker(ticker: str) -> str:
    """获取特定公司的报告列表。

    Args:
        ticker: 股票代码
    """
    try:
        # 输出目录
        output_dir = os.path.join(os.getcwd(), "output")

        if not os.path.exists(output_dir):
            return json.dumps({"reports": [], "message": "输出目录不存在"}, ensure_ascii=False)

        reports = []

        # 遍历目录
        for company_dir in os.listdir(output_dir):
            company_path = os.path.join(output_dir, company_dir)

            if not os.path.isdir(company_path):
                continue

            # 如果指定了 ticker，只列出该公司的报告
            if ticker.upper() not in company_dir.upper():
                continue

            # 列出该公司的所有报告
            for filename in os.listdir(company_path):
                filepath = os.path.join(company_path, filename)

                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    reports.append({
                        "company": company_dir,
                        "filename": filename,
                        "filepath": filepath,
                        "file_size": stat.st_size,
                        "modified_time": stat.st_mtime,
                    })

        # 按修改时间排序
        reports.sort(key=lambda x: x["modified_time"], reverse=True)

        result = {
            "ticker": ticker,
            "report_count": len(reports),
            "reports": reports,
        }

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"获取公司报告失败: {str(e)}"}, ensure_ascii=False)


@mcp.resource("reports://{ticker}/{filename}")
def get_report_content(ticker: str, filename: str) -> str:
    """获取特定报告内容。

    Args:
        ticker: 股票代码
        filename: 报告文件名
    """
    try:
        # 输出目录
        output_dir = os.path.join(os.getcwd(), "output")

        if not os.path.exists(output_dir):
            return json.dumps({"error": "输出目录不存在"}, ensure_ascii=False)

        # 查找公司目录
        company_dir = None
        for dir_name in os.listdir(output_dir):
            if ticker.upper() in dir_name.upper():
                company_dir = dir_name
                break

        if not company_dir:
            return json.dumps({"error": f"未找到 {ticker} 的报告目录"}, ensure_ascii=False)

        # 构建文件路径
        filepath = os.path.join(output_dir, company_dir, filename)

        if not os.path.exists(filepath):
            return json.dumps({"error": f"未找到报告文件: {filename}"}, ensure_ascii=False)

        # 读取文件内容
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        result = {
            "ticker": ticker,
            "filename": filename,
            "filepath": filepath,
            "content": content,
        }

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"获取报告内容失败: {str(e)}"}, ensure_ascii=False)
