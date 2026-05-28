"""Technical Analyzer — 基于 InvestSkill 的技术分析框架

分析维度：
1. 趋势识别：主趋势、支撑/阻力
2. 技术指标：MA、RSI、MACD
3. 多时间框架分析（MTF）
4. 成交量分析
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class TrendDirection(str, Enum):
    UPTREND = "UPTREND"
    DOWNTREND = "DOWNTREND"
    SIDEWAYS = "SIDEWAYS"


class MTFAlignment(str, Enum):
    STRONG_BULL = "3/3 Bullish"
    MODERATE_BULL = "2/3 Bullish"
    NEUTRAL = "1/3 Aligned"
    MODERATE_BEAR = "2/3 Bearish"
    STRONG_BEAR = "3/3 Bearish"


@dataclass
class TechnicalIndicators:
    """技术指标"""
    ma20: Optional[float] = None
    ma50: Optional[float] = None
    ma200: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    atr: Optional[float] = None


@dataclass
class PriceLevels:
    """价格水平"""
    support: list[float] = field(default_factory=list)
    resistance: list[float] = field(default_factory=list)
    pivot: Optional[float] = None


@dataclass
class TechnicalSignal:
    """技术分析信号"""
    ticker: str
    current_price: float
    trend: TrendDirection
    mtf_alignment: MTFAlignment
    mtf_score: int  # 0-3
    indicators: TechnicalIndicators
    levels: PriceLevels
    signal: str  # BULLISH / NEUTRAL / BEARISH
    confidence: str  # HIGH / MEDIUM / LOW
    summary: str

    @property
    def signal_strength(self) -> str:
        if self.mtf_score >= 3:
            return "STRONG"
        elif self.mtf_score >= 2:
            return "MODERATE"
        else:
            return "WEAK"


class TechnicalAnalyzer:
    """技术分析器

    基于 InvestSkill 的 technical-analysis 提示词，进行多时间框架技术分析。
    """

    def analyze(self, ticker: str, period: str = "1y") -> Optional[TechnicalSignal]:
        """进行技术分析

        Args:
            ticker: 股票代码
            period: 数据周期 (1mo, 3mo, 6mo, 1y, 2y, 5y)

        Returns:
            TechnicalSignal 或 None
        """
        try:
            # 获取价格数据
            data = self._fetch_data(ticker, period)
            if data is None or data.empty:
                logger.warning(f"无法获取 {ticker} 的价格数据")
                return None

            # 计算技术指标
            indicators = self._calculate_indicators(data)

            # 识别趋势
            trend = self._identify_trend(data, indicators)

            # 计算支撑/阻力
            levels = self._calculate_levels(data)

            # 多时间框架分析
            mtf_score, mtf_alignment = self._mtf_analysis(ticker, data, indicators)

            # 生成信号
            signal, confidence = self._generate_signal(
                trend=trend,
                mtf_score=mtf_score,
                indicators=indicators,
                current_price=data["Close"].iloc[-1],
            )

            # 生成摘要
            summary = self._generate_summary(
                ticker=ticker,
                trend=trend,
                mtf_score=mtf_score,
                indicators=indicators,
                signal=signal,
            )

            return TechnicalSignal(
                ticker=ticker,
                current_price=float(data["Close"].iloc[-1]),
                trend=trend,
                mtf_alignment=mtf_alignment,
                mtf_score=mtf_score,
                indicators=indicators,
                levels=levels,
                signal=signal,
                confidence=confidence,
                summary=summary,
            )

        except Exception as e:
            logger.error(f"技术分析失败 {ticker}: {e}")
            return None

    def _fetch_data(self, ticker: str, period: str) -> Optional[pd.DataFrame]:
        """获取价格数据"""
        try:
            t = yf.Ticker(ticker)
            data = t.history(period=period, auto_adjust=True)
            return data if not data.empty else None
        except Exception as e:
            logger.error(f"获取 {ticker} 数据失败: {e}")
            return None

    def _calculate_indicators(self, data: pd.DataFrame) -> TechnicalIndicators:
        """计算技术指标"""
        close = data["Close"]

        # 移动平均线
        ma20 = float(close.rolling(window=20).mean().iloc[-1]) if len(close) >= 20 else None
        ma50 = float(close.rolling(window=50).mean().iloc[-1]) if len(close) >= 50 else None
        ma200 = float(close.rolling(window=200).mean().iloc[-1]) if len(close) >= 200 else None

        # RSI
        rsi = self._calculate_rsi(close, period=14)

        # MACD
        macd, macd_signal, macd_hist = self._calculate_macd(close)

        # ATR
        atr = self._calculate_atr(data, period=14)

        return TechnicalIndicators(
            ma20=ma20,
            ma50=ma50,
            ma200=ma200,
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
            macd_hist=macd_hist,
            atr=atr,
        )

    def _calculate_rsi(self, close: pd.Series, period: int = 14) -> Optional[float]:
        """计算 RSI"""
        try:
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1])
        except Exception:
            return None

    def _calculate_macd(self, close: pd.Series) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """计算 MACD"""
        try:
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            macd_signal = macd.ewm(span=9, adjust=False).mean()
            macd_hist = macd - macd_signal
            return float(macd.iloc[-1]), float(macd_signal.iloc[-1]), float(macd_hist.iloc[-1])
        except Exception:
            return None, None, None

    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> Optional[float]:
        """计算 ATR"""
        try:
            high = data["High"]
            low = data["Low"]
            close = data["Close"]

            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()
            return float(atr.iloc[-1])
        except Exception:
            return None

    def _identify_trend(self, data: pd.DataFrame, indicators: TechnicalIndicators) -> TrendDirection:
        """识别趋势"""
        close = data["Close"]
        current_price = float(close.iloc[-1])

        # 使用 MA 判断趋势
        if indicators.ma50 and indicators.ma200:
            if current_price > indicators.ma50 > indicators.ma200:
                return TrendDirection.UPTREND
            elif current_price < indicators.ma50 < indicators.ma200:
                return TrendDirection.DOWNTREND
            else:
                return TrendDirection.SIDEWAYS
        elif indicators.ma50:
            if current_price > indicators.ma50:
                return TrendDirection.UPTREND
            else:
                return TrendDirection.DOWNTREND
        else:
            # 使用简单方法
            if len(close) >= 20:
                recent_avg = float(close.tail(20).mean())
                if current_price > recent_avg * 1.02:
                    return TrendDirection.UPTREND
                elif current_price < recent_avg * 0.98:
                    return TrendDirection.DOWNTREND
            return TrendDirection.SIDEWAYS

    def _calculate_levels(self, data: pd.DataFrame) -> PriceLevels:
        """计算支撑/阻力水平"""
        close = data["Close"]
        high = data["High"]
        low = data["Low"]

        # 简化版：使用近期高低点
        recent_high = float(high.tail(20).max())
        recent_low = float(low.tail(20).min())
        current = float(close.iloc[-1])

        # 计算枢轴点
        pivot = (recent_high + recent_low + current) / 3

        # 支撑位
        s1 = 2 * pivot - recent_high
        s2 = pivot - (recent_high - recent_low)

        # 阻力位
        r1 = 2 * pivot - recent_low
        r2 = pivot + (recent_high - recent_low)

        return PriceLevels(
            support=[round(s1, 2), round(s2, 2)],
            resistance=[round(r1, 2), round(r2, 2)],
            pivot=round(pivot, 2),
        )

    def _mtf_analysis(
        self,
        ticker: str,
        data: pd.DataFrame,
        indicators: TechnicalIndicators,
    ) -> tuple[int, MTFAlignment]:
        """多时间框架分析

        简化版：基于当前数据的趋势强度评分
        """
        score = 0
        close = data["Close"]
        current_price = float(close.iloc[-1])

        # 短期趋势（MA20）
        if indicators.ma20:
            if current_price > indicators.ma20:
                score += 1

        # 中期趋势（MA50）
        if indicators.ma50:
            if current_price > indicators.ma50:
                score += 1

        # MTF 评分（基于 RSI 补充）
        if indicators.rsi is not None and indicators.rsi > 50:
            score += 1

        # 确定对齐状态
        if score == 3:
            alignment = MTFAlignment.STRONG_BULL
        elif score == 2:
            alignment = MTFAlignment.MODERATE_BULL
        elif score == 1:
            alignment = MTFAlignment.NEUTRAL
        elif score == 0:
            alignment = MTFAlignment.STRONG_BEAR
        else:
            alignment = MTFAlignment.NEUTRAL

        return score, alignment

    def _generate_signal(
        self,
        trend: TrendDirection,
        mtf_score: int,
        indicators: TechnicalIndicators,
        current_price: float,
    ) -> tuple[str, str]:
        """生成信号"""
        # 基于 MTF 评分
        if mtf_score >= 3:
            signal = "BULLISH"
            confidence = "HIGH"
        elif mtf_score >= 2:
            signal = "BULLISH"
            confidence = "MEDIUM"
        elif mtf_score <= 0:
            signal = "BEARISH"
            confidence = "HIGH"
        elif mtf_score <= 1:
            signal = "BEARISH"
            confidence = "MEDIUM"
        else:
            signal = "NEUTRAL"
            confidence = "MEDIUM"

        # RSI 调整
        if indicators.rsi:
            if indicators.rsi > 70:
                # 超买
                if signal == "BULLISH":
                    confidence = "MEDIUM"  # 降低置信度
            elif indicators.rsi < 30:
                # 超卖
                if signal == "BEARISH":
                    confidence = "MEDIUM"  # 降低置信度

        # MACD 调整
        if indicators.macd_hist is not None:
            if indicators.macd_hist > 0 and signal == "BEARISH":
                confidence = "LOW"
            elif indicators.macd_hist < 0 and signal == "BULLISH":
                confidence = "LOW"

        return signal, confidence

    def _generate_summary(
        self,
        ticker: str,
        trend: TrendDirection,
        mtf_score: int,
        indicators: TechnicalIndicators,
        signal: str,
    ) -> str:
        """生成摘要"""
        lines = [f"### {ticker} 技术分析摘要", ""]

        # 趋势
        trend_cn = {
            TrendDirection.UPTREND: "上升趋势",
            TrendDirection.DOWNTREND: "下降趋势",
            TrendDirection.SIDEWAYS: "横盘整理",
        }
        lines.append(f"**趋势**: {trend_cn.get(trend, '未知')}")
        lines.append(f"**MTF 评分**: {mtf_score}/3")
        lines.append("")

        # 技术指标
        lines.append("**技术指标**:")
        if indicators.ma20:
            lines.append(f"- MA20: ${indicators.ma20:.2f}")
        if indicators.ma50:
            lines.append(f"- MA50: ${indicators.ma50:.2f}")
        if indicators.ma200:
            lines.append(f"- MA200: ${indicators.ma200:.2f}")
        if indicators.rsi:
            rsi_status = "超买" if indicators.rsi > 70 else ("超卖" if indicators.rsi < 30 else "中性")
            lines.append(f"- RSI: {indicators.rsi:.1f} ({rsi_status})")
        if indicators.macd is not None:
            macd_status = "看多" if indicators.macd_hist and indicators.macd_hist > 0 else "看空"
            lines.append(f"- MACD: {indicators.macd:.2f} ({macd_status})")
        lines.append("")

        # 信号
        lines.append(f"**技术信号**: {signal}")

        return "\n".join(lines)
