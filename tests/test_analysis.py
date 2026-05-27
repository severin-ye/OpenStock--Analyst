"""analysis 模块集成测试"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from stock_analysis.analysis import (
    ResultValidator,
    TechnicalAnalyzer,
    InsiderAnalyzer,
    InstitutionalAnalyzer,
    EarningsAnalyzer,
    SectorAnalyzer,
    EconomicsAnalyzer,
    CompetitorAnalyzer,
)


def test_validator():
    """测试 Result Validator"""
    print("=" * 60)
    print("测试 Result Validator")
    print("=" * 60)

    validator = ResultValidator()

    # 模拟分析结果
    result = validator.validate_analysis(
        ticker="NVDA",
        signal="BULLISH",
        confidence="HIGH",
        f_score=7,
        composite_rank="#2/9",
        data_sources=["yfinance", "SEC EDGAR"],
        has_dcf=True,
        has_technical=True,
        has_fundamental=True,
        risk_count=5,
        bull_points=["ROIC 90%+", "AI 领先地位", "数据中心增长"],
        bear_points=["估值偏高", "竞争加剧"],
    )

    print(result.summary)
    print()


def test_technical():
    """测试 Technical Analyzer"""
    print("=" * 60)
    print("测试 Technical Analyzer")
    print("=" * 60)

    analyzer = TechnicalAnalyzer()

    # 分析 NVDA
    signal = analyzer.analyze("NVDA", period="1y")
    if signal:
        print(signal.summary)
        print()
        print(f"信号: {signal.signal}")
        print(f"置信度: {signal.confidence}")
        print(f"MTF 评分: {signal.mtf_score}/3")
    else:
        print("无法获取技术分析数据")
    print()


def test_insider():
    """测试 Insider Analyzer"""
    print("=" * 60)
    print("测试 Insider Analyzer")
    print("=" * 60)

    analyzer = InsiderAnalyzer()

    # 分析 NVDA
    signal = analyzer.analyze("NVDA")
    if signal:
        print(signal.summary)
        print()
        print(f"信号: {signal.signal}")
        print(f"置信度: {signal.confidence}")
        print(f"净情绪: {signal.net_sentiment:.2f}")
    else:
        print("无法获取内部人交易数据")
    print()


def test_institutional():
    """测试 Institutional Analyzer"""
    print("=" * 60)
    print("测试 Institutional Analyzer")
    print("=" * 60)

    analyzer = InstitutionalAnalyzer()

    # 分析 NVDA
    signal = analyzer.analyze("NVDA")
    if signal:
        print(signal.summary)
        print()
        print(f"信号: {signal.signal}")
        print(f"置信度: {signal.confidence}")
        print(f"机构持仓: {signal.institutional_ownership_pct:.1%}")
    else:
        print("无法获取机构持仓数据")
    print()


def test_earnings():
    """测试 Earnings Analyzer"""
    print("=" * 60)
    print("测试 Earnings Analyzer")
    print("=" * 60)

    analyzer = EarningsAnalyzer()

    # 分析 NVDA
    signal = analyzer.analyze("NVDA")
    if signal:
        print(signal.summary)
        print()
        print(f"信号: {signal.signal}")
        print(f"置信度: {signal.confidence}")
        print(f"管理层情绪: {signal.management_tone.value}")
    else:
        print("无法获取财报数据")
    print()


def test_sector():
    """测试 Sector Analyzer"""
    print("=" * 60)
    print("测试 Sector Analyzer")
    print("=" * 60)

    analyzer = SectorAnalyzer()

    # 分析 NVDA
    signal = analyzer.analyze("NVDA")
    if signal:
        print(signal.summary)
        print()
        print(f"信号: {signal.signal}")
        print(f"置信度: {signal.confidence}")
        print(f"行业分数: {signal.sector_score}/10")
    else:
        print("无法获取行业数据")
    print()


def test_economics():
    """测试 Economics Analyzer"""
    print("=" * 60)
    print("测试 Economics Analyzer")
    print("=" * 60)

    analyzer = EconomicsAnalyzer()

    # 分析宏观经济
    signal = analyzer.analyze()
    print(signal.summary)
    print()
    print(f"信号: {signal.signal}")
    print(f"置信度: {signal.confidence}")
    print(f"经济周期: {signal.phase.value}")
    print()


def test_competitor():
    """测试 Competitor Analyzer"""
    print("=" * 60)
    print("测试 Competitor Analyzer")
    print("=" * 60)

    analyzer = CompetitorAnalyzer()

    # 分析 NVDA
    signal = analyzer.analyze("NVDA")
    if signal:
        print(signal.summary)
        print()
        print(f"信号: {signal.signal}")
        print(f"置信度: {signal.confidence}")
        print(f"护城河: {signal.moat_width.value}")
    else:
        print("无法获取竞争数据")
    print()


def main():
    """运行所有测试"""
    print("InvestSkill 分析模块集成测试")
    print("=" * 60)
    print()

    # 测试各个模块
    test_validator()
    test_technical()
    test_insider()
    test_institutional()
    test_earnings()
    test_sector()
    test_economics()
    test_competitor()

    print("=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
