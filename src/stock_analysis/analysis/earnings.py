"""Earnings Analyzer — 基于 InvestSkill 的财报电话会议分析框架

分析维度：
1. 管理层情绪分析
2. 关键主题提取
3. 指引变化分析
4. Q&A 会话分析
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import yfinance as yf

logger = logging.getLogger(__name__)


class ManagementTone(str, Enum):
    CONFIDENT = "CONFIDENT"
    NEUTRAL = "NEUTRAL"
    CAUTIOUS = "CAUTIOUS"
    DEFENSIVE = "DEFENSIVE"


class GuidanceChange(str, Enum):
    RAISED = "RAISED"
    MAINTAINED = "MAINTAINED"
    LOWERED = "LOWERED"
    WITHDRAWN = "WITHDRAWN"


@dataclass
class KeyTheme:
    """关键主题"""
    category: str  # Strategic / Operational / Market / Capital
    theme: str
    sentiment: str  # Positive / Neutral / Negative


@dataclass
class EarningsSignal:
    """财报电话会议信号"""
    ticker: str
    quarter: str
    management_tone: ManagementTone
    guidance_change: GuidanceChange
    key_themes: list[KeyTheme]
    confidence_indicators: list[str]
    caution_indicators: list[str]
    red_flags: list[str]
    signal: str  # BULLISH / NEUTRAL / BEARISH
    confidence: str  # HIGH / MEDIUM / LOW
    summary: str


class EarningsAnalyzer:
    """财报电话会议分析器

    基于 InvestSkill 的 earnings-call-analysis 提示词，分析管理层情绪和指引。
    """

    def analyze(self, ticker: str) -> Optional[EarningsSignal]:
        """分析财报电话会议

        Args:
            ticker: 股票代码

        Returns:
            EarningsSignal 或 None
        """
        try:
            # 获取财报数据
            earnings_data = self._fetch_earnings_data(ticker)
            if earnings_data is None:
                logger.warning(f"无法获取 {ticker} 的财报数据")
                return None

            # 分析管理层情绪
            tone = self._analyze_tone(earnings_data)

            # 分析指引变化
            guidance = self._analyze_guidance(earnings_data)

            # 提取关键主题
            themes = self._extract_themes(earnings_data)

            # 识别指标
            confidence_indicators = self._identify_confidence_indicators(earnings_data)
            caution_indicators = self._identify_caution_indicators(earnings_data)
            red_flags = self._identify_red_flags(earnings_data)

            # 生成信号
            signal, confidence_level = self._generate_signal(
                tone=tone,
                guidance=guidance,
                themes=themes,
                red_flags=red_flags,
            )

            # 生成摘要
            summary = self._generate_summary(
                ticker=ticker,
                tone=tone,
                guidance=guidance,
                themes=themes,
                signal=signal,
            )

            # 获取季度信息
            quarter = self._get_quarter_info(earnings_data)

            return EarningsSignal(
                ticker=ticker,
                quarter=quarter,
                management_tone=tone,
                guidance_change=guidance,
                key_themes=themes,
                confidence_indicators=confidence_indicators,
                caution_indicators=caution_indicators,
                red_flags=red_flags,
                signal=signal,
                confidence=confidence_level,
                summary=summary,
            )

        except Exception as e:
            logger.error(f"财报分析失败 {ticker}: {e}")
            return None

    def _fetch_earnings_data(self, ticker: str) -> Optional[dict]:
        """获取财报数据"""
        try:
            t = yf.Ticker(ticker)

            # 获取财报信息
            info = t.info
            earnings_dates = t.earnings_dates
            earnings_history = t.earnings_history

            return {
                "info": info,
                "earnings_dates": earnings_dates,
                "earnings_history": earnings_history,
            }
        except Exception as e:
            logger.error(f"获取 {ticker} 财报数据失败: {e}")
            return None

    def _analyze_tone(self, earnings_data: dict) -> ManagementTone:
        """分析管理层情绪

        简化版：基于财报表现推断情绪
        """
        info = earnings_data.get("info", {})

        # 获取盈利增长
        earnings_growth = info.get("earningsGrowth")
        revenue_growth = info.get("revenueGrowth")

        if earnings_growth and revenue_growth:
            if earnings_growth > 0.2 and revenue_growth > 0.1:
                return ManagementTone.CONFIDENT
            elif earnings_growth > 0 and revenue_growth > 0:
                return ManagementTone.NEUTRAL
            elif earnings_growth < -0.1 or revenue_growth < -0.05:
                return ManagementTone.CAUTIOUS
            else:
                return ManagementTone.NEUTRAL

        return ManagementTone.NEUTRAL

    def _analyze_guidance(self, earnings_data: dict) -> GuidanceChange:
        """分析指引变化

        简化版：基于盈利惊喜推断指引
        """
        earnings_history = earnings_data.get("earnings_history")

        if earnings_history is not None and not earnings_history.empty:
            try:
                # 获取最近的盈利惊喜
                surprise_pct = earnings_history.get("surprisePercent")
                if surprise_pct is not None and len(surprise_pct) > 0:
                    latest_surprise = float(surprise_pct.iloc[-1])
                    if latest_surprise > 0.05:
                        return GuidanceChange.RAISED
                    elif latest_surprise < -0.05:
                        return GuidanceChange.LOWERED
                    else:
                        return GuidanceChange.MAINTAINED
            except Exception:
                pass

        return GuidanceChange.MAINTAINED

    def _extract_themes(self, earnings_data: dict) -> list[KeyTheme]:
        """提取关键主题

        简化版：基于业务描述推断主题
        """
        themes = []
        info = earnings_data.get("info", {})

        # 业务描述
        business_summary = info.get("longBusinessSummary", "")
        industry = info.get("industry", "")

        # 战略主题
        if "AI" in business_summary or "artificial intelligence" in business_summary.lower():
            themes.append(KeyTheme(
                category="Strategic",
                theme="AI/人工智能战略",
                sentiment="Positive",
            ))

        if "cloud" in business_summary.lower():
            themes.append(KeyTheme(
                category="Strategic",
                theme="云计算业务",
                sentiment="Positive",
            ))

        # 运营业务
        revenue_growth = info.get("revenueGrowth")
        if revenue_growth:
            if revenue_growth > 0.1:
                themes.append(KeyTheme(
                    category="Operational",
                    theme="强劲营收增长",
                    sentiment="Positive",
                ))
            elif revenue_growth < 0:
                themes.append(KeyTheme(
                    category="Operational",
                    theme="营收下滑",
                    sentiment="Negative",
                ))

        # 行业主题
        if industry:
            themes.append(KeyTheme(
                category="Market",
                theme=f"行业: {industry}",
                sentiment="Neutral",
            ))

        return themes

    def _identify_confidence_indicators(self, earnings_data: dict) -> list[str]:
        """识别信心指标"""
        indicators = []
        info = earnings_data.get("info", {})

        # 盈利增长
        earnings_growth = info.get("earningsGrowth")
        if earnings_growth and earnings_growth > 0.1:
            indicators.append(f"盈利增长 {earnings_growth:.1%}")

        # 营收增长
        revenue_growth = info.get("revenueGrowth")
        if revenue_growth and revenue_growth > 0.1:
            indicators.append(f"营收增长 {revenue_growth:.1%}")

        # 利润率
        profit_margin = info.get("profitMargins")
        if profit_margin and profit_margin > 0.15:
            indicators.append(f"高利润率 {profit_margin:.1%}")

        return indicators

    def _identify_caution_indicators(self, earnings_data: dict) -> list[str]:
        """识别谨慎指标"""
        indicators = []
        info = earnings_data.get("info", {})

        # 盈利下滑
        earnings_growth = info.get("earningsGrowth")
        if earnings_growth and earnings_growth < -0.1:
            indicators.append(f"盈利下滑 {earnings_growth:.1%}")

        # 营收下滑
        revenue_growth = info.get("revenueGrowth")
        if revenue_growth and revenue_growth < -0.05:
            indicators.append(f"营收下滑 {revenue_growth:.1%}")

        # 高负债
        debt_to_equity = info.get("debtToEquity")
        if debt_to_equity and debt_to_equity > 100:
            indicators.append(f"高负债率 {debt_to_equity:.0f}%")

        return indicators

    def _identify_red_flags(self, earnings_data: dict) -> list[str]:
        """识别红旗"""
        flags = []
        info = earnings_data.get("info", {})

        # 盈利大幅下滑
        earnings_growth = info.get("earningsGrowth")
        if earnings_growth and earnings_growth < -0.3:
            flags.append("盈利大幅下滑")

        # 营收大幅下滑
        revenue_growth = info.get("revenueGrowth")
        if revenue_growth and revenue_growth < -0.15:
            flags.append("营收大幅下滑")

        # 负面利润
        profit_margin = info.get("profitMargins")
        if profit_margin and profit_margin < 0:
            flags.append("亏损状态")

        return flags

    def _generate_signal(
        self,
        tone: ManagementTone,
        guidance: GuidanceChange,
        themes: list[KeyTheme],
        red_flags: list[str],
    ) -> tuple[str, str]:
        """生成信号"""
        # 基于管理层情绪
        if tone == ManagementTone.CONFIDENT:
            if guidance == GuidanceChange.RAISED:
                signal = "BULLISH"
                confidence = "HIGH"
            else:
                signal = "BULLISH"
                confidence = "MEDIUM"
        elif tone == ManagementTone.CAUTIOUS:
            if guidance == GuidanceChange.LOWERED:
                signal = "BEARISH"
                confidence = "HIGH"
            else:
                signal = "BEARISH"
                confidence = "MEDIUM"
        elif tone == ManagementTone.DEFENSIVE:
            signal = "BEARISH"
            confidence = "HIGH"
        else:
            signal = "NEUTRAL"
            confidence = "MEDIUM"

        # 红旗调整
        if red_flags:
            if signal == "BULLISH":
                confidence = "MEDIUM"
            elif signal == "NEUTRAL":
                signal = "BEARISH"
                confidence = "MEDIUM"

        # 主题调整
        positive_themes = sum(1 for t in themes if t.sentiment == "Positive")
        negative_themes = sum(1 for t in themes if t.sentiment == "Negative")

        if negative_themes > positive_themes:
            if signal == "BULLISH":
                confidence = "LOW"

        return signal, confidence

    def _get_quarter_info(self, earnings_data: dict) -> str:
        """获取季度信息"""

        # 尝试获取最近财报日期
        earnings_dates = earnings_data.get("earnings_dates")
        if earnings_dates is not None and not earnings_dates.empty:
            try:
                latest_date = earnings_dates.index[-1]
                return f"Q{latest_date.quarter} {latest_date.year}"
            except Exception:
                pass

        return "最近季度"

    def _generate_summary(
        self,
        ticker: str,
        tone: ManagementTone,
        guidance: GuidanceChange,
        themes: list[KeyTheme],
        signal: str,
    ) -> str:
        """生成摘要"""
        lines = [f"### {ticker} 财报分析", ""]

        # 管理层情绪
        tone_cn = {
            ManagementTone.CONFIDENT: "自信",
            ManagementTone.NEUTRAL: "中性",
            ManagementTone.CAUTIOUS: "谨慎",
            ManagementTone.DEFENSIVE: "防御",
        }
        lines.append("**管理层情绪**:")
        lines.append(f"- 情绪: {tone_cn.get(tone, '未知')}")
        lines.append("")

        # 指引变化
        guidance_cn = {
            GuidanceChange.RAISED: "上调",
            GuidanceChange.MAINTAINED: "维持",
            GuidanceChange.LOWERED: "下调",
            GuidanceChange.WITHDRAWN: "撤回",
        }
        lines.append("**指引变化**:")
        lines.append(f"- 变化: {guidance_cn.get(guidance, '未知')}")
        lines.append("")

        # 关键主题
        if themes:
            lines.append("**关键主题**:")
            for theme in themes[:5]:
                lines.append(f"- [{theme.category}] {theme.theme} ({theme.sentiment})")
            lines.append("")

        # 信号
        lines.append(f"**财报信号**: {signal}")

        return "\n".join(lines)
