"""Insider Analyzer — 基于 InvestSkill 的内部人交易分析框架

分析维度：
1. 交易汇总：买卖数量、金额
2. 情绪分析：净情绪计算
3. 显著交易识别
4. 内部人分类
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import yfinance as yf

logger = logging.getLogger(__name__)


class InsiderSentiment(str, Enum):
    STRONGLY_BULLISH = "STRONGLY BULLISH"
    MODERATELY_BULLISH = "MODERATELY BULLISH"
    NEUTRAL = "NEUTRAL"
    MODERATELY_BEARISH = "MODERATELY BEARISH"
    STRONGLY_BEARISH = "STRONGLY BEARISH"


@dataclass
class InsiderTransaction:
    """内部人交易"""
    date: str
    insider: str
    title: str
    transaction_type: str  # Buy / Sell / Exercise
    shares: int
    price: float
    value: float


@dataclass
class InsiderSignal:
    """内部人交易信号"""
    ticker: str
    total_transactions: int
    buy_count: int
    sell_count: int
    net_sentiment: float  # -1.0 to +1.0
    sentiment: InsiderSentiment
    total_buy_value: float
    total_sell_value: float
    significant_transactions: list[InsiderTransaction]
    signal: str  # BULLISH / NEUTRAL / BEARISH
    confidence: str  # HIGH / MEDIUM / LOW
    summary: str


class InsiderAnalyzer:
    """内部人交易分析器

    基于 InvestSkill 的 insider-trading 提示词，分析 SEC Form 4 数据。
    """

    def analyze(self, ticker: str) -> Optional[InsiderSignal]:
        """分析内部人交易

        Args:
            ticker: 股票代码

        Returns:
            InsiderSignal 或 None
        """
        try:
            # 获取内部人交易数据
            insider_data = self._fetch_insider_data(ticker)
            if insider_data is None:
                logger.warning(f"无法获取 {ticker} 的内部人交易数据")
                return None

            # 分析交易
            transactions = self._parse_transactions(insider_data)

            # 计算情绪
            buy_count, sell_count, buy_value, sell_value = self._calculate_totals(transactions)
            net_sentiment = self._calculate_net_sentiment(buy_value, sell_value)
            sentiment = self._classify_sentiment(net_sentiment)

            # 识别显著交易
            significant = self._identify_significant(transactions)

            # 生成信号
            signal, confidence = self._generate_signal(
                net_sentiment=net_sentiment,
                buy_count=buy_count,
                sell_count=sell_count,
                significant_count=len(significant),
            )

            # 生成摘要
            summary = self._generate_summary(
                ticker=ticker,
                total=len(transactions),
                buy_count=buy_count,
                sell_count=sell_count,
                net_sentiment=net_sentiment,
                sentiment=sentiment,
                signal=signal,
            )

            return InsiderSignal(
                ticker=ticker,
                total_transactions=len(transactions),
                buy_count=buy_count,
                sell_count=sell_count,
                net_sentiment=net_sentiment,
                sentiment=sentiment,
                total_buy_value=buy_value,
                total_sell_value=sell_value,
                significant_transactions=significant,
                signal=signal,
                confidence=confidence,
                summary=summary,
            )

        except Exception as e:
            logger.error(f"内部人交易分析失败 {ticker}: {e}")
            return None

    def _fetch_insider_data(self, ticker: str) -> Optional[dict]:
        """获取内部人交易数据"""
        try:
            t = yf.Ticker(ticker)
            # yfinance 提供 insider_purchases 和 insider_transactions
            insider_transactions = t.insider_transactions
            if insider_transactions is not None and not insider_transactions.empty:
                return {"transactions": insider_transactions}
            return None
        except Exception as e:
            logger.error(f"获取 {ticker} 内部人数据失败: {e}")
            return None

    def _parse_transactions(self, insider_data: dict) -> list[InsiderTransaction]:
        """解析交易数据"""
        transactions = []

        try:
            df = insider_data.get("transactions")
            if df is None or df.empty:
                return transactions

            for _, row in df.iterrows():
                try:
                    # 解析交易类型
                    text = str(row.get("Text", ""))
                    if "Purchase" in text or "Buy" in text:
                        tx_type = "Buy"
                    elif "Sale" in text or "Sell" in text:
                        tx_type = "Sell"
                    else:
                        tx_type = "Other"

                    # 解析数量和价格
                    shares = abs(int(row.get("Shares", 0)))
                    price = float(row.get("Price", 0))
                    value = shares * price

                    transactions.append(InsiderTransaction(
                        date=str(row.get("Start Date", "")),
                        insider=str(row.get("Insider", "")),
                        title=str(row.get("Title", "")),
                        transaction_type=tx_type,
                        shares=shares,
                        price=price,
                        value=value,
                    ))
                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"解析内部人交易数据失败: {e}")

        return transactions

    def _calculate_totals(
        self,
        transactions: list[InsiderTransaction],
    ) -> tuple[int, int, float, float]:
        """计算买卖汇总"""
        buy_count = 0
        sell_count = 0
        buy_value = 0.0
        sell_value = 0.0

        for tx in transactions:
            if tx.transaction_type == "Buy":
                buy_count += 1
                buy_value += tx.value
            elif tx.transaction_type == "Sell":
                sell_count += 1
                sell_value += tx.value

        return buy_count, sell_count, buy_value, sell_value

    def _calculate_net_sentiment(self, buy_value: float, sell_value: float) -> float:
        """计算净情绪

        公式: (Buy $ - Sell $) / (Buy $ + Sell $)
        范围: -1.0 到 +1.0
        """
        total = buy_value + sell_value
        if total == 0:
            return 0.0
        return (buy_value - sell_value) / total

    def _classify_sentiment(self, net_sentiment: float) -> InsiderSentiment:
        """分类情绪"""
        if net_sentiment >= 0.5:
            return InsiderSentiment.STRONGLY_BULLISH
        elif net_sentiment >= 0.2:
            return InsiderSentiment.MODERATELY_BULLISH
        elif net_sentiment >= -0.2:
            return InsiderSentiment.NEUTRAL
        elif net_sentiment >= -0.5:
            return InsiderSentiment.MODERATELY_BEARISH
        else:
            return InsiderSentiment.STRONGLY_BEARISH

    def _identify_significant(
        self,
        transactions: list[InsiderTransaction],
        min_value: float = 1_000_000,
    ) -> list[InsiderTransaction]:
        """识别显著交易

        显著交易标准：
        - 交易金额 > $1M
        - CEO/CFO 交易
        """
        significant = []

        for tx in transactions:
            # 金额标准
            if tx.value >= min_value:
                significant.append(tx)
                continue

            # 高管标准
            if any(title in tx.title.upper() for title in ["CEO", "CFO", "COO", "PRESIDENT"]):
                significant.append(tx)

        return significant

    def _generate_signal(
        self,
        net_sentiment: float,
        buy_count: int,
        sell_count: int,
        significant_count: int,
    ) -> tuple[str, str]:
        """生成信号"""
        # 基于净情绪
        if net_sentiment >= 0.3:
            signal = "BULLISH"
            confidence = "HIGH"
        elif net_sentiment >= 0.1:
            signal = "BULLISH"
            confidence = "MEDIUM"
        elif net_sentiment <= -0.3:
            signal = "BEARISH"
            confidence = "HIGH"
        elif net_sentiment <= -0.1:
            signal = "BEARISH"
            confidence = "MEDIUM"
        else:
            signal = "NEUTRAL"
            confidence = "MEDIUM"

        # 调整置信度
        if significant_count >= 3:
            # 多笔显著交易，提高置信度
            if confidence == "MEDIUM":
                confidence = "HIGH"
        elif significant_count == 0:
            # 无显著交易，降低置信度
            if confidence == "HIGH":
                confidence = "MEDIUM"

        # 交易数量调整
        total = buy_count + sell_count
        if total < 3:
            # 样本量太小
            confidence = "LOW"

        return signal, confidence

    def _generate_summary(
        self,
        ticker: str,
        total: int,
        buy_count: int,
        sell_count: int,
        net_sentiment: float,
        sentiment: InsiderSentiment,
        signal: str,
    ) -> str:
        """生成摘要"""
        lines = [f"### {ticker} 内部人交易分析", ""]

        # 交易汇总
        lines.append("**交易汇总**:")
        lines.append(f"- 总交易数: {total}")
        lines.append(f"- 买入: {buy_count} 笔")
        lines.append(f"- 卖出: {sell_count} 笔")
        lines.append("")

        # 情绪分析
        sentiment_cn = {
            InsiderSentiment.STRONGLY_BULLISH: "强烈看多",
            InsiderSentiment.MODERATELY_BULLISH: "温和看多",
            InsiderSentiment.NEUTRAL: "中性",
            InsiderSentiment.MODERATELY_BEARISH: "温和看空",
            InsiderSentiment.STRONGLY_BEARISH: "强烈看空",
        }
        lines.append("**情绪分析**:")
        lines.append(f"- 净情绪: {net_sentiment:.2f}")
        lines.append(f"- 情绪分类: {sentiment_cn.get(sentiment, '未知')}")
        lines.append("")

        # 信号
        lines.append(f"**内部人信号**: {signal}")

        return "\n".join(lines)
