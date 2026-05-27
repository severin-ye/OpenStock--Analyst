"""Institutional Analyzer — 基于 InvestSkill 的机构持仓分析框架

分析维度：
1. 机构持仓概览
2. 持仓变化趋势
3. 聪明钱流向
4. 持仓集中度
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import yfinance as yf

logger = logging.getLogger(__name__)


class OwnershipTrend(str, Enum):
    INCREASING = "INCREASING"
    STABLE = "STABLE"
    DECREASING = "DECREASING"


class SmartMoneySignal(str, Enum):
    ACCUMULATING = "ACCUMULATING"
    HOLDING = "HOLDING"
    DISTRIBUTING = "DISTRIBUTING"


@dataclass
class InstitutionalHolder:
    """机构持有人"""
    name: str
    shares: int
    value: float
    pct_outstanding: float
    change_pct: Optional[float] = None


@dataclass
class InstitutionalSignal:
    """机构持仓信号"""
    ticker: str
    institutional_ownership_pct: float
    num_holders: int
    trend: OwnershipTrend
    top_holders: list[InstitutionalHolder]
    smart_money_signal: SmartMoneySignal
    concentration: float  # Top 10 持仓占比
    signal: str  # BULLISH / NEUTRAL / BEARISH
    confidence: str  # HIGH / MEDIUM / LOW
    summary: str


class InstitutionalAnalyzer:
    """机构持仓分析器

    基于 InvestSkill 的 institutional-ownership 提示词，分析 SEC 13F 数据。
    """

    def analyze(self, ticker: str) -> Optional[InstitutionalSignal]:
        """分析机构持仓

        Args:
            ticker: 股票代码

        Returns:
            InstitutionalSignal 或 None
        """
        try:
            # 获取机构持仓数据
            inst_data = self._fetch_institutional_data(ticker)
            if inst_data is None:
                logger.warning(f"无法获取 {ticker} 的机构持仓数据")
                return None

            # 解析持仓数据
            holders = self._parse_holders(inst_data)
            if not holders:
                logger.warning(f"{ticker} 无机构持仓数据")
                return None

            # 计算汇总指标
            total_pct = sum(h.pct_outstanding for h in holders)
            num_holders = len(holders)

            # 计算集中度（Top 10）
            top_holders = sorted(holders, key=lambda h: h.shares, reverse=True)[:10]
            concentration = sum(h.pct_outstanding for h in top_holders)

            # 分析趋势
            trend = self._analyze_trend(holders)

            # 分析聪明钱信号
            smart_money = self._analyze_smart_money(top_holders)

            # 生成信号
            signal, confidence = self._generate_signal(
                ownership_pct=total_pct,
                trend=trend,
                smart_money=smart_money,
                concentration=concentration,
            )

            # 生成摘要
            summary = self._generate_summary(
                ticker=ticker,
                ownership_pct=total_pct,
                num_holders=num_holders,
                trend=trend,
                smart_money=smart_money,
                signal=signal,
            )

            return InstitutionalSignal(
                ticker=ticker,
                institutional_ownership_pct=total_pct,
                num_holders=num_holders,
                trend=trend,
                top_holders=top_holders,
                smart_money_signal=smart_money,
                concentration=concentration,
                signal=signal,
                confidence=confidence,
                summary=summary,
            )

        except Exception as e:
            logger.error(f"机构持仓分析失败 {ticker}: {e}")
            return None

    def _fetch_institutional_data(self, ticker: str) -> Optional[dict]:
        """获取机构持仓数据"""
        try:
            t = yf.Ticker(ticker)

            # 获取机构持有人
            holders = t.institutional_holders
            if holders is not None and not holders.empty:
                return {"holders": holders}

            return None
        except Exception as e:
            logger.error(f"获取 {ticker} 机构数据失败: {e}")
            return None

    def _parse_holders(self, inst_data: dict) -> list[InstitutionalHolder]:
        """解析持有人数据"""
        holders = []

        try:
            df = inst_data.get("holders")
            if df is None or df.empty:
                return holders

            for _, row in df.iterrows():
                try:
                    # 解析持仓比例
                    pct_str = str(row.get("% Out", "0"))
                    pct = float(pct_str.replace("%", "")) / 100 if "%" in pct_str else float(pct_str)

                    # 解析变化
                    change_str = str(row.get("Change", "0"))
                    change = None
                    if change_str and change_str != "nan":
                        try:
                            change = float(change_str.replace("%", "").replace("+", ""))
                        except ValueError:
                            pass

                    holders.append(InstitutionalHolder(
                        name=str(row.get("Holder", "")),
                        shares=int(row.get("Shares", 0)),
                        value=float(row.get("Value", 0)),
                        pct_outstanding=pct,
                        change_pct=change,
                    ))
                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"解析机构持仓数据失败: {e}")

        return holders

    def _analyze_trend(self, holders: list[InstitutionalHolder]) -> OwnershipTrend:
        """分析持仓趋势"""
        # 计算平均变化
        changes = [h.change_pct for h in holders if h.change_pct is not None]
        if not changes:
            return OwnershipTrend.STABLE

        avg_change = sum(changes) / len(changes)

        if avg_change > 5:
            return OwnershipTrend.INCREASING
        elif avg_change < -5:
            return OwnershipTrend.DECREASING
        else:
            return OwnershipTrend.STABLE

    def _analyze_smart_money(self, top_holders: list[InstitutionalHolder]) -> SmartMoneySignal:
        """分析聪明钱信号

        聪明钱特征：
        - 对冲基金：高换手率，战术性强
        - 价值投资者：长期持有，信号强
        - 主动管理基金：选股能力强
        """
        # 简化版：基于前10大持仓者的变化
        changes = [h.change_pct for h in top_holders if h.change_pct is not None]
        if not changes:
            return SmartMoneySignal.HOLDING

        avg_change = sum(changes) / len(changes)
        positive_count = sum(1 for c in changes if c > 0)

        # 如果大部分机构在增持
        if positive_count >= len(changes) * 0.7 and avg_change > 3:
            return SmartMoneySignal.ACCUMULATING
        # 如果大部分机构在减持
        elif positive_count <= len(changes) * 0.3 and avg_change < -3:
            return SmartMoneySignal.DISTRIBUTING
        else:
            return SmartMoneySignal.HOLDING

    def _generate_signal(
        self,
        ownership_pct: float,
        trend: OwnershipTrend,
        smart_money: SmartMoneySignal,
        concentration: float,
    ) -> tuple[str, str]:
        """生成信号"""
        # 基于趋势和聪明钱
        if trend == OwnershipTrend.INCREASING and smart_money == SmartMoneySignal.ACCUMULATING:
            signal = "BULLISH"
            confidence = "HIGH"
        elif trend == OwnershipTrend.INCREASING:
            signal = "BULLISH"
            confidence = "MEDIUM"
        elif trend == OwnershipTrend.DECREASING and smart_money == SmartMoneySignal.DISTRIBUTING:
            signal = "BEARISH"
            confidence = "HIGH"
        elif trend == OwnershipTrend.DECREASING:
            signal = "BEARISH"
            confidence = "MEDIUM"
        else:
            signal = "NEUTRAL"
            confidence = "MEDIUM"

        # 持仓比例调整
        if ownership_pct < 0.3:
            # 机构持仓比例低，信号较弱
            confidence = "LOW"
        elif ownership_pct > 0.8:
            # 机构持仓比例高，信号较强
            if confidence == "MEDIUM":
                confidence = "HIGH"

        # 集中度调整
        if concentration > 0.5:
            # 高集中度，风险较高
            if signal == "BULLISH":
                confidence = "MEDIUM"

        return signal, confidence

    def _generate_summary(
        self,
        ticker: str,
        ownership_pct: float,
        num_holders: int,
        trend: OwnershipTrend,
        smart_money: SmartMoneySignal,
        signal: str,
    ) -> str:
        """生成摘要"""
        lines = [f"### {ticker} 机构持仓分析", ""]

        # 持仓概览
        lines.append("**持仓概览**:")
        lines.append(f"- 机构持仓比例: {ownership_pct:.1%}")
        lines.append(f"- 机构持有人数: {num_holders}")
        lines.append("")

        # 趋势
        trend_cn = {
            OwnershipTrend.INCREASING: "增持",
            OwnershipTrend.STABLE: "稳定",
            OwnershipTrend.DECREASING: "减持",
        }
        lines.append("**持仓趋势**:")
        lines.append(f"- 趋势方向: {trend_cn.get(trend, '未知')}")
        lines.append("")

        # 聪明钱
        smart_cn = {
            SmartMoneySignal.ACCUMULATING: "积累中",
            SmartMoneySignal.HOLDING: "持有",
            SmartMoneySignal.DISTRIBUTING: "分发中",
        }
        lines.append("**聪明钱信号**:")
        lines.append(f"- 信号: {smart_cn.get(smart_money, '未知')}")
        lines.append("")

        # 信号
        lines.append(f"**机构信号**: {signal}")

        return "\n".join(lines)
