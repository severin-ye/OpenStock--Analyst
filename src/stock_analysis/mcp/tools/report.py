"""
MCP 报告工具模块

提供报告生成工具。
"""

from mcp.server.fastmcp import FastMCP, Context
from typing import Optional
import json
import os

# 获取服务器实例
from ..server import mcp


@mcp.tool()
async def generate_report(
    ticker: str,
    report_type: str = "html",
    output_dir: Optional[str] = None,
    ctx: Context = None,
) -> str:
    """生成股票分析报告。
    
    Args:
        ticker: 股票代码
        report_type: 报告类型 (html/markdown)
        output_dir: 输出目录 (可选)
    """
    if ctx:
        await ctx.info(f"正在生成 {ticker} 的分析报告...")
    
    try:
        from ..server import AppContext
        
        # 获取公司信息
        from stock_analysis.registry import get_company_by_name
        company = get_company_by_name(ticker)
        
        if not company:
            return json.dumps({"error": f"未找到公司: {ticker}"}, ensure_ascii=False)
        
        # 执行分析
        analyzers = AppContext.analyzers
        analysis_results = {}
        
        for name, analyzer in analyzers.items():
            try:
                if name == "economics":
                    signal = analyzer.analyze()
                else:
                    signal = analyzer.analyze(ticker)
                analysis_results[name] = signal
            except Exception as e:
                analysis_results[name] = {"error": str(e)}
        
        # 计算排名
        ranker = AppContext.ranker
        ranking_result = ranker.rank_single(company)
        
        # 生成报告
        if report_type == "html":
            report_content = await generate_html_report(
                ticker, company, analysis_results, ranking_result
            )
            file_extension = "html"
        else:
            report_content = await generate_markdown_report(
                ticker, company, analysis_results, ranking_result
            )
            file_extension = "md"
        
        # 确定输出路径
        if not output_dir:
            output_dir = os.path.join(os.getcwd(), "分析输出", company.get("name", ticker))
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成文件名
        from datetime import datetime
        date_str = datetime.now().strftime("%y%m%d")
        filename = f"{date_str}-01_整体分析.{file_extension}"
        filepath = os.path.join(output_dir, filename)
        
        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        result = {
            "ticker": ticker,
            "company_name": company.get("name", ticker),
            "report_type": report_type,
            "output_path": filepath,
            "file_size": os.path.getsize(filepath),
            "analysis_count": len(analysis_results),
            "ranking": ranking_result,
        }
        
        if ctx:
            await ctx.report_progress(100, 100, "报告生成完成")
        
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"报告生成失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


async def generate_html_report(
    ticker: str,
    company: dict,
    analysis_results: dict,
    ranking_result: dict,
) -> str:
    """生成 HTML 报告。"""
    from jinja2 import Template
    
    # 简化的 HTML 模板
    template_str = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company.name }} - 股票分析报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background-color: #f5f5f5; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background-color: #e9ecef; border-radius: 5px; }
        .signal-bullish { color: green; }
        .signal-bearish { color: red; }
        .signal-neutral { color: gray; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ company.name }} ({{ ticker }})</h1>
        <p>市场: {{ company.market }} | 分析日期: {{ date }}</p>
    </div>
    
    <div class="section">
        <h2>排名信息</h2>
        <div class="metric">综合排名: {{ ranking.composite_rank }}</div>
        <div class="metric">评分: {{ ranking.score_10 }}/10</div>
        <div class="metric">EBIT/EV: {{ ranking.ebit_ev }}</div>
        <div class="metric">ROIC: {{ ranking.roic }}</div>
        <div class="metric">F-Score: {{ ranking.f_score }}</div>
        <div class="metric">PEG: {{ ranking.peg }}</div>
    </div>
    
    <div class="section">
        <h2>分析结果</h2>
        {% for name, result in analysis_results.items() %}
        <div class="metric">
            <strong>{{ name }}:</strong>
            {% if result.error %}
            <span class="signal-bearish">错误: {{ result.error }}</span>
            {% else %}
            <span class="signal-{{ result.signal | lower }}">{{ result.signal }}</span>
            {% endif %}
        </div>
        {% endfor %}
    </div>
</body>
</html>
    """
    
    template = Template(template_str)
    
    from datetime import datetime
    return template.render(
        ticker=ticker,
        company=company,
        ranking=ranking_result,
        analysis_results=analysis_results,
        date=datetime.now().strftime("%Y-%m-%d"),
    )


async def generate_markdown_report(
    ticker: str,
    company: dict,
    analysis_results: dict,
    ranking_result: dict,
) -> str:
    """生成 Markdown 报告。"""
    from datetime import datetime
    
    report = f"""# {company.get('name', ticker)} ({ticker}) - 股票分析报告

**市场**: {company.get('market', 'Unknown')}  
**分析日期**: {datetime.now().strftime("%Y-%m-%d")}

## 排名信息

| 指标 | 值 |
|------|-----|
| 综合排名 | {ranking_result.get('composite_rank', 'N/A')} |
| 评分 | {ranking_result.get('score_10', 'N/A')}/10 |
| EBIT/EV | {ranking_result.get('ebit_ev', 'N/A')} |
| ROIC | {ranking_result.get('roic', 'N/A')} |
| F-Score | {ranking_result.get('f_score', 'N/A')} |
| PEG | {ranking_result.get('peg', 'N/A')} |

## 分析结果

"""
    
    for name, result in analysis_results.items():
        if isinstance(result, dict) and "error" in result:
            report += f"### {name}\n\n**错误**: {result['error']}\n\n"
        else:
            signal = getattr(result, 'signal', 'N/A')
            report += f"### {name}\n\n**信号**: {signal}\n\n"
    
    return report


@mcp.tool()
async def list_reports(
    ticker: Optional[str] = None,
    ctx: Context = None,
) -> str:
    """列出分析报告。
    
    Args:
        ticker: 股票代码 (可选)
    """
    if ctx:
        await ctx.info("正在列出分析报告...")
    
    try:
        # 分析输出目录
        output_dir = os.path.join(os.getcwd(), "分析输出")
        
        if not os.path.exists(output_dir):
            return json.dumps({"reports": [], "message": "分析输出目录不存在"}, ensure_ascii=False)
        
        reports = []
        
        # 遍历目录
        for company_dir in os.listdir(output_dir):
            company_path = os.path.join(output_dir, company_dir)
            
            if not os.path.isdir(company_path):
                continue
            
            # 如果指定了 ticker，只列出该公司的报告
            if ticker and ticker.upper() not in company_dir.upper():
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
        
        if ctx:
            await ctx.report_progress(100, 100, "报告列表获取完成")
        
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"报告列表获取失败: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)
