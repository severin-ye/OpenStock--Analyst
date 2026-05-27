"""回测报告生成器 — 将回测数据转换为 StockReport 并渲染 HTML"""

import logging
from datetime import datetime
from pathlib import Path

from stock_analysis.backtest import config as cfg
from stock_analysis.data.fetcher import PriceSnapshot
from stock_analysis.ranking.greenblatt import RankingResult
from stock_analysis.reports.schema import (
    AssetCategory,
    ChartDataset,
    ChartDef,
    ChartType,
    CompanyOverview,
    CompetitonSection,
    FScoreItem,
    KeyMetricRow,
    KPIItem,
    PriceChangeRow,
    RiskItem,
    ScenarioRow,
    SignalBlock,
    StockReport,
    ValuationMethod,
    VerdictSection,
)
from stock_analysis.reports.schema import (
    RankingRow as SchemaRankingRow,
)
from stock_analysis.reports.stages.render import render_to_file

logger = logging.getLogger(__name__)

# 货币符号映射
CURRENCY_MAP = {
    "NVDA": "$", "AAPL": "$", "INTC": "$", "TSLA": "$", "AMD": "$", "MU": "$", "LLY": "$", "AVGO": "$",
    "1810.HK": "HK$",
}


def _signal_from_rank(rank_str: str, f_score: int | None, total: int) -> tuple[str, str]:
    """根据排名判定信号 + 方向"""
    try:
        rank_num = int(rank_str.split("/")[0].replace("#", ""))
    except (ValueError, IndexError, AttributeError):
        return ("NEUTRAL", "中性")

    if f_score is not None and f_score <= 3:
        return ("BEARISH", "看空")

    if rank_num <= max(1, total // 3):
        return ("BULLISH", "看多")
    elif rank_num <= max(2, total * 2 // 3):
        return ("NEUTRAL", "中性")
    else:
        return ("BEARISH", "看空")


def _action_from_signal(signal: str) -> str:
    """信号转操作建议"""
    return {"BULLISH": "BUY", "BEARISH": "SELL", "NEUTRAL": "HOLD"}.get(signal, "HOLD")


def _check_deviation(signal: str, ret: float | None) -> str:
    """检查偏差"""
    if ret is None:
        return "—"
    if signal == "BULLISH":
        return "✅正确" if ret > 5 else ("❌错误" if ret < -5 else "➖持平")
    if signal == "BEARISH":
        return "✅正确" if ret < -5 else ("❌错误" if ret > 5 else "➖持平")
    return f"➖中性({ret:+.0f}%)"


def build_backtest_report(
    ticker: str,
    cutoff_label: str,
    cutoff_date: str,
    price: float,
    snapshot: PriceSnapshot,
    rank_result: RankingResult,
    returns: dict,
    all_tickers: list[str],
) -> StockReport:
    """将回测数据构建为 StockReport"""

    currency = CURRENCY_MAP.get(ticker, "$")
    name_map = cfg.NAME_MAP
    company_name = name_map.get(ticker, ticker)

    # 信号判定
    total = len(all_tickers)
    signal, direction = _signal_from_rank(rank_result.composite_rank, snapshot.f_score, total)
    action = _action_from_signal(signal)

    # 回报数据
    ret_6m = returns.get("ret_6m")
    ret_1y = returns.get("ret_1y")
    entry_price = returns.get("entry_price", price)

    # 偏差检查
    dev_6m = _check_deviation(signal, ret_6m)
    dev_1y = _check_deviation(signal, ret_1y)

    # 构建 KPI
    cover_kpi = [
        KPIItem(label="买入价", value=f"{currency}{entry_price:.2f}" if entry_price else "N/A"),
        KPIItem(label="综合排名", value=rank_result.composite_rank),
        KPIItem(label="综合分", value=f"{rank_result.composite_score:.2f}"),
        KPIItem(label="F-Score", value=f"{snapshot.f_score}/9" if snapshot.f_score else "N/A"),
        KPIItem(label="6月回报", value=f"{ret_6m:+.2f}%" if ret_6m is not None else "N/A",
                css_class="up" if (ret_6m or 0) > 0 else "dn"),
        KPIItem(label="1年回报", value=f"{ret_1y:+.2f}%" if ret_1y is not None else "N/A",
                css_class="up" if (ret_1y or 0) > 0 else "dn"),
    ]

    # 涨跌比例总览 (回测特有: 信号 vs 实际)
    s1_price_changes = [
        PriceChangeRow(
            dimension="系统信号",
            change_pct=direction,
            corresponding_price=f"{currency}{entry_price:.2f}" if entry_price else "N/A",
            probability_weight="四层加权排名",
            industry_compare=f"排名 {rank_result.composite_rank}",
        ),
        PriceChangeRow(
            dimension="6个月实际",
            change_pct=f"{ret_6m:+.2f}%" if ret_6m is not None else "N/A",
            corresponding_price=dev_6m,
            probability_weight="持有期回报",
            industry_compare="回测验证",
        ),
        PriceChangeRow(
            dimension="1年实际",
            change_pct=f"{ret_1y:+.2f}%" if ret_1y is not None else "N/A",
            corresponding_price=dev_1y,
            probability_weight="持有期回报",
            industry_compare="回测验证",
        ),
    ]

    # 公司概览
    s2 = CompanyOverview(
        title=f"🏢 {company_name} 回测概览",
        subtitle=f"截止日: {cutoff_date} | 回测时点: {cutoff_label}",
        body_html=f"""
        <p>本报告为回测实验生成，验证四层加权排名系统在历史时点的预测准确性。</p>
        <p><strong>回测方法</strong>: 在 {cutoff_date} 构建历史财报快照，计算排名和信号，然后对比实际持有期回报。</p>
        <p><strong>数据隔离</strong>: 仅使用截止日之前已公开的财报（90天滞后期），避免前瞻偏差。</p>
        """,
        key_metrics=[
            KeyMetricRow(label="EBIT/EV", value=f"{snapshot.ebit_ev}" if snapshot.ebit_ev else "N/A", note="L1指标"),
            KeyMetricRow(label="ROIC", value=f"{snapshot.roic}" if snapshot.roic else "N/A", note="L2指标"),
            KeyMetricRow(label="F-Score", value=f"{snapshot.f_score}/9" if snapshot.f_score else "N/A", note="L3指标"),
            KeyMetricRow(label="PEG", value=f"{snapshot.peg_ratio}" if snapshot.peg_ratio else "N/A", note="L4指标"),
        ],
    )

    # 走势分析 (回测特有: 偏差分析)
    dev_summary = f"6月偏差: {dev_6m} | 1年偏差: {dev_1y}"
    s3_body_html = f"""
    <h3>📊 回测偏差分析</h3>
    <p>{dev_summary}</p>
    <p>信号方向: <strong>{direction}</strong> ({signal}) | 操作建议: <strong>{action}</strong></p>
    """

    # 竞争格局 (回测特有: 排名对比)
    s4 = CompetitonSection(
        title="⚔️ 排名对比",
        subtitle=f"截止日 {cutoff_date} 的排名情况",
        body_html=f"""
        <p>在 {len(all_tickers)} 家公司中，{company_name} 排名 <strong>{rank_result.composite_rank}</strong></p>
        <p>综合分: {rank_result.composite_score:.2f} (越小越好)</p>
        """,
    )

    # Greenblatt 排名行
    greenblatt_ranking = [
        SchemaRankingRow(
            layer=r.layer, dimension=r.dimension, metric=r.metric,
            value=r.value, rank=r.rank, weight=r.weight, verdict=r.verdict,
        )
        for r in rank_result.rows
    ]

    # F-Score 项目
    f_score_items = _build_f_score_items(snapshot)

    # 仪表盘指标
    dashboard_metrics = [
        KeyMetricRow(label="EBIT/EV", value=f"{snapshot.ebit_ev}" if snapshot.ebit_ev else "N/A"),
        KeyMetricRow(label="ROIC", value=f"{snapshot.roic}" if snapshot.roic else "N/A"),
        KeyMetricRow(label="F-Score", value=f"{snapshot.f_score}/9" if snapshot.f_score else "N/A"),
        KeyMetricRow(label="PEG", value=f"{snapshot.peg_ratio}" if snapshot.peg_ratio else "N/A"),
        KeyMetricRow(label="市盈率", value=f"{snapshot.pe_ratio}" if snapshot.pe_ratio else "N/A"),
        KeyMetricRow(label="市值", value=snapshot.market_cap if snapshot.market_cap else "N/A"),
        KeyMetricRow(label="企业价值", value=snapshot.enterprise_value if snapshot.enterprise_value else "N/A"),
        KeyMetricRow(label="FCF Yield", value=snapshot.fcf_yield if snapshot.fcf_yield else "N/A"),
        KeyMetricRow(label="营收增长", value=snapshot.revenue_growth if snapshot.revenue_growth else "N/A"),
    ]

    # 情景分析 (回测特有: 基于信号和实际回报)
    s6_scenarios = _build_scenarios(signal, ret_6m, ret_1y, currency, entry_price)

    # 风险矩阵
    s7_risks = _build_risks(signal, dev_6m, dev_1y)

    # 信号块
    s8_signal = SignalBlock(
        signal=signal,
        confidence="HIGH" if abs((ret_6m or 0)) > 20 else "MEDIUM",
        horizon="MEDIUM",
        action=action,
        conviction="STRONG" if "✅" in dev_6m else "MODERATE",
        rank_summary=f"综合排名 {rank_result.composite_rank}",
        composite_rank=rank_result.composite_rank,
    )

    # 最终裁决
    bull_points, bear_points = _build_verdict_points(signal, ret_6m, ret_1y, dev_6m, dev_1y)
    verdict = VerdictSection(
        title=f"{company_name} 回测验证裁决",
        bull_points=bull_points,
        bear_points=bear_points,
        composite_rank=rank_result.composite_rank,
        f_score_total=f"{snapshot.f_score}/9" if snapshot.f_score else "N/A",
        recommendation=_get_recommendation(signal, dev_6m),
        rec_class="bull" if signal == "BULLISH" else ("bear" if signal == "BEARISH" else "neut"),
    )

    # 图表
    charts = _build_charts(ticker, cutoff_label, rank_result, ret_6m, ret_1y)

    # 侧边栏点
    sidebar_dots = {
        "s1": "bull" if signal == "BULLISH" else ("bear" if signal == "BEARISH" else "neut"),
        "s2": "neut",
        "s3": "bull" if (ret_6m or 0) > 0 else "bear",
        "s4": "neut",
        "s5": "bull" if (snapshot.f_score or 0) >= 6 else "bear",
        "s6": "neut",
        "s7": "neut",
        "s8": "bull" if signal == "BULLISH" else ("bear" if signal == "BEARISH" else "neut"),
    }

    # 构建报告
    report = StockReport(
        report_version="3.0-backtest",
        ticker=ticker,
        company_name=company_name,
        company_name_en=ticker,
        exchange=_get_exchange(ticker),
        sector="回测验证",
        asset_category=AssetCategory.HK_STOCK if ticker.endswith(".HK") else AssetCategory.STOCK,
        report_date=datetime.now().strftime("%Y-%m-%d"),
        data_date=cutoff_date,
        company_dir=f"回测/{company_name}",

        cover_kpi=cover_kpi,
        cover_title=f"回测验证报告 ({cutoff_label})",
        cover_price=f"{currency}{entry_price:.2f}" if entry_price else "N/A",
        cover_market_cap=snapshot.market_cap if snapshot.market_cap else "N/A",

        s1_price_changes=s1_price_changes,
        s1_core_judgment=f"系统信号: {direction} ({signal}) | 实际6月: {ret_6m:+.2f}% | 偏差: {dev_6m}",

        s2=s2,
        s3_body_html=s3_body_html,
        s4=s4,

        greenblatt_ranking=greenblatt_ranking,
        ranking_summary=rank_result.summary,
        f_score_items=f_score_items,
        f_score_total=str(snapshot.f_score) if snapshot.f_score else "0",
        composite_score=rank_result.composite_score,
        composite_rank_8=rank_result.composite_rank,

        s5_body_html=_build_s5_body(snapshot, rank_result),
        s5_valuation_methods=_build_valuation_methods(signal, entry_price, ret_6m, ret_1y, currency),

        dashboard_metrics=dashboard_metrics,

        s6_body_html=f"<p>基于系统信号 <strong>{direction}</strong> 和实际回报的偏差分析。</p>",
        s6_scenarios=s6_scenarios,

        s7_risks=s7_risks,

        s8_signal=s8_signal,

        charts=charts,

        verdict=verdict,

        sidebar_dots=sidebar_dots,

        footer_text="InvestSkill v3.0 · 回测验证报告 · 教育性分析，不构成投资建议",
    )

    return report


def _build_f_score_items(snapshot: PriceSnapshot) -> list[FScoreItem]:
    """构建 F-Score 项目"""
    items = []

    # 简化版 F-Score 项目 (基于快照数据)
    f_score = snapshot.f_score or 0

    # 盈利组
    items.append(FScoreItem(group="盈利", criterion="ROA > 0", score=1 if f_score >= 1 else 0, reason="盈利能力"))
    items.append(FScoreItem(group="盈利", criterion="经营现金流 > 0", score=1 if f_score >= 2 else 0, reason="现金生成"))
    items.append(FScoreItem(group="盈利", criterion="ROA 同比增长", score=1 if f_score >= 3 else 0, reason="盈利改善"))

    # 杠杆组
    items.append(FScoreItem(group="杠杆", criterion="经营现金流 > 净利润", score=1 if f_score >= 4 else 0, reason="盈利质量"))
    items.append(FScoreItem(group="杠杆", criterion="长期债务减少", score=1 if f_score >= 5 else 0, reason="去杠杆"))
    items.append(FScoreItem(group="杠杆", criterion="流动比率改善", score=1 if f_score >= 6 else 0, reason="流动性"))

    # 效率组
    items.append(FScoreItem(group="效率", criterion="股本未稀释", score=1 if f_score >= 7 else 0, reason="股本效率"))
    items.append(FScoreItem(group="效率", criterion="毛利率提升", score=1 if f_score >= 8 else 0, reason="定价权"))
    items.append(FScoreItem(group="效率", criterion="资产周转率提升", score=1 if f_score >= 9 else 0, reason="运营效率"))

    return items


def _build_scenarios(signal: str, ret_6m: float | None, ret_1y: float | None, currency: str, price: float | None) -> list[ScenarioRow]:
    """构建情景分析"""
    scenarios = []
    p = price or 0

    def _sr(scenario: str, prob: str, mult: float, ret: str, desc: str) -> ScenarioRow:
        return ScenarioRow(
            scenario=scenario, probability=prob,
            price_target=f"{currency}{p * mult:.0f}",
            return_pct=ret, description=desc,
        )

    if signal == "BULLISH":
        scenarios.append(_sr("乐观", "40%", 1.3, "+30%", "系统看多正确，大幅上涨"))
        scenarios.append(_sr("中性", "35%", 1.1, "+10%", "温和上涨"))
        scenarios.append(_sr("悲观", "25%", 0.9, "-10%", "系统看多错误"))
    elif signal == "BEARISH":
        scenarios.append(_sr("乐观", "25%", 1.1, "+10%", "系统看空错误"))
        scenarios.append(_sr("中性", "35%", 0.95, "-5%", "小幅下跌"))
        scenarios.append(_sr("悲观", "40%", 0.7, "-30%", "系统看空正确，大幅下跌"))
    else:
        scenarios.append(_sr("乐观", "30%", 1.15, "+15%", "突破预期"))
        scenarios.append(_sr("中性", "45%", 1.0, "0%", "横盘整理"))
        scenarios.append(_sr("悲观", "25%", 0.85, "-15%", "跌破支撑"))

    return scenarios


def _build_risks(signal: str, dev_6m: str, dev_1y: str) -> list[RiskItem]:
    """构建风险矩阵"""
    risks = [
        RiskItem(risk="前瞻偏差", probability="低", impact="高", mitigation="90天财报滞后期"),
        RiskItem(risk="数据质量问题", probability="中", impact="中", mitigation="yfinance 数据验证"),
        RiskItem(risk="市场环境变化", probability="高", impact="高", mitigation="多时点回测验证"),
        RiskItem(risk="信号失效", probability="中" if signal != "NEUTRAL" else "低", impact="高", mitigation="偏差监控"),
        RiskItem(risk="模型过拟合", probability="低", impact="中", mitigation="样本外验证"),
    ]
    return risks


def _build_verdict_points(signal: str, ret_6m: float | None, ret_1y: float | None, dev_6m: str, dev_1y: str) -> tuple[list[str], list[str]]:
    """构建裁决要点"""
    bull_points = []
    bear_points = []

    if signal == "BULLISH":
        bull_points.append("系统信号看多 (BULLISH)")
        if ret_6m and ret_6m > 0:
            bull_points.append(f"6月实际回报 +{ret_6m:.1f}% 验证看多")
        if ret_1y and ret_1y > 0:
            bull_points.append(f"1年实际回报 +{ret_1y:.1f}% 持续验证")
    else:
        bear_points.append(f"系统信号: {signal}")
        if ret_6m and ret_6m < 0:
            bear_points.append(f"6月实际回报 {ret_6m:.1f}% 验证看空")

    if "✅" in dev_6m:
        bull_points.append("6月偏差验证正确")
    elif "❌" in dev_6m:
        bear_points.append("6月偏差验证错误")

    if "✅" in dev_1y:
        bull_points.append("1年偏差验证正确")
    elif "❌" in dev_1y:
        bear_points.append("1年偏差验证错误")

    return bull_points, bear_points


def _build_s5_body(snapshot: PriceSnapshot, rank_result: RankingResult) -> str:
    """构建 S5 估值分析正文"""
    return f"""
    <h3>📊 四层加权排名分析</h3>
    <p>综合分: <strong>{rank_result.composite_score:.2f}</strong> (越小越好)</p>
    <p>综合排名: <strong>{rank_result.composite_rank}</strong></p>
    <p>{rank_result.summary}</p>
    """


def _build_valuation_methods(signal: str, price: float | None, ret_6m: float | None, ret_1y: float | None, currency: str) -> list[ValuationMethod]:
    """构建估值方法"""
    methods = []

    if signal == "BULLISH":
        methods.append(ValuationMethod(name="系统看多", value=f"{currency}{price:.2f}" if price else "N/A", probability="60%"))
        methods.append(ValuationMethod(name="6月目标", value=f"{currency}{(price or 0) * 1.2:.0f}" if price else "N/A", probability="40%"))
    elif signal == "BEARISH":
        methods.append(ValuationMethod(name="系统看空", value=f"{currency}{price:.2f}" if price else "N/A", probability="60%"))
        methods.append(ValuationMethod(name="6月目标", value=f"{currency}{(price or 0) * 0.8:.0f}" if price else "N/A", probability="40%"))
    else:
        methods.append(ValuationMethod(name="系统中性", value=f"{currency}{price:.2f}" if price else "N/A", probability="50%"))
        methods.append(ValuationMethod(name="6月目标", value=f"{currency}{(price or 0) * 1.0:.0f}" if price else "N/A", probability="50%"))

    return methods


def _build_charts(ticker: str, cutoff_label: str, rank_result: RankingResult, ret_6m: float | None, ret_1y: float | None) -> list[ChartDef]:
    """构建图表"""
    charts = []

    # 排名雷达图
    layers = []
    scores = []
    for row in rank_result.rows:
        layers.append(row.layer)
        # 从 rank 提取分数
        try:
            rank_num = int(row.rank.split("/")[0].replace("#", ""))
            total = int(row.rank.split("/")[1])
            score = max(0, min(10, 10 - (rank_num - 1) * 10 / max(1, total - 1)))
        except (ValueError, IndexError):
            score = 5.0
        scores.append(round(score, 1))

    if layers:
        charts.append(ChartDef(
            chart_id="rankingRadar",
            chart_type=ChartType.RADAR,
            section_id="s5",
            title="四层排名雷达图",
            labels=layers,
            datasets=[ChartDataset(label="排名得分", data=scores, color="#2563eb")],
        ))

    # 回报对比柱状图
    if ret_6m is not None or ret_1y is not None:
        charts.append(ChartDef(
            chart_id="returnCompare",
            chart_type=ChartType.BAR,
            section_id="s6",
            title="回报对比",
            labels=["6个月", "1年"],
            datasets=[ChartDataset(
                label="实际回报",
                data=[ret_6m or 0, ret_1y or 0],
                color="#059669" if (ret_6m or 0) > 0 else "#dc2626",
            )],
            y_axis_label="%",
            y_axis_format="%",
            tooltip_suffix="%",
        ))

    return charts


def _get_exchange(ticker: str) -> str:
    """获取交易所"""
    if ticker.endswith(".HK"):
        return "香港交易所"
    elif ticker.endswith(".T"):
        return "东京交易所"
    elif ticker.endswith(".KS"):
        return "韩国交易所"
    elif ticker.endswith(".SS"):
        return "上海证券交易所"
    else:
        return "纳斯达克/纽约"


def _get_recommendation(signal: str, dev_6m: str) -> str:
    """获取推荐"""
    if signal == "BULLISH" and "✅" in dev_6m:
        return "强力推荐"
    elif signal == "BULLISH":
        return "推荐"
    elif signal == "BEARISH" and "✅" in dev_6m:
        return "强力回避"
    elif signal == "BEARISH":
        return "回避"
    else:
        return "持有观望"


def generate_backtest_html_reports(
    all_periods: list[dict],
    snapshots: dict[str, dict[str, PriceSnapshot]],
    rank_results: dict[str, dict[str, RankingResult]],
    output_dir: Path,
) -> list[str]:
    """为所有回测周期生成 HTML 报告"""

    generated_files = []

    # 按公司分组
    by_ticker: dict[str, list[dict]] = {}
    for record in all_periods:
        ticker = record["ticker"]
        if ticker not in by_ticker:
            by_ticker[ticker] = []
        by_ticker[ticker].append(record)

    # 为每个公司生成报告
    for ticker, records in by_ticker.items():
        company_name = cfg.NAME_MAP.get(ticker, ticker)
        company_dir = output_dir / company_name
        company_dir.mkdir(parents=True, exist_ok=True)

        for record in records:
            period = record["period"]
            cutoff = record["cutoff"]

            # 获取对应的快照和排名结果
            snap = snapshots.get(cutoff, {}).get(ticker)
            rank = rank_results.get(cutoff, {}).get(ticker)

            if not snap or not rank:
                logger.warning(f"  跳过 {ticker} @{period}: 缺少快照或排名结果")
                continue

            # 构建报告
            report = build_backtest_report(
                ticker=ticker,
                cutoff_label=period,
                cutoff_date=cutoff,
                price=record.get("entry_price", 0),
                snapshot=snap,
                rank_result=rank,
                returns={
                    "entry_price": record.get("entry_price"),
                    "ret_6m": record.get("ret_6m"),
                    "ret_1y": record.get("ret_1y"),
                },
                all_tickers=cfg.RANKING_UNIVERSE,
            )

            # 渲染 HTML
            filename = f"260527_回测_{period}.html"
            output_path = str(company_dir / filename)

            try:
                render_to_file(report, output_path, logger)
                generated_files.append(output_path)
                logger.info(f"  生成: {output_path}")
            except Exception as e:
                logger.error(f"  渲染失败 {ticker} @{period}: {e}")

    return generated_files
