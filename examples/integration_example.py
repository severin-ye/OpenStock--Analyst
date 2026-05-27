"""集成分析模块到现有系统

展示如何将 InvestSkill 分析模块集成到股票分析流程中。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from stock_analysis.analysis import (
    ResultValidator,
    TechnicalAnalyzer,
    InsiderAnalyzer,
    InstitutionalAnalyzer,
)


def comprehensive_analysis(ticker: str) -> dict:
    """综合分析

    集成所有分析模块，生成综合报告。

    Args:
        ticker: 股票代码

    Returns:
        分析结果字典
    """
    results = {
        "ticker": ticker,
        "technical": None,
        "insider": None,
        "institutional": None,
        "validation": None,
    }

    # 1. 技术分析
    print(f"📊 技术分析 {ticker}...")
    tech = TechnicalAnalyzer()
    tech_signal = tech.analyze(ticker, period="1y")
    if tech_signal:
        results["technical"] = {
            "signal": tech_signal.signal,
            "confidence": tech_signal.confidence,
            "mtf_score": tech_signal.mtf_score,
            "trend": tech_signal.trend.value,
            "rsi": tech_signal.indicators.rsi,
        }
        print(f"   信号: {tech_signal.signal}, MTF: {tech_signal.mtf_score}/3")

    # 2. 内部人交易分析
    print(f"👥 内部人交易分析 {ticker}...")
    insider = InsiderAnalyzer()
    insider_signal = insider.analyze(ticker)
    if insider_signal:
        results["insider"] = {
            "signal": insider_signal.signal,
            "confidence": insider_signal.confidence,
            "net_sentiment": insider_signal.net_sentiment,
            "sentiment": insider_signal.sentiment.value,
        }
        print(f"   信号: {insider_signal.signal}, 情绪: {insider_signal.net_sentiment:.2f}")

    # 3. 机构持仓分析
    print(f"🏛️ 机构持仓分析 {ticker}...")
    inst = InstitutionalAnalyzer()
    inst_signal = inst.analyze(ticker)
    if inst_signal:
        results["institutional"] = {
            "signal": inst_signal.signal,
            "confidence": inst_signal.confidence,
            "ownership_pct": inst_signal.institutional_ownership_pct,
            "trend": inst_signal.trend.value,
        }
        print(f"   信号: {inst_signal.signal}, 持仓: {inst_signal.institutional_ownership_pct:.1%}")

    # 4. 综合验证
    print(f"✅ 综合验证 {ticker}...")
    validator = ResultValidator()

    # 确定综合信号
    signals = []
    if results["technical"]:
        signals.append(results["technical"]["signal"])
    if results["insider"]:
        signals.append(results["insider"]["signal"])
    if results["institutional"]:
        signals.append(results["institutional"]["signal"])

    # 投票决定综合信号
    if signals:
        bullish_count = signals.count("BULLISH")
        bearish_count = signals.count("BEARISH")

        if bullish_count > bearish_count:
            overall_signal = "BULLISH"
        elif bearish_count > bullish_count:
            overall_signal = "BEARISH"
        else:
            overall_signal = "NEUTRAL"
    else:
        overall_signal = "NEUTRAL"

    # 验证结果
    validation = validator.validate_analysis(
        ticker=ticker,
        signal=overall_signal,
        confidence="MEDIUM",
        has_technical=results["technical"] is not None,
        has_fundamental=True,
        risk_count=3,
    )

    results["validation"] = {
        "total_score": validation.total_score,
        "tier": validation.tier.value,
        "overall_signal": overall_signal,
    }

    print(f"   综合信号: {overall_signal}")
    print(f"   验证分数: {validation.total_score}/100 ({validation.tier.value})")

    return results


def main():
    """主函数"""
    print("=" * 60)
    print("InvestSkill 分析模块集成示例")
    print("=" * 60)
    print()

    # 分析 NVDA
    results = comprehensive_analysis("NVDA")

    print()
    print("=" * 60)
    print("分析结果汇总")
    print("=" * 60)

    # 技术分析
    if results["technical"]:
        tech = results["technical"]
        print(f"技术分析: {tech['signal']} (MTF: {tech['mtf_score']}/3, RSI: {tech['rsi']:.1f})")

    # 内部人交易
    if results["insider"]:
        insider = results["insider"]
        print(f"内部人交易: {insider['signal']} (情绪: {insider['net_sentiment']:.2f})")

    # 机构持仓
    if results["institutional"]:
        inst = results["institutional"]
        print(f"机构持仓: {inst['signal']} (持仓: {inst['ownership_pct']:.1%})")

    # 综合验证
    if results["validation"]:
        val = results["validation"]
        print(f"综合验证: {val['overall_signal']} ({val['total_score']}/100, {val['tier']})")


if __name__ == "__main__":
    main()
