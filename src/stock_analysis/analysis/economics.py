"""Economics Analyzer — 基于 InvestSkill 的宏观经济分析框架

分析维度：
1. 经济增长指标
2. 通胀指标
3. 货币政策
4. 市场情绪
5. 收益率曲线
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import yfinance as yf

logger = logging.getLogger(__name__)


class EconomicPhase(str, Enum):
    EXPANSION = "EXPANSION"
    PEAK = "PEAK"
    CONTRACTION = "CONTRACTION"
    TROUGH = "TROUGH"


class FedStance(str, Enum):
    HAWKISH = "HAWKISH"
    NEUTRAL = "NEUTRAL"
    DOVISH = "DOVISH"


class YieldCurveShape(str, Enum):
    NORMAL = "NORMAL"
    FLAT = "FLAT"
    INVERTED = "INVERTED"


@dataclass
class EconomicIndicators:
    """经济指标"""
    gdp_growth: Optional[float] = None
    unemployment_rate: Optional[float] = None
    inflation_rate: Optional[float] = None
    fed_rate: Optional[float] = None
    vix: Optional[float] = None
    yield_10y: Optional[float] = None
    yield_2y: Optional[float] = None


@dataclass
class EconomicSignal:
    """宏观经济信号"""
    phase: EconomicPhase
    fed_stance: FedStance
    yield_curve: YieldCurveShape
    indicators: EconomicIndicators
    market_impact: str  # Positive / Neutral / Negative
    sector_implications: dict[str, str]
    signal: str  # BULLISH / NEUTRAL / BEARISH
    confidence: str  # HIGH / MEDIUM / LOW
    summary: str


class EconomicsAnalyzer:
    """宏观经济分析器

    基于 InvestSkill 的 economics-analysis 提示词，分析宏观经济环境。
    """

    def analyze(self, ticker: Optional[str] = None) -> EconomicSignal:
        """分析宏观经济环境

        Args:
            ticker: 可选，用于分析特定股票的宏观敏感性

        Returns:
            EconomicSignal
        """
        try:
            # 获取经济指标
            indicators = self._fetch_economic_indicators()

            # 确定经济周期
            phase = self._determine_phase(indicators)

            # 分析美联储立场
            fed_stance = self._analyze_fed_stance(indicators)

            # 分析收益率曲线
            yield_curve = self._analyze_yield_curve(indicators)

            # 评估市场影响
            market_impact = self._assess_market_impact(phase, fed_stance, yield_curve)

            # 行业影响
            sector_implications = self._assess_sector_implications(phase, fed_stance)

            # 生成信号
            signal, confidence = self._generate_signal(
                phase=phase,
                fed_stance=fed_stance,
                yield_curve=yield_curve,
                indicators=indicators,
            )

            # 生成摘要
            summary = self._generate_summary(
                phase=phase,
                fed_stance=fed_stance,
                yield_curve=yield_curve,
                indicators=indicators,
                signal=signal,
            )

            return EconomicSignal(
                phase=phase,
                fed_stance=fed_stance,
                yield_curve=yield_curve,
                indicators=indicators,
                market_impact=market_impact,
                sector_implications=sector_implications,
                signal=signal,
                confidence=confidence,
                summary=summary,
            )

        except Exception as e:
            logger.error(f"宏观经济分析失败: {e}")
            # 返回默认值
            return EconomicSignal(
                phase=EconomicPhase.EXPANSION,
                fed_stance=FedStance.NEUTRAL,
                yield_curve=YieldCurveShape.NORMAL,
                indicators=EconomicIndicators(),
                market_impact="Neutral",
                sector_implications={},
                signal="NEUTRAL",
                confidence="LOW",
                summary="无法获取宏观经济数据",
            )

    def _fetch_economic_indicators(self) -> EconomicIndicators:
        """获取经济指标"""
        indicators = EconomicIndicators()

        try:
            # VIX
            vix = yf.Ticker("^VIX")
            vix_hist = vix.history(period="1d")
            if not vix_hist.empty:
                indicators.vix = float(vix_hist["Close"].iloc[-1])
        except Exception:
            pass

        try:
            # 10年期国债收益率
            tnx = yf.Ticker("^TNX")
            tnx_hist = tnx.history(period="1d")
            if not tnx_hist.empty:
                indicators.yield_10y = float(tnx_hist["Close"].iloc[-1])
        except Exception:
            pass

        try:
            # 2年期国债收益率
            irx = yf.Ticker("^IRX")
            irx_hist = irx.history(period="1d")
            if not irx_hist.empty:
                indicators.yield_2y = float(irx_hist["Close"].iloc[-1])
        except Exception:
            pass

        return indicators

    def _determine_phase(self, indicators: EconomicIndicators) -> EconomicPhase:
        """确定经济周期阶段

        简化版：基于市场指标推断
        """
        # 基于 VIX
        if indicators.vix:
            if indicators.vix > 30:
                return EconomicPhase.CONTRACTION
            elif indicators.vix > 20:
                return EconomicPhase.PEAK
            else:
                return EconomicPhase.EXPANSION

        return EconomicPhase.EXPANSION

    def _analyze_fed_stance(self, indicators: EconomicIndicators) -> FedStance:
        """分析美联储立场

        简化版：基于收益率曲线推断
        """
        if indicators.yield_10y and indicators.yield_2y:
            spread = indicators.yield_10y - indicators.yield_2y
            if spread < -0.5:
                return FedStance.HAWKISH  # 倒挂严重，紧缩政策
            elif spread > 0.5:
                return FedStance.DOVISH  # 正常曲线，宽松政策
            else:
                return FedStance.NEUTRAL

        return FedStance.NEUTRAL

    def _analyze_yield_curve(self, indicators: EconomicIndicators) -> YieldCurveShape:
        """分析收益率曲线"""
        if indicators.yield_10y and indicators.yield_2y:
            spread = indicators.yield_10y - indicators.yield_2y
            if spread < -0.2:
                return YieldCurveShape.INVERTED
            elif spread < 0.2:
                return YieldCurveShape.FLAT
            else:
                return YieldCurveShape.NORMAL

        return YieldCurveShape.NORMAL

    def _assess_market_impact(
        self,
        phase: EconomicPhase,
        fed_stance: FedStance,
        yield_curve: YieldCurveShape,
    ) -> str:
        """评估市场影响"""
        # 经济周期影响
        if phase == EconomicPhase.EXPANSION:
            cycle_impact = "Positive"
        elif phase == EconomicPhase.PEAK:
            cycle_impact = "Neutral"
        elif phase == EconomicPhase.CONTRACTION:
            cycle_impact = "Negative"
        else:
            cycle_impact = "Neutral"

        # 美联储影响
        if fed_stance == FedStance.DOVISH:
            fed_impact = "Positive"
        elif fed_stance == FedStance.HAWKISH:
            fed_impact = "Negative"
        else:
            fed_impact = "Neutral"

        # 综合评估
        if cycle_impact == "Positive" and fed_impact == "Positive":
            return "Positive"
        elif cycle_impact == "Negative" and fed_impact == "Negative":
            return "Negative"
        else:
            return "Neutral"

    def _assess_sector_implications(
        self,
        phase: EconomicPhase,
        fed_stance: FedStance,
    ) -> dict[str, str]:
        """评估行业影响"""
        implications = {}

        # 基于经济周期
        if phase == EconomicPhase.EXPANSION:
            implications["Technology"] = "Positive"
            implications["Consumer Discretionary"] = "Positive"
            implications["Industrials"] = "Positive"
            implications["Utilities"] = "Neutral"
        elif phase == EconomicPhase.CONTRACTION:
            implications["Utilities"] = "Positive"
            implications["Consumer Staples"] = "Positive"
            implications["Healthcare"] = "Positive"
            implications["Technology"] = "Negative"

        # 基于美联储立场
        if fed_stance == FedStance.HAWKISH:
            implications["Financials"] = "Positive"
            implications["Real Estate"] = "Negative"
            implications["Growth Stocks"] = "Negative"
        elif fed_stance == FedStance.DOVISH:
            implications["Growth Stocks"] = "Positive"
            implications["Real Estate"] = "Positive"

        return implications

    def _generate_signal(
        self,
        phase: EconomicPhase,
        fed_stance: FedStance,
        yield_curve: YieldCurveShape,
        indicators: EconomicIndicators,
    ) -> tuple[str, str]:
        """生成信号"""
        # 经济周期信号
        if phase == EconomicPhase.EXPANSION:
            signal = "BULLISH"
            confidence = "MEDIUM"
        elif phase == EconomicPhase.PEAK:
            signal = "NEUTRAL"
            confidence = "MEDIUM"
        elif phase == EconomicPhase.CONTRACTION:
            signal = "BEARISH"
            confidence = "MEDIUM"
        else:
            signal = "NEUTRAL"
            confidence = "LOW"

        # 收益率曲线调整
        if yield_curve == YieldCurveShape.INVERTED:
            # 倒挂是衰退信号
            if signal == "BULLISH":
                signal = "NEUTRAL"
                confidence = "MEDIUM"
        elif yield_curve == YieldCurveShape.NORMAL:
            # 正常曲线是健康信号
            if signal == "BEARISH":
                confidence = "LOW"

        # VIX 调整
        if indicators.vix:
            if indicators.vix > 30:
                # 高波动率，市场恐慌
                if signal == "BULLISH":
                    signal = "NEUTRAL"
            elif indicators.vix < 15:
                # 低波动率，市场平静
                if signal == "BEARISH":
                    confidence = "LOW"

        return signal, confidence

    def _generate_summary(
        self,
        phase: EconomicPhase,
        fed_stance: FedStance,
        yield_curve: YieldCurveShape,
        indicators: EconomicIndicators,
        signal: str,
    ) -> str:
        """生成摘要"""
        lines = ["### 宏观经济分析", ""]

        # 经济周期
        phase_cn = {
            EconomicPhase.EXPANSION: "扩张",
            EconomicPhase.PEAK: "顶峰",
            EconomicPhase.CONTRACTION: "收缩",
            EconomicPhase.TROUGH: "谷底",
        }
        lines.append("**经济周期**:")
        lines.append(f"- 当前阶段: {phase_cn.get(phase, '未知')}")
        lines.append("")

        # 美联储立场
        fed_cn = {
            FedStance.HAWKISH: "鹰派",
            FedStance.NEUTRAL: "中性",
            FedStance.DOVISH: "鸽派",
        }
        lines.append("**货币政策**:")
        lines.append(f"- 美联储立场: {fed_cn.get(fed_stance, '未知')}")
        lines.append("")

        # 收益率曲线
        curve_cn = {
            YieldCurveShape.NORMAL: "正常",
            YieldCurveShape.FLAT: "平坦",
            YieldCurveShape.INVERTED: "倒挂",
        }
        lines.append("**收益率曲线**:")
        lines.append(f"- 形态: {curve_cn.get(yield_curve, '未知')}")
        if indicators.yield_10y:
            lines.append(f"- 10年期收益率: {indicators.yield_10y:.2f}%")
        if indicators.yield_2y:
            lines.append(f"- 2年期收益率: {indicators.yield_2y:.2f}%")
        lines.append("")

        # 市场情绪
        if indicators.vix:
            lines.append("**市场情绪**:")
            lines.append(f"- VIX: {indicators.vix:.1f}")
            if indicators.vix > 25:
                lines.append("- 状态: 恐慌")
            elif indicators.vix > 20:
                lines.append("- 状态: 谨慎")
            else:
                lines.append("- 状态: 平静")
            lines.append("")

        # 信号
        lines.append(f"**宏观信号**: {signal}")

        return "\n".join(lines)
