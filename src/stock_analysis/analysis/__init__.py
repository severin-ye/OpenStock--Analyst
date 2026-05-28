"""InvestSkill 分析模块集成

集成 InvestSkill 的专业分析框架到股市分析系统：
- ResultValidator: 五维验证框架
- TechnicalAnalyzer: 技术分析
- InsiderAnalyzer: 内部人交易分析
- InstitutionalAnalyzer: 机构持仓分析
- EarningsAnalyzer: 财报电话会议分析
- SectorAnalyzer: 行业轮动分析
- EconomicsAnalyzer: 宏观经济分析
- CompetitorAnalyzer: 竞争分析
"""

from stock_analysis.analysis.competitor import CompetitorAnalyzer, CompetitorSignal
from stock_analysis.analysis.earnings import EarningsAnalyzer, EarningsSignal
from stock_analysis.analysis.economics import EconomicsAnalyzer, EconomicSignal
from stock_analysis.analysis.insider import InsiderAnalyzer, InsiderSignal
from stock_analysis.analysis.institutional import InstitutionalAnalyzer, InstitutionalSignal
from stock_analysis.analysis.narrative import NarrativeAnalyzer, NarrativeSignal
from stock_analysis.analysis.sector import SectorAnalyzer, SectorSignal
from stock_analysis.analysis.technical import TechnicalAnalyzer, TechnicalSignal
from stock_analysis.analysis.validator import ResultValidator, ValidationResult

__all__ = [
    # 验证框架
    "ResultValidator",
    "ValidationResult",
    # 分析器
    "TechnicalAnalyzer",
    "TechnicalSignal",
    "InsiderAnalyzer",
    "InsiderSignal",
    "InstitutionalAnalyzer",
    "InstitutionalSignal",
    "EarningsAnalyzer",
    "EarningsSignal",
    "SectorAnalyzer",
    "SectorSignal",
    "EconomicsAnalyzer",
    "EconomicSignal",
    "CompetitorAnalyzer",
    "CompetitorSignal",
    "NarrativeAnalyzer",
    "NarrativeSignal",
]
