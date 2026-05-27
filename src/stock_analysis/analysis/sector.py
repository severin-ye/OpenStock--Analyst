"""Sector Analyzer — 基于 InvestSkill 的行业轮动分析框架

分析维度：
1. 行业表现
2. 经济周期定位
3. 基本面指标
4. 宏观驱动因素
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import yfinance as yf

logger = logging.getLogger(__name__)


class EconomicCycle(str, Enum):
    EARLY = "EARLY"
    MID = "MID"
    LATE = "LATE"
    RECESSION = "RECESSION"


class SectorMomentum(str, Enum):
    STRONG_UP = "STRONG UP"
    UP = "UP"
    NEUTRAL = "NEUTRAL"
    DOWN = "DOWN"
    STRONG_DOWN = "STRONG DOWN"


@dataclass
class SectorMetrics:
    """行业指标"""
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    ytd_return: Optional[float] = None
    momentum: SectorMomentum = SectorMomentum.NEUTRAL


@dataclass
class SectorSignal:
    """行业分析信号"""
    ticker: str
    sector: str
    industry: str
    cycle_phase: EconomicCycle
    metrics: SectorMetrics
    relative_strength: float  # vs SPX
    sector_score: int  # 1-10
    signal: str  # BULLISH / NEUTRAL / BEARISH
    confidence: str  # HIGH / MEDIUM / LOW
    summary: str


class SectorAnalyzer:
    """行业轮动分析器

    基于 InvestSkill 的 sector-analysis 提示词，分析行业轮动机会。
    """

    # S&P 500 行业 ETF 映射
    SECTOR_ETFS = {
        "Technology": "XLK",
        "Healthcare": "XLV",
        "Financials": "XLF",
        "Consumer Discretionary": "XLY",
        "Communication Services": "XLC",
        "Industrials": "XLI",
        "Consumer Staples": "XLP",
        "Energy": "XLE",
        "Utilities": "XLU",
        "Real Estate": "XLRE",
        "Materials": "XLB",
    }

    # 经济周期中的优势行业
    CYCLE_OUTPERFORMERS = {
        EconomicCycle.EARLY: ["Financials", "Technology", "Industrials"],
        EconomicCycle.MID: ["Industrials", "Materials", "Energy"],
        EconomicCycle.LATE: ["Energy", "Consumer Staples", "Healthcare"],
        EconomicCycle.RECESSION: ["Utilities", "Consumer Staples", "Healthcare"],
    }

    def analyze(self, ticker: str) -> Optional[SectorSignal]:
        """分析行业

        Args:
            ticker: 股票代码

        Returns:
            SectorSignal 或 None
        """
        try:
            # 获取股票信息
            stock_info = self._fetch_stock_info(ticker)
            if stock_info is None:
                logger.warning(f"无法获取 {ticker} 的信息")
                return None

            sector = stock_info.get("sector", "Unknown")
            industry = stock_info.get("industry", "Unknown")

            # 获取行业 ETF 数据
            sector_etf = self.SECTOR_ETFS.get(sector)
            metrics = self._analyze_sector_metrics(sector_etf)

            # 计算相对强度
            relative_strength = self._calculate_relative_strength(ticker, sector_etf)

            # 确定经济周期
            cycle = self._determine_cycle_phase()

            # 计算行业分数
            sector_score = self._calculate_sector_score(
                sector=sector,
                cycle=cycle,
                metrics=metrics,
                relative_strength=relative_strength,
            )

            # 生成信号
            signal, confidence = self._generate_signal(
                sector_score=sector_score,
                cycle=cycle,
                sector=sector,
                relative_strength=relative_strength,
            )

            # 生成摘要
            summary = self._generate_summary(
                ticker=ticker,
                sector=sector,
                industry=industry,
                cycle=cycle,
                metrics=metrics,
                sector_score=sector_score,
                signal=signal,
            )

            return SectorSignal(
                ticker=ticker,
                sector=sector,
                industry=industry,
                cycle_phase=cycle,
                metrics=metrics,
                relative_strength=relative_strength,
                sector_score=sector_score,
                signal=signal,
                confidence=confidence,
                summary=summary,
            )

        except Exception as e:
            logger.error(f"行业分析失败 {ticker}: {e}")
            return None

    def _fetch_stock_info(self, ticker: str) -> Optional[dict]:
        """获取股票信息"""
        try:
            t = yf.Ticker(ticker)
            return t.info
        except Exception as e:
            logger.error(f"获取 {ticker} 信息失败: {e}")
            return None

    def _analyze_sector_metrics(self, sector_etf: Optional[str]) -> SectorMetrics:
        """分析行业指标"""
        if sector_etf is None:
            return SectorMetrics()

        try:
            t = yf.Ticker(sector_etf)
            info = t.info
            hist = t.history(period="1y")

            # 计算 YTD 回报
            ytd_return = None
            if not hist.empty:
                start_price = hist["Close"].iloc[0]
                end_price = hist["Close"].iloc[-1]
                ytd_return = (end_price / start_price - 1) * 100

            # 计算动量
            momentum = SectorMomentum.NEUTRAL
            if ytd_return is not None:
                if ytd_return > 15:
                    momentum = SectorMomentum.STRONG_UP
                elif ytd_return > 5:
                    momentum = SectorMomentum.UP
                elif ytd_return < -15:
                    momentum = SectorMomentum.STRONG_DOWN
                elif ytd_return < -5:
                    momentum = SectorMomentum.DOWN

            return SectorMetrics(
                pe_ratio=info.get("trailingPE"),
                pb_ratio=info.get("priceToBook"),
                dividend_yield=info.get("dividendYield"),
                ytd_return=ytd_return,
                momentum=momentum,
            )

        except Exception as e:
            logger.warning(f"获取行业 ETF 数据失败: {e}")
            return SectorMetrics()

    def _calculate_relative_strength(self, ticker: str, sector_etf: Optional[str]) -> float:
        """计算相对强度 vs SPX"""
        try:
            # 获取股票和 SPY 数据
            stock = yf.Ticker(ticker)
            spy = yf.Ticker("SPY")

            stock_hist = stock.history(period="3mo")
            spy_hist = spy.history(period="3mo")

            if stock_hist.empty or spy_hist.empty:
                return 0.0

            # 计算 3 个月回报
            stock_return = (stock_hist["Close"].iloc[-1] / stock_hist["Close"].iloc[0] - 1)
            spy_return = (spy_hist["Close"].iloc[-1] / spy_hist["Close"].iloc[0] - 1)

            # 相对强度 = 股票回报 - SPY 回报
            return (stock_return - spy_return) * 100

        except Exception as e:
            logger.warning(f"计算相对强度失败: {e}")
            return 0.0

    def _determine_cycle_phase(self) -> EconomicCycle:
        """确定经济周期阶段

        简化版：基于市场表现推断
        """
        try:
            # 获取 SPY 数据
            spy = yf.Ticker("SPY")
            hist = spy.history(period="1y")

            if hist.empty:
                return EconomicCycle.MID

            # 计算 1 年回报
            return_1y = (hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1)

            # 简化判断
            if return_1y > 0.15:
                return EconomicCycle.EARLY
            elif return_1y > 0.05:
                return EconomicCycle.MID
            elif return_1y > -0.05:
                return EconomicCycle.LATE
            else:
                return EconomicCycle.RECESSION

        except Exception:
            return EconomicCycle.MID

    def _calculate_sector_score(
        self,
        sector: str,
        cycle: EconomicCycle,
        metrics: SectorMetrics,
        relative_strength: float,
    ) -> int:
        """计算行业分数 (1-10)"""
        score = 5  # 基础分

        # 经济周期匹配
        outperformers = self.CYCLE_OUTPERFORMERS.get(cycle, [])
        if sector in outperformers:
            score += 2
        else:
            score -= 1

        # 动量调整
        if metrics.momentum == SectorMomentum.STRONG_UP:
            score += 2
        elif metrics.momentum == SectorMomentum.UP:
            score += 1
        elif metrics.momentum == SectorMomentum.STRONG_DOWN:
            score -= 2
        elif metrics.momentum == SectorMomentum.DOWN:
            score -= 1

        # 相对强度调整
        if relative_strength > 5:
            score += 1
        elif relative_strength < -5:
            score -= 1

        # 估值调整
        if metrics.pe_ratio:
            if metrics.pe_ratio < 15:
                score += 1
            elif metrics.pe_ratio > 25:
                score -= 1

        return max(1, min(10, score))

    def _generate_signal(
        self,
        sector_score: int,
        cycle: EconomicCycle,
        sector: str,
        relative_strength: float,
    ) -> tuple[str, str]:
        """生成信号"""
        # 基于行业分数
        if sector_score >= 7:
            signal = "BULLISH"
            confidence = "HIGH"
        elif sector_score >= 5:
            signal = "BULLISH"
            confidence = "MEDIUM"
        elif sector_score >= 4:
            signal = "NEUTRAL"
            confidence = "MEDIUM"
        elif sector_score >= 3:
            signal = "BEARISH"
            confidence = "MEDIUM"
        else:
            signal = "BEARISH"
            confidence = "HIGH"

        # 周期匹配调整
        outperformers = self.CYCLE_OUTPERFORMERS.get(cycle, [])
        if sector in outperformers:
            if signal == "BEARISH":
                confidence = "MEDIUM"
        else:
            if signal == "BULLISH":
                confidence = "MEDIUM"

        return signal, confidence

    def _generate_summary(
        self,
        ticker: str,
        sector: str,
        industry: str,
        cycle: EconomicCycle,
        metrics: SectorMetrics,
        sector_score: int,
        signal: str,
    ) -> str:
        """生成摘要"""
        lines = [f"### {ticker} 行业分析", ""]

        # 行业信息
        lines.append("**行业信息**:")
        lines.append(f"- 行业: {sector}")
        lines.append(f"- 细分: {industry}")
        lines.append("")

        # 经济周期
        cycle_cn = {
            EconomicCycle.EARLY: "早期",
            EconomicCycle.MID: "中期",
            EconomicCycle.LATE: "晚期",
            EconomicCycle.RECESSION: "衰退",
        }
        lines.append("**经济周期**:")
        lines.append(f"- 当前阶段: {cycle_cn.get(cycle, '未知')}")
        lines.append(f"- 优势行业: {', '.join(self.CYCLE_OUTPERFORMERS.get(cycle, []))}")
        lines.append("")

        # 行业指标
        lines.append("**行业指标**:")
        if metrics.pe_ratio:
            lines.append(f"- P/E: {metrics.pe_ratio:.1f}")
        if metrics.ytd_return:
            lines.append(f"- YTD 回报: {metrics.ytd_return:+.1f}%")
        if metrics.momentum:
            lines.append(f"- 动量: {metrics.momentum.value}")
        lines.append("")

        # 行业分数
        lines.append("**行业评估**:")
        lines.append(f"- 行业分数: {sector_score}/10")
        lines.append(f"- 信号: {signal}")

        return "\n".join(lines)
