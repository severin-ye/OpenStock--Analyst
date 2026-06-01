"""
MCP 分析提示模块

提供股票分析相关的提示模板。
"""

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import UserMessage, AssistantMessage

# 获取服务器实例
from ..server import mcp


@mcp.prompt()
def stock_analysis_prompt(
    ticker: str,
    analysis_depth: str = "full",
) -> str:
    """生成股票分析提示。
    
    Args:
        ticker: 股票代码
        analysis_depth: 分析深度 (full/quick/basic)
    """
    if analysis_depth == "full":
        return f"""请对 {ticker} 进行全面的股票分析，包括：

1. **技术分析**：分析价格趋势、支撑阻力位、技术指标（RSI、MACD等）
2. **基本面分析**：查看财务数据、盈利能力、估值水平
3. **内部人交易**：分析内部人买卖情况
4. **机构持仓**：查看机构持仓变化
5. **财报分析**：分析最近财报电话会议内容
6. **行业分析**：查看行业轮动和竞争格局
7. **宏观经济**：分析当前经济周期和政策环境
8. **叙事分析**：识别市场主题和情绪

请使用以下工具：
- `technical_analysis` 进行技术分析
- `insider_analysis` 分析内部人交易
- `institutional_analysis` 分析机构持仓
- `earnings_analysis` 分析财报
- `sector_analysis` 分析行业
- `economics_analysis` 分析宏观经济
- `competitor_analysis` 分析竞争格局
- `narrative_analysis` 分析叙事

最后，请给出综合投资建议和风险提示。"""
    
    elif analysis_depth == "quick":
        return f"""请对 {ticker} 进行快速分析，重点关注：

1. **技术分析**：当前趋势和关键指标
2. **估值水平**：是否被低估或高估
3. **风险因素**：主要风险点

请使用 `technical_analysis` 和 `calculate_ranking` 工具获取数据。"""
    
    else:  # basic
        return f"""请查看 {ticker} 的基本信息和当前排名。

使用 `get_company_info` 获取公司信息。
使用 `calculate_ranking` 获取排名数据。"""


@mcp.prompt()
def comparison_prompt(
    ticker1: str,
    ticker2: str,
) -> str:
    """生成公司对比提示。
    
    Args:
        ticker1: 第一个股票代码
        ticker2: 第二个股票代码
    """
    return f"""请对比 {ticker1} 和 {ticker2} 两只股票：

1. **基本信息对比**：公司规模、市场地位、行业分类
2. **财务指标对比**：盈利能力、估值水平、增长潜力
3. **技术面对比**：价格走势、技术指标
4. **风险对比**：各自的风险因素
5. **投资建议**：哪只股票更具投资价值

请使用以下工具获取数据：
- `get_company_info` 获取公司信息
- `calculate_ranking` 获取排名数据
- `technical_analysis` 进行技术分析

最后，请给出明确的对比结论。"""


@mcp.prompt()
def sector_analysis_prompt(
    sector: str,
) -> str:
    """生成行业分析提示。
    
    Args:
        sector: 行业名称
    """
    return f"""请对 {sector} 行业进行全面分析：

1. **行业概况**：行业定义、主要参与者、市场规模
2. **行业趋势**：当前发展方向、技术创新、政策影响
3. **竞争格局**：主要竞争者、市场份额、竞争壁垒
4. **投资机会**：哪些公司值得关注
5. **风险因素**：行业面临的主要风险

请使用 `get_companies_by_market` 获取行业相关公司。
使用 `sector_analysis` 分析行业情况。

最后，请给出行业投资建议。"""


@mcp.prompt()
def risk_assessment_prompt(
    ticker: str,
) -> str:
    """生成风险评估提示。
    
    Args:
        ticker: 股票代码
    """
    return f"""请对 {ticker} 进行全面风险评估：

1. **市场风险**：价格波动、市场情绪、流动性风险
2. **公司风险**：经营风险、财务风险、管理风险
3. **行业风险**：行业周期、竞争加剧、技术变革
4. **宏观风险**：经济周期、政策变化、利率风险
5. **特定风险**：公司特有风险因素

请使用以下工具：
- `technical_analysis` 分析市场风险
- `validate_analysis` 验证分析结果
- `get_company_info` 获取公司信息

最后，请给出风险等级评估和风险管理建议。"""
