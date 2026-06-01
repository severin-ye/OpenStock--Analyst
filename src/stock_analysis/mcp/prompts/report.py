"""
MCP 报告提示模块

提供报告生成相关的提示模板。
"""

from mcp.server.fastmcp import FastMCP

# 获取服务器实例
from ..server import mcp


@mcp.prompt()
def report_generation_prompt(
    ticker: str,
    report_type: str = "full",
) -> str:
    """生成报告创建提示。
    
    Args:
        ticker: 股票代码
        report_type: 报告类型 (full/summary/quick)
    """
    if report_type == "full":
        return f"""请为 {ticker} 生成一份完整的股票分析报告：

报告结构：
1. **封面**：公司名称、代码、分析日期、关键指标
2. **执行摘要**：核心投资观点和结论
3. **公司概况**：业务模式、市场地位、竞争优势
4. **财务分析**：盈利能力、估值水平、财务健康度
5. **技术分析**：价格走势、技术指标、趋势判断
6. **风险分析**：主要风险因素、风险等级
7. **投资建议**：买入/持有/卖出建议、目标价位
8. **附录**：详细数据、分析方法说明

请使用以下工具获取数据：
- `get_company_info` 获取公司信息
- `calculate_ranking` 获取排名数据
- `technical_analysis` 进行技术分析
- `validate_analysis` 验证分析结果

使用 `generate_report` 工具生成最终报告。"""
    
    elif report_type == "summary":
        return f"""请为 {ticker} 生成一份简要分析报告：

报告结构：
1. **核心观点**：一句话投资结论
2. **关键指标**：最重要的3-5个指标
3. **风险提示**：主要风险点
4. **投资建议**：明确的操作建议

请使用 `calculate_ranking` 和 `technical_analysis` 获取关键数据。"""
    
    else:  # quick
        return f"""请为 {ticker} 生成一份快速分析报告：

报告内容：
1. **当前状态**：价格、涨跌幅、市值
2. **排名情况**：综合排名、各项指标
3. **简单结论**：是否值得关注

请使用 `calculate_ranking` 获取排名数据。"""


@mcp.prompt()
def batch_report_prompt(
    tickers: list[str],
) -> str:
    """生成批量报告提示。
    
    Args:
        tickers: 股票代码列表
    """
    return f"""请为以下股票生成批量分析报告：

{', '.join(tickers)}

报告要求：
1. **对比分析**：横向对比各股票的关键指标
2. **排名汇总**：综合排名和各项指标排名
3. **投资组合建议**：哪些股票值得投资
4. **风险分散**：如何构建投资组合

请使用以下工具：
- `compare_rankings` 比较排名
- `get_company_info` 获取公司信息
- `calculate_ranking` 计算排名

最后，请生成一份综合投资建议报告。"""


@mcp.prompt()
def report_update_prompt(
    ticker: str,
    existing_report: str,
) -> str:
    """生成报告更新提示。
    
    Args:
        ticker: 股票代码
        existing_report: 现有报告内容
    """
    return f"""请更新 {ticker} 的分析报告：

现有报告内容：
{existing_report}

更新要求：
1. **数据更新**：更新最新价格、财务数据
2. **观点更新**：根据最新情况调整投资观点
3. **风险更新**：更新风险因素和风险等级
4. **建议更新**：调整投资建议

请使用以下工具获取最新数据：
- `get_price_data` 获取最新价格
- `calculate_ranking` 重新计算排名
- `technical_analysis` 更新技术分析

最后，请生成更新后的完整报告。"""
