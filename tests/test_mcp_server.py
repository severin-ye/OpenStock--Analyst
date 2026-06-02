"""
MCP 服务器测试

测试 MCP 服务器的工具、资源和提示功能。
"""

import pytest
import json
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestMCPServer:
    """MCP 服务器测试类。"""
    
    def test_server_import(self):
        """测试服务器导入。"""
        from stock_analysis.mcp.server import mcp
        assert mcp is not None
        assert mcp.name == "stock-analysis"
    
    def test_tools_import(self):
        """测试工具导入。"""
        from stock_analysis.mcp.tools import analysis, ranking, data, report
        assert analysis is not None
        assert ranking is not None
        assert data is not None
        assert report is not None
    
    def test_resources_import(self):
        """测试资源导入。"""
        from stock_analysis.mcp.resources import companies, prices, reports
        assert companies is not None
        assert prices is not None
        assert reports is not None
    
    def test_prompts_import(self):
        """测试提示导入。"""
        from stock_analysis.mcp.prompts import analysis, report
        assert analysis is not None
        assert report is not None


class TestMCPTools:
    """MCP 工具测试类。"""
    
    def test_analysis_tools_exist(self):
        """测试分析工具存在。"""
        from stock_analysis.mcp.tools.analysis import (
            technical_analysis,
            insider_analysis,
            institutional_analysis,
            earnings_analysis,
            sector_analysis,
            economics_analysis,
            competitor_analysis,
            narrative_analysis,
        )
        
        assert callable(technical_analysis)
        assert callable(insider_analysis)
        assert callable(institutional_analysis)
        assert callable(earnings_analysis)
        assert callable(sector_analysis)
        assert callable(economics_analysis)
        assert callable(competitor_analysis)
        assert callable(narrative_analysis)
    
    def test_data_tools_exist(self):
        """测试数据工具存在。"""
        from stock_analysis.mcp.tools.data import (
            get_price_summary,
            get_financial_summary,
            get_valuation_summary,
            calculate_ranking,
            compare_stocks,
            full_analysis,
        )
        
        assert callable(get_price_summary)
        assert callable(get_financial_summary)
        assert callable(get_valuation_summary)
        assert callable(calculate_ranking)
        assert callable(compare_stocks)
        assert callable(full_analysis)
    
    def test_ranking_tools_exist(self):
        """测试排名工具存在。"""
        from stock_analysis.mcp.tools.ranking import get_rankings
        
        assert callable(get_rankings)
    
    def test_report_tools_exist(self):
        """测试报告工具存在。"""
        from stock_analysis.mcp.tools.report import (
            generate_report,
            validate_analysis,
        )
        
        assert callable(generate_report)
        assert callable(validate_analysis)


class TestMCPResources:
    """MCP 资源测试类。"""
    
    def test_companies_resources_exist(self):
        """测试公司资源存在。"""
        from stock_analysis.mcp.resources.companies import (
            get_companies_list,
            get_company_info,
            get_companies_by_market,
            search_companies,
        )
        
        assert callable(get_companies_list)
        assert callable(get_company_info)
        assert callable(get_companies_by_market)
        assert callable(search_companies)
    
    def test_prices_resources_exist(self):
        """测试价格资源存在。"""
        from stock_analysis.mcp.resources.prices import (
            get_price_data,
            get_all_prices,
            get_prices_by_market,
        )
        
        assert callable(get_price_data)
        assert callable(get_all_prices)
        assert callable(get_prices_by_market)
    
    def test_reports_resources_exist(self):
        """测试报告资源存在。"""
        from stock_analysis.mcp.resources.reports import (
            get_reports_list,
            get_reports_by_ticker,
            get_report_content,
        )
        
        assert callable(get_reports_list)
        assert callable(get_reports_by_ticker)
        assert callable(get_report_content)


class TestMCPPrompts:
    """MCP 提示测试类。"""
    
    def test_analysis_prompts_exist(self):
        """测试分析提示存在。"""
        from stock_analysis.mcp.prompts.analysis import (
            stock_analysis_prompt,
            comparison_prompt,
            sector_analysis_prompt,
            risk_assessment_prompt,
        )
        
        assert callable(stock_analysis_prompt)
        assert callable(comparison_prompt)
        assert callable(sector_analysis_prompt)
        assert callable(risk_assessment_prompt)
    
    def test_report_prompts_exist(self):
        """测试报告提示存在。"""
        from stock_analysis.mcp.prompts.report import (
            report_generation_prompt,
            batch_report_prompt,
            report_update_prompt,
        )
        
        assert callable(report_generation_prompt)
        assert callable(batch_report_prompt)
        assert callable(report_update_prompt)


@pytest.mark.asyncio
class TestMCPToolsAsync:
    """MCP 异步工具测试类。"""
    
    async def test_calculate_ranking(self):
        """测试排名计算工具。"""
        from stock_analysis.mcp.tools.data import calculate_ranking
        
        # 测试计算排名
        result = await calculate_ranking("NVDA")
        result_data = json.loads(result)
        
        # 验证结果结构
        assert "ticker" in result_data or "error" in result_data
    
    async def test_get_rankings(self):
        """测试获取排名工具。"""
        from stock_analysis.mcp.tools.ranking import get_rankings
        
        # 测试获取排名
        result = await get_rankings(market="US", limit=5)
        result_data = json.loads(result)
        
        # 验证结果结构
        assert "market" in result_data or "error" in result_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
