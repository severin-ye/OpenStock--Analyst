"""Competitor Analyzer — 基于 InvestSkill 的竞争分析框架

分析维度：
1. 护城河识别
2. Porter 五力分析
3. 竞争优势评估
4. 行业结构分析
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import yfinance as yf

logger = logging.getLogger(__name__)


class MoatWidth(str, Enum):
    WIDE = "WIDE"
    NARROW = "NARROW"
    NONE = "NONE"
    AT_RISK = "AT_RISK"


class MoatTrend(str, Enum):
    WIDENING = "WIDENING"
    STABLE = "STABLE"
    NARROWING = "NARROWING"


class ForceIntensity(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


@dataclass
class PorterFiveForces:
    """Porter 五力"""
    rivalry: ForceIntensity = ForceIntensity.MODERATE
    new_entrants: ForceIntensity = ForceIntensity.MODERATE
    supplier_power: ForceIntensity = ForceIntensity.MODERATE
    buyer_power: ForceIntensity = ForceIntensity.MODERATE
    substitutes: ForceIntensity = ForceIntensity.MODERATE


@dataclass
class CompetitorSignal:
    """竞争分析信号"""
    ticker: str
    sector: str
    moat_width: MoatWidth
    moat_trend: MoatTrend
    moat_sources: list[str]
    five_forces: PorterFiveForces
    competitive_advantages: list[str]
    competitive_risks: list[str]
    signal: str  # BULLISH / NEUTRAL / BEARISH
    confidence: str  # HIGH / MEDIUM / LOW
    summary: str
    roic_vs_wacc: Optional[float] = None


class CompetitorAnalyzer:
    """竞争分析器

    基于 InvestSkill 的 competitor-analysis 提示词，分析竞争优势和行业结构。
    """

    # 常见护城河来源
    MOAT_SOURCES = {
        "Network Effects": ["Visa", "Mastercard", "Meta", "Airbnb"],
        "Cost Advantages": ["Costco", "Amazon", "Walmart"],
        "Intangible Assets": ["Apple", "LVMH", "Coca-Cola", "Pfizer"],
        "Switching Costs": ["Oracle", "Salesforce", "Adobe", "Microsoft"],
        "Efficient Scale": ["Waste Management", "Union Pacific"],
    }

    def analyze(self, ticker: str) -> Optional[CompetitorSignal]:
        """分析竞争优势

        Args:
            ticker: 股票代码

        Returns:
            CompetitorSignal 或 None
        """
        try:
            # 获取股票信息
            stock_info = self._fetch_stock_info(ticker)
            if stock_info is None:
                logger.warning(f"无法获取 {ticker} 的信息")
                return None

            sector = stock_info.get("sector", "Unknown")
            company_name = stock_info.get("shortName", ticker)

            # 识别护城河
            moat_width, moat_trend, moat_sources = self._identify_moat(
                ticker=ticker,
                company_name=company_name,
                stock_info=stock_info,
            )

            # 分析五力
            five_forces = self._analyze_five_forces(sector, stock_info)

            # 识别竞争优势和风险
            advantages = self._identify_advantages(stock_info, moat_sources)
            risks = self._identify_risks(sector, five_forces)

            # 计算 ROIC vs WACC
            roic_vs_wacc = self._calculate_roic_wacc(stock_info)

            # 生成信号
            signal, confidence = self._generate_signal(
                moat_width=moat_width,
                moat_trend=moat_trend,
                five_forces=five_forces,
                roic_vs_wacc=roic_vs_wacc,
            )

            # 生成摘要
            summary = self._generate_summary(
                ticker=ticker,
                sector=sector,
                moat_width=moat_width,
                moat_trend=moat_trend,
                moat_sources=moat_sources,
                five_forces=five_forces,
                signal=signal,
            )

            return CompetitorSignal(
                ticker=ticker,
                sector=sector,
                moat_width=moat_width,
                moat_trend=moat_trend,
                moat_sources=moat_sources,
                five_forces=five_forces,
                competitive_advantages=advantages,
                competitive_risks=risks,
                roic_vs_wacc=roic_vs_wacc,
                signal=signal,
                confidence=confidence,
                summary=summary,
            )

        except Exception as e:
            logger.error(f"竞争分析失败 {ticker}: {e}")
            return None

    def _fetch_stock_info(self, ticker: str) -> Optional[dict]:
        """获取股票信息"""
        try:
            t = yf.Ticker(ticker)
            return t.info
        except Exception as e:
            logger.error(f"获取 {ticker} 信息失败: {e}")
            return None

    def _identify_moat(
        self,
        ticker: str,
        company_name: str,
        stock_info: dict,
    ) -> tuple[MoatWidth, MoatTrend, list[str]]:
        """识别护城河"""
        sources = []

        # 基于利润率判断
        profit_margin = stock_info.get("profitMargins", 0)
        gross_margin = stock_info.get("grossMargins", 0)
        roic = stock_info.get("returnOnCapital", 0)

        # 高利润率 = 可能有护城河
        if profit_margin and profit_margin > 0.2:
            sources.append("Intangible Assets")
        if gross_margin and gross_margin > 0.5:
            sources.append("Pricing Power")

        # 高 ROIC = 有竞争优势
        if roic and roic > 0.15:
            sources.append("Efficient Scale")

        # 确定护城河宽度
        if len(sources) >= 2 and profit_margin and profit_margin > 0.25:
            width = MoatWidth.WIDE
        elif len(sources) >= 1:
            width = MoatWidth.NARROW
        else:
            width = MoatWidth.NONE

        # 护城河趋势（简化版）
        revenue_growth = stock_info.get("revenueGrowth", 0)
        if revenue_growth and revenue_growth > 0.1:
            trend = MoatTrend.WIDENING
        elif revenue_growth and revenue_growth < 0:
            trend = MoatTrend.NARROWING
        else:
            trend = MoatTrend.STABLE

        return width, trend, sources

    def _analyze_five_forces(self, sector: str, stock_info: dict) -> PorterFiveForces:
        """分析五力"""
        # 简化版：基于行业特征
        forces = PorterFiveForces()

        # 行业竞争
        if sector in ["Technology", "Consumer Discretionary"]:
            forces.rivalry = ForceIntensity.HIGH
        elif sector in ["Utilities", "Consumer Staples"]:
            forces.rivalry = ForceIntensity.LOW

        # 新进入者威胁
        if sector in ["Technology", "Financials"]:
            forces.new_entrants = ForceIntensity.MODERATE
        elif sector in ["Utilities", "Healthcare"]:
            forces.new_entrants = ForceIntensity.LOW

        # 供应商议价能力
        if sector in ["Technology", "Consumer Discretionary"]:
            forces.supplier_power = ForceIntensity.MODERATE
        elif sector in ["Energy", "Materials"]:
            forces.supplier_power = ForceIntensity.HIGH

        # 买方议价能力
        if sector in ["Consumer Staples", "Consumer Discretionary"]:
            forces.buyer_power = ForceIntensity.HIGH
        elif sector in ["Technology", "Healthcare"]:
            forces.buyer_power = ForceIntensity.LOW

        # 替代品威胁
        if sector in ["Technology", "Consumer Discretionary"]:
            forces.substitutes = ForceIntensity.HIGH
        elif sector in ["Utilities", "Healthcare"]:
            forces.substitutes = ForceIntensity.LOW

        return forces

    def _identify_advantages(self, stock_info: dict, moat_sources: list[str]) -> list[str]:
        """识别竞争优势"""
        advantages = []

        # 基于护城河来源
        if "Network Effects" in moat_sources:
            advantages.append("网络效应")
        if "Cost Advantages" in moat_sources:
            advantages.append("成本优势")
        if "Intangible Assets" in moat_sources:
            advantages.append("品牌/专利")
        if "Switching Costs" in moat_sources:
            advantages.append("客户锁定")
        if "Efficient Scale" in moat_sources:
            advantages.append("规模效应")

        # 基于财务指标
        profit_margin = stock_info.get("profitMargins", 0)
        if profit_margin and profit_margin > 0.2:
            advantages.append("高利润率")

        revenue_growth = stock_info.get("revenueGrowth", 0)
        if revenue_growth and revenue_growth > 0.1:
            advantages.append("强劲增长")

        return advantages

    def _identify_risks(self, sector: str, five_forces: PorterFiveForces) -> list[str]:
        """识别竞争风险"""
        risks = []

        if five_forces.rivalry in [ForceIntensity.HIGH, ForceIntensity.EXTREME]:
            risks.append("激烈竞争")
        if five_forces.new_entrants in [ForceIntensity.HIGH, ForceIntensity.EXTREME]:
            risks.append("新进入者威胁")
        if five_forces.substitutes in [ForceIntensity.HIGH, ForceIntensity.EXTREME]:
            risks.append("替代品威胁")
        if five_forces.supplier_power in [ForceIntensity.HIGH, ForceIntensity.EXTREME]:
            risks.append("供应商议价能力强")
        if five_forces.buyer_power in [ForceIntensity.HIGH, ForceIntensity.EXTREME]:
            risks.append("买方议价能力强")

        return risks

    def _calculate_roic_wacc(self, stock_info: dict) -> Optional[float]:
        """计算 ROIC - WACC"""
        roic = stock_info.get("returnOnCapital")
        # WACC 简化为 10%
        wacc = 0.10

        if roic:
            return roic - wacc
        return None

    def _generate_signal(
        self,
        moat_width: MoatWidth,
        moat_trend: MoatTrend,
        five_forces: PorterFiveForces,
        roic_vs_wacc: Optional[float],
    ) -> tuple[str, str]:
        """生成信号"""
        # 基于护城河
        if moat_width == MoatWidth.WIDE:
            signal = "BULLISH"
            confidence = "HIGH"
        elif moat_width == MoatWidth.NARROW:
            signal = "BULLISH"
            confidence = "MEDIUM"
        elif moat_width == MoatWidth.AT_RISK:
            signal = "BEARISH"
            confidence = "MEDIUM"
        else:
            signal = "NEUTRAL"
            confidence = "MEDIUM"

        # 护城河趋势调整
        if moat_trend == MoatTrend.WIDENING:
            if signal == "BEARISH":
                signal = "NEUTRAL"
        elif moat_trend == MoatTrend.NARROWING:
            if signal == "BULLISH":
                confidence = "MEDIUM"

        # ROIC vs WACC 调整
        if roic_vs_wacc is not None:
            if roic_vs_wacc > 0.05:
                # ROIC 显著高于 WACC
                if signal == "BEARISH":
                    signal = "NEUTRAL"
            elif roic_vs_wacc < -0.05:
                # ROIC 显著低于 WACC
                if signal == "BULLISH":
                    confidence = "LOW"

        return signal, confidence

    def _generate_summary(
        self,
        ticker: str,
        sector: str,
        moat_width: MoatWidth,
        moat_trend: MoatTrend,
        moat_sources: list[str],
        five_forces: PorterFiveForces,
        signal: str,
    ) -> str:
        """生成摘要"""
        lines = [f"### {ticker} 竞争分析", ""]

        # 行业
        lines.append(f"**行业**: {sector}")
        lines.append("")

        # 护城河
        width_cn = {
            MoatWidth.WIDE: "宽",
            MoatWidth.NARROW: "窄",
            MoatWidth.NONE: "无",
            MoatWidth.AT_RISK: "风险中",
        }
        trend_cn = {
            MoatTrend.WIDENING: "加宽",
            MoatTrend.STABLE: "稳定",
            MoatTrend.NARROWING: "收窄",
        }
        lines.append("**护城河**:")
        lines.append(f"- 宽度: {width_cn.get(moat_width, '未知')}")
        lines.append(f"- 趋势: {trend_cn.get(moat_trend, '未知')}")
        if moat_sources:
            lines.append(f"- 来源: {', '.join(moat_sources)}")
        lines.append("")

        # 五力分析
        force_cn = {
            ForceIntensity.LOW: "低",
            ForceIntensity.MODERATE: "中",
            ForceIntensity.HIGH: "高",
            ForceIntensity.EXTREME: "极高",
        }
        lines.append("**Porter 五力**:")
        lines.append(f"- 行业竞争: {force_cn.get(five_forces.rivalry, '未知')}")
        lines.append(f"- 新进入者: {force_cn.get(five_forces.new_entrants, '未知')}")
        lines.append(f"- 供应商: {force_cn.get(five_forces.supplier_power, '未知')}")
        lines.append(f"- 买方: {force_cn.get(five_forces.buyer_power, '未知')}")
        lines.append(f"- 替代品: {force_cn.get(five_forces.substitutes, '未知')}")
        lines.append("")

        # 信号
        lines.append(f"**竞争信号**: {signal}")

        return "\n".join(lines)
