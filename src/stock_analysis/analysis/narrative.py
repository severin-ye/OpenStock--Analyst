"""Narrative Analyzer — 捕获市场叙事和主题

分析维度：
1. 公司叙事识别（EV、AI、元宇宙等）
2. 新闻情绪分析
3. 主题匹配评分
4. 叙事强度评估
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import yfinance as yf

logger = logging.getLogger(__name__)


class NarrativeStrength(str, Enum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    NONE = "NONE"


@dataclass
class MatchedTheme:
    """匹配的主题"""
    theme: str
    relevance: float  # 0-1
    source: str  # 来源


@dataclass
class NarrativeSignal:
    """叙事分析信号"""
    ticker: str
    company_name: str
    narrative_strength: NarrativeStrength
    matched_themes: list[MatchedTheme]
    news_sentiment: float  # -1 到 +1
    social_sentiment: float  # -1 到 +1
    signal: str  # BULLISH / NEUTRAL / BEARISH
    confidence: str  # HIGH / MEDIUM / LOW
    summary: str


class NarrativeAnalyzer:
    """叙事分析器

    分析公司的市场叙事和主题热度。
    """

    # 已知的主题关键词（可扩展）
    THEME_KEYWORDS = {
        "AI": ["artificial intelligence", "AI", "machine learning", "deep learning", "neural network", "LLM", "generative AI"],
        "EV": ["electric vehicle", "EV", "smart EV", "autonomous driving", "self-driving", "battery", "charging"],
        "Cloud": ["cloud computing", "cloud", "SaaS", "data center", "hyperscaler"],
        "Semiconductor": ["chip", "semiconductor", "foundry", "wafer", "GPU", "CPU", "processor"],
        "Crypto": ["cryptocurrency", "blockchain", "bitcoin", "ethereum", "DeFi", "Web3"],
        "Metaverse": ["metaverse", "AR", "VR", "virtual reality", "spatial computing"],
        "Robotics": ["robot", "automation", "humanoid", "Boston Dynamics"],
        "Green Energy": ["solar", "wind", "renewable", "clean energy", "carbon neutral", "ESG"],
    }

    def analyze(self, ticker: str) -> Optional[NarrativeSignal]:
        """分析公司叙事

        Args:
            ticker: 股票代码

        Returns:
            NarrativeSignal 或 None
        """
        try:
            # 获取公司信息
            stock_info = self._fetch_stock_info(ticker)
            if stock_info is None:
                return None

            company_name = stock_info.get("shortName", ticker)
            business_summary = stock_info.get("longBusinessSummary", "")
            industry = stock_info.get("industry", "")
            sector = stock_info.get("sector", "")

            # 匹配主题
            matched_themes = self._match_themes(
                company_name=company_name,
                business_summary=business_summary,
                industry=industry,
                sector=sector,
            )

            # 计算叙事强度
            narrative_strength = self._calculate_narrative_strength(matched_themes, stock_info)

            # 分析新闻情绪
            news_sentiment = self._analyze_news_sentiment(ticker)

            # 分析社交媒体情绪
            social_sentiment = self._analyze_social_sentiment(ticker)

            # 生成信号
            signal, confidence = self._generate_signal(
                narrative_strength=narrative_strength,
                news_sentiment=news_sentiment,
                social_sentiment=social_sentiment,
                matched_themes=matched_themes,
            )

            # 生成摘要
            summary = self._generate_summary(
                ticker=ticker,
                company_name=company_name,
                narrative_strength=narrative_strength,
                matched_themes=matched_themes,
                news_sentiment=news_sentiment,
                signal=signal,
            )

            return NarrativeSignal(
                ticker=ticker,
                company_name=company_name,
                narrative_strength=narrative_strength,
                matched_themes=matched_themes,
                news_sentiment=news_sentiment,
                social_sentiment=social_sentiment,
                signal=signal,
                confidence=confidence,
                summary=summary,
            )

        except Exception as e:
            logger.error(f"叙事分析失败 {ticker}: {e}")
            return None

    def _fetch_stock_info(self, ticker: str) -> Optional[dict]:
        """获取公司信息"""
        try:
            t = yf.Ticker(ticker)
            return t.info
        except Exception:
            return None

    def _match_themes(
        self,
        company_name: str,
        business_summary: str,
        industry: str,
        sector: str,
    ) -> list[MatchedTheme]:
        """匹配公司到已知主题"""
        themes = []

        # 合并所有文本
        full_text = f"{company_name} {business_summary} {industry} {sector}".lower()

        for theme_name, keywords in self.THEME_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw.lower() in full_text)
            if matches > 0:
                relevance = min(1.0, matches / len(keywords) * 2)
                themes.append(MatchedTheme(
                    theme=theme_name,
                    relevance=round(relevance, 2),
                    source="company_description",
                ))

        return themes

    def _calculate_narrative_strength(
        self,
        themes: list[MatchedTheme],
        stock_info: dict,
    ) -> NarrativeStrength:
        """计算叙事强度"""
        if not themes:
            return NarrativeStrength.NONE

        # 主题数量
        theme_count = len(themes)
        # 平均相关性
        avg_relevance = sum(t.relevance for t in themes) / theme_count if themes else 0

        # 营收增速加成
        revenue_growth = stock_info.get("revenueGrowth")
        growth_bonus = 1 if revenue_growth and revenue_growth > 0.2 else 0

        # 综合评分
        if theme_count >= 3 and avg_relevance > 0.6:
            strength = NarrativeStrength.STRONG
        elif theme_count >= 2 and avg_relevance > 0.4:
            strength = NarrativeStrength.MODERATE
        elif theme_count >= 1:
            strength = NarrativeStrength.WEAK
        else:
            strength = NarrativeStrength.NONE

        # 高增长加成
        if strength == NarrativeStrength.MODERATE and growth_bonus > 0:
            strength = NarrativeStrength.STRONG
        elif strength == NarrativeStrength.WEAK and growth_bonus > 0:
            strength = NarrativeStrength.MODERATE

        return strength

    def _analyze_news_sentiment(self, ticker: str) -> float:
        """分析新闻情绪

        简化版：基于公司推荐评级推断
        """
        try:
            t = yf.Ticker(ticker)
            info = t.info

            # 分析师推荐：1=Strong Buy, 5=Strong Sell
            recommendation = info.get("recommendationMean")
            if recommendation:
                # 转换为 -1 到 +1
                # 1 (Strong Buy) → +1, 5 (Strong Sell) → -1
                sentiment = 1.0 - (recommendation - 1) / 2
                return round(max(-1.0, min(1.0, sentiment)), 2)

            # 分析师目标价 vs 当前价
            target_price = info.get("targetMeanPrice")
            current_price = info.get("currentPrice")
            if target_price and current_price:
                upside = (target_price / current_price - 1)
                # 转换为 -1 到 +1
                sentiment = min(1.0, upside * 5)
                return round(max(-1.0, min(1.0, sentiment)), 2)

            return 0.0

        except Exception:
            return 0.0

    def _analyze_social_sentiment(self, ticker: str) -> float:
        """分析社交媒体情绪

        简化版：基于动量推断
        """
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="1mo")

            if hist.empty:
                return 0.0

            # 使用短期内价格动量作为社交情绪的代理
            start_price = hist["Close"].iloc[0]
            end_price = hist["Close"].iloc[-1]
            momentum = (end_price / start_price - 1)

            # 转换为 -1 到 +1
            sentiment = min(1.0, momentum * 10)
            return round(max(-1.0, min(1.0, sentiment)), 2)

        except Exception:
            return 0.0

    def _generate_signal(
        self,
        narrative_strength: NarrativeStrength,
        news_sentiment: float,
        social_sentiment: float,
        matched_themes: list[MatchedTheme],
    ) -> tuple[str, str]:
        """生成信号"""
        # 基于叙事强度
        if narrative_strength == NarrativeStrength.STRONG:
            base_signal = "BULLISH"
            base_confidence = "HIGH"
        elif narrative_strength == NarrativeStrength.MODERATE:
            base_signal = "BULLISH"
            base_confidence = "MEDIUM"
        elif narrative_strength == NarrativeStrength.WEAK:
            base_signal = "NEUTRAL"
            base_confidence = "MEDIUM"
        else:
            base_signal = "NEUTRAL"
            base_confidence = "LOW"

        # 新闻情绪调整
        if news_sentiment > 0.3 and base_signal != "BULLISH":
            base_signal = "BULLISH"
        elif news_sentiment < -0.3 and base_signal == "BULLISH":
            base_confidence = "MEDIUM"

        # 主题质量调整
        hot_themes = ["AI", "EV"]
        has_hot_theme = any(t.theme in hot_themes for t in matched_themes)
        if has_hot_theme:
            if base_signal == "NEUTRAL":
                base_signal = "BULLISH"
                base_confidence = "MEDIUM"

        return base_signal, base_confidence

    def _generate_summary(
        self,
        ticker: str,
        company_name: str,
        narrative_strength: NarrativeStrength,
        matched_themes: list[MatchedTheme],
        news_sentiment: float,
        signal: str,
    ) -> str:
        """生成摘要"""
        lines = [f"### {company_name} 叙事分析", ""]

        # 叙事强度
        strength_cn = {
            NarrativeStrength.STRONG: "强烈",
            NarrativeStrength.MODERATE: "中等",
            NarrativeStrength.WEAK: "微弱",
            NarrativeStrength.NONE: "无",
        }
        lines.append("**叙事强度**:")
        lines.append(f"- 强度: {strength_cn.get(narrative_strength, '未知')}")
        lines.append("")

        # 匹配主题
        if matched_themes:
            lines.append("**匹配主题**:")
            for theme in matched_themes:
                lines.append(f"- {theme.theme}: 相关性 {theme.relevance:.0%} ({theme.source})")
            lines.append("")

        # 情绪
        sentiment_label = "积极" if news_sentiment > 0.1 else ("消极" if news_sentiment < -0.1 else "中性")
        lines.append("**市场情绪**:")
        lines.append(f"- 新闻情绪: {news_sentiment:+.2f} ({sentiment_label})")
        lines.append("")

        # 信号
        lines.append(f"**叙事信号**: {signal}")

        return "\n".join(lines)
