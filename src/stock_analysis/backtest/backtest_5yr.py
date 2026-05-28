"""五年回测实验 — 小米、特斯拉、英伟达

功能：
1. 10个时点（每半年）回测
2. 集成所有分析模块（技术分析、内部人、机构持仓、财报、行业、宏观、竞争）
3. 多维度信号综合判断
4. 概率加权预测 vs 实际回报对比
5. 生成综合分析报告
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from stock_analysis.backtest import config as cfg
from stock_analysis.backtest.historical_fetcher import build_all_snapshots, get_price_at_date
from stock_analysis.backtest.returns_calculator import compute_all_returns
from stock_analysis.data.fetcher import PriceSnapshot
from stock_analysis.ranking.greenblatt import compute_greenblatt, RankingResult
from stock_analysis.analysis import (
    TechnicalAnalyzer,
    InsiderAnalyzer,
    InstitutionalAnalyzer,
    EarningsAnalyzer,
    SectorAnalyzer,
    EconomicsAnalyzer,
    CompetitorAnalyzer,
    ResultValidator,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent / "results"


def _pv(snap: PriceSnapshot, attr: str):
    """从 PriceSnapshot 安全取值"""
    v = getattr(snap, attr, None)
    if v is None or v == "" or v == "N/A":
        return None
    if isinstance(v, str):
        v = v.replace("%", "").replace("x", "").strip()
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def signal_from_rank(rank_str: str, f_score: int | None, total: int) -> tuple[str, str]:
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


def run_analysis_modules(ticker: str) -> dict:
    """运行所有分析模块
    
    Args:
        ticker: 股票代码
    
    Returns:
        dict: 各模块分析结果
    """
    results = {
        "technical": None,
        "insider": None,
        "institutional": None,
        "earnings": None,
        "sector": None,
        "economics": None,
        "competitor": None,
    }
    
    # 技术分析
    try:
        tech = TechnicalAnalyzer()
        tech_signal = tech.analyze(ticker, period="1y")
        if tech_signal:
            results["technical"] = {
                "signal": tech_signal.signal,
                "confidence": tech_signal.confidence,
                "mtf_score": tech_signal.mtf_score,
                "trend": tech_signal.trend.value,
            }
    except Exception as e:
        logger.debug(f"  技术分析失败 {ticker}: {e}")
    
    # 内部人交易分析
    try:
        insider = InsiderAnalyzer()
        insider_signal = insider.analyze(ticker)
        if insider_signal:
            results["insider"] = {
                "signal": insider_signal.signal,
                "confidence": insider_signal.confidence,
                "net_sentiment": insider_signal.net_sentiment,
            }
    except Exception as e:
        logger.debug(f"  内部人分析失败 {ticker}: {e}")
    
    # 机构持仓分析
    try:
        inst = InstitutionalAnalyzer()
        inst_signal = inst.analyze(ticker)
        if inst_signal:
            results["institutional"] = {
                "signal": inst_signal.signal,
                "confidence": inst_signal.confidence,
                "ownership_pct": inst_signal.institutional_ownership_pct,
            }
    except Exception as e:
        logger.debug(f"  机构持仓分析失败 {ticker}: {e}")
    
    # 财报分析
    try:
        earnings = EarningsAnalyzer()
        earnings_signal = earnings.analyze(ticker)
        if earnings_signal:
            results["earnings"] = {
                "signal": earnings_signal.signal,
                "confidence": earnings_signal.confidence,
                "tone": earnings_signal.management_tone.value,
            }
    except Exception as e:
        logger.debug(f"  财报分析失败 {ticker}: {e}")
    
    # 行业分析
    try:
        sector = SectorAnalyzer()
        sector_signal = sector.analyze(ticker)
        if sector_signal:
            results["sector"] = {
                "signal": sector_signal.signal,
                "confidence": sector_signal.confidence,
                "score": sector_signal.sector_score,
            }
    except Exception as e:
        logger.debug(f"  行业分析失败 {ticker}: {e}")
    
    # 竞争分析
    try:
        competitor = CompetitorAnalyzer()
        competitor_signal = competitor.analyze(ticker)
        if competitor_signal:
            results["competitor"] = {
                "signal": competitor_signal.signal,
                "confidence": competitor_signal.confidence,
                "moat": competitor_signal.moat_width.value,
            }
    except Exception as e:
        logger.debug(f"  竞争分析失败 {ticker}: {e}")
    
    return results


def get_composite_signal(analysis_results: dict, rank_signal: str) -> tuple[str, str]:
    """综合多维度信号
    
    Args:
        analysis_results: 各模块分析结果
        rank_signal: 排名信号
    
    Returns:
        tuple: (综合信号, 置信度)
    """
    signals = []
    confidences = []
    
    # 收集所有信号
    if analysis_results.get("technical"):
        signals.append(analysis_results["technical"]["signal"])
        confidences.append(analysis_results["technical"]["confidence"])
    
    if analysis_results.get("insider"):
        signals.append(analysis_results["insider"]["signal"])
        confidences.append(analysis_results["insider"]["confidence"])
    
    if analysis_results.get("institutional"):
        signals.append(analysis_results["institutional"]["signal"])
        confidences.append(analysis_results["institutional"]["confidence"])
    
    if analysis_results.get("earnings"):
        signals.append(analysis_results["earnings"]["signal"])
        confidences.append(analysis_results["earnings"]["confidence"])
    
    if analysis_results.get("sector"):
        signals.append(analysis_results["sector"]["signal"])
        confidences.append(analysis_results["sector"]["confidence"])
    
    if analysis_results.get("competitor"):
        signals.append(analysis_results["competitor"]["signal"])
        confidences.append(analysis_results["competitor"]["confidence"])
    
    # 添加排名信号
    signals.append(rank_signal)
    
    if not signals:
        return "NEUTRAL", "LOW"
    
    # 投票决定综合信号
    bullish_count = signals.count("BULLISH")
    bearish_count = signals.count("BEARISH")
    neutral_count = signals.count("NEUTRAL")
    
    total = len(signals)
    
    if bullish_count > total * 0.5:
        composite_signal = "BULLISH"
    elif bearish_count > total * 0.5:
        composite_signal = "BEARISH"
    elif bullish_count > bearish_count:
        composite_signal = "BULLISH"
    elif bearish_count > bullish_count:
        composite_signal = "BEARISH"
    else:
        composite_signal = "NEUTRAL"
    
    # 计算置信度
    high_count = confidences.count("HIGH")
    medium_count = confidences.count("MEDIUM")
    
    if high_count >= len(confidences) * 0.5:
        confidence = "HIGH"
    elif high_count + medium_count >= len(confidences) * 0.7:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    return composite_signal, confidence


def weighted_prediction(signal: str, composite_score: float, total: int) -> dict:
    """概率加权预测"""
    weights = cfg.SIGNAL_WEIGHTS.get(signal, cfg.SIGNAL_WEIGHTS["NEUTRAL"])
    
    base_prob = weights["prob"]
    base_return = weights["expected_return"]
    
    try:
        rank_num = int(composite_score)
        rank_pct = rank_num / total if total > 0 else 0.5
    except (ValueError, TypeError):
        rank_pct = 0.5
    
    rank_adjustment = 1.0 - rank_pct
    
    prob_up = base_prob + (rank_adjustment - 0.5) * 0.2
    return_adjustment = rank_adjustment * 0.1
    expected_return_6m = base_return + return_adjustment
    expected_return_1y = expected_return_6m * 1.5
    
    if abs(rank_adjustment - 0.5) > 0.3:
        confidence = "HIGH"
    elif abs(rank_adjustment - 0.5) > 0.15:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    return {
        "prob_up": round(prob_up, 3),
        "expected_return_6m": round(expected_return_6m, 4),
        "expected_return_1y": round(expected_return_1y, 4),
        "confidence": confidence,
        "rank_adjustment": round(rank_adjustment, 3),
    }


def check_prediction_accuracy(prediction: dict, actual_6m: float | None, actual_1y: float | None) -> dict:
    """检查预测准确性"""
    result = {
        "direction_correct_6m": None,
        "direction_correct_1y": None,
        "return_error_6m": None,
        "return_error_1y": None,
        "prob_calibration": None,
    }
    
    if actual_6m is not None:
        predicted_up = prediction["prob_up"] > 0.5
        actual_up = actual_6m > 0
        result["direction_correct_6m"] = predicted_up == actual_up
        result["return_error_6m"] = abs(prediction["expected_return_6m"] - actual_6m / 100)
    
    if actual_1y is not None:
        predicted_up = prediction["prob_up"] > 0.5
        actual_up = actual_1y > 0
        result["direction_correct_1y"] = predicted_up == actual_up
        result["return_error_1y"] = abs(prediction["expected_return_1y"] - actual_1y / 100)
    
    if actual_6m is not None:
        actual_prob = 1.0 if actual_6m > 0 else 0.0
        result["prob_calibration"] = 1.0 - abs(prediction["prob_up"] - actual_prob)
    
    return result


def run():
    """运行五年回测实验"""
    start_time = datetime.now()
    logger.info("=" * 120)
    logger.info(f"五年回测实验开始: {start_time.isoformat()}")
    logger.info(f"目标公司: {cfg.TARGET}")
    logger.info(f"排名对照组: {cfg.RANKING_UNIVERSE} ({len(cfg.RANKING_UNIVERSE)} 家)")
    logger.info(f"回测时点: {[c[0] for c in cfg.CUTOFFS]} ({len(cfg.CUTOFFS)} 个)")
    logger.info("集成模块: 技术分析、内部人交易、机构持仓、财报分析、行业分析、竞争分析")
    logger.info("=" * 120)

    all_periods = []
    all_snapshots: dict[str, dict[str, PriceSnapshot]] = {}
    all_rank_results: dict[str, dict[str, RankingResult]] = {}

    # 宏观经济分析（全局）
    logger.info("\n📊 宏观经济分析...")
    economics = EconomicsAnalyzer()
    econ_signal = economics.analyze()
    logger.info(f"  经济周期: {econ_signal.phase.value}, 信号: {econ_signal.signal}")

    for label, cutoff in cfg.CUTOFFS:
        logger.info(f"\n{'─' * 100}")
        logger.info(f"▶ {label} (截止日 {cutoff})")
        logger.info(f"{'─' * 100}")

        # 1. 获取所有公司的价格
        prices = {}
        for ticker in cfg.RANKING_UNIVERSE:
            p = get_price_at_date(ticker, cutoff)
            if p:
                prices[ticker] = p

        if not prices:
            logger.warning(f"  {label}: 无价格数据，跳过")
            continue

        # 2. 构建历史财报快照
        snapshots = build_all_snapshots(list(prices.keys()), cutoff, prices)

        if not snapshots:
            logger.warning(f"  {label}: 无财报快照，跳过")
            continue
        
        all_snapshots[cutoff] = snapshots

        # 3. 提取各层指标用于排名
        all_ebit_ev: dict[str, float] = {}
        all_roic: dict[str, float] = {}
        all_f_score: dict[str, int] = {}
        all_peg: dict[str, float] = {}

        for t, snap in snapshots.items():
            ebit_ev_val = _pv(snap, "ebit_ev")
            roic_val = _pv(snap, "roic")
            peg_val = _pv(snap, "peg_ratio")
            if ebit_ev_val is not None:
                all_ebit_ev[t] = ebit_ev_val
            if roic_val is not None:
                all_roic[t] = roic_val
            if snap.f_score is not None and snap.f_score != 0:
                all_f_score[t] = snap.f_score
            if peg_val is not None and peg_val > 0:
                all_peg[t] = peg_val

        total = len(all_ebit_ev)
        logger.info(f"  排名公司数: {total} (有 EBIT/EV)")

        # 4. 对每个目标公司计算排名和运行分析模块
        period_results = {}
        rank_results_for_cutoff: dict[str, RankingResult] = {}
        
        valid_snapshots = {t: s for t, s in snapshots.items() if _pv(s, "ebit_ev") is not None}
        if not valid_snapshots:
            logger.warning(f"  {label}: 无有效财报数据，跳过")
            continue
        
        for ticker in cfg.RANKING_UNIVERSE:
            if ticker not in snapshots:
                continue
            snap = snapshots[ticker]
            ebit_ev_val = _pv(snap, "ebit_ev")
            roic_val = _pv(snap, "roic")
            peg_val = _pv(snap, "peg_ratio")
            
            if ebit_ev_val is None:
                continue

            rank_result = compute_greenblatt(
                ticker=ticker,
                ebit_ev=ebit_ev_val,
                roic=roic_val,
                f_score=snap.f_score,
                peg=peg_val,
                all_ebit_ev=all_ebit_ev,
                all_roic=all_roic,
                all_f_score=all_f_score,
                all_peg=all_peg,
            )
            
            rank_results_for_cutoff[ticker] = rank_result

            # 排名信号
            rank_sig, rank_dir = signal_from_rank(rank_result.composite_rank, snap.f_score, total)
            
            # 运行所有分析模块（仅目标公司）
            analysis_results = {}
            if ticker in cfg.TARGET:
                logger.info(f"  📈 运行分析模块 {ticker}...")
                analysis_results = run_analysis_modules(ticker)
            
            # 综合多维度信号
            composite_signal, composite_confidence = get_composite_signal(analysis_results, rank_sig)
            
            # 概率加权预测
            prediction = weighted_prediction(composite_signal, rank_result.composite_score, total)
            
            period_results[ticker] = {
                "ticker": ticker,
                "rank": rank_result.composite_rank,
                "composite_score": round(rank_result.composite_score, 2),
                "score_10": rank_result.score_10,
                "f_score": snap.f_score,
                "rank_signal": rank_sig,
                "rank_direction": rank_dir,
                "analysis_results": analysis_results,
                "composite_signal": composite_signal,
                "composite_confidence": composite_confidence,
                "prediction": prediction,
            }
        
        all_rank_results[cutoff] = rank_results_for_cutoff

        # 5. 计算实际回报（仅目标公司）
        raw_returns = compute_all_returns(cfg.TARGET, cutoff)

        # 6. 合并输出
        period_records = []
        for ticker in cfg.TARGET:
            pr = period_results.get(ticker, {})
            rr = raw_returns.get(ticker, {})
            sig = pr.get("composite_signal", "N/A")
            ret_6m = rr.get("ret_6m")
            ret_1y = rr.get("ret_1y")
            
            prediction = pr.get("prediction", {})
            accuracy = check_prediction_accuracy(prediction, ret_6m, ret_1y)

            record = {
                "period": label,
                "cutoff": cutoff,
                "ticker": ticker,
                "entry_price": rr.get("entry_price"),
                "rank": pr.get("rank", "N/A"),
                "composite_score": pr.get("composite_score"),
                "f_score": pr.get("f_score"),
                "rank_signal": pr.get("rank_signal", "N/A"),
                "composite_signal": sig,
                "composite_confidence": pr.get("composite_confidence", "N/A"),
                "analysis_results": pr.get("analysis_results", {}),
                "prediction": prediction,
                "ret_6m": ret_6m,
                "ret_1y": ret_1y,
                "accuracy": accuracy,
            }
            period_records.append(record)

            name = cfg.NAME_MAP.get(ticker, ticker)
            sym = "$" if ticker != "1810.HK" else "HK$"
            ep = f"{sym}{rr.get('entry_price', 'N/A')}"
            r6s = f"{ret_6m:+.2f}%" if ret_6m is not None else "N/A"
            r1s = f"{ret_1y:+.2f}%" if ret_1y is not None else "N/A"
            prob_up = f"{prediction.get('prob_up', 0)*100:.1f}%" if prediction else "N/A"
            dir_correct = "✅" if accuracy.get("direction_correct_6m") else "❌" if accuracy.get("direction_correct_6m") is False else "—"
            
            # 分析模块信号汇总
            tech_sig = pr.get("analysis_results", {}).get("technical", {}).get("signal", "—")
            insider_sig = pr.get("analysis_results", {}).get("insider", {}).get("signal", "—")
            inst_sig = pr.get("analysis_results", {}).get("institutional", {}).get("signal", "—")
            
            logger.info(
                f"  {name:6s} {ep:>10s}  "
                f"排名={pr.get('rank', 'N/A'):>5s}  "
                f"排名信号={pr.get('rank_signal', 'N/A'):>8s}  "
                f"综合信号={sig:>8s}  "
                f"技术={tech_sig:>8s}  "
                f"内部人={insider_sig:>8s}  "
                f"机构={inst_sig:>8s}  "
                f"实际:6m={r6s:>8s} {dir_correct}"
            )

        all_periods.extend(period_records)

    # ── 生成汇总 ──
    out_dir = RESULTS_DIR / "backtest_integrated_260528"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "all_results.json", "w", encoding="utf-8") as f:
        json.dump(all_periods, f, ensure_ascii=False, indent=2, default=str)

    # 生成 summary.md
    generate_summary(all_periods, out_dir)
    
    # 生成 HTML 报告
    from stock_analysis.backtest.backtest_report import generate_backtest_html_reports
    html_files = generate_backtest_html_reports(all_periods, all_snapshots, all_rank_results, out_dir)
    logger.info(f"  HTML 报告: {len(html_files)} 份")
    
    # 生成多维度信号分析报告
    generate_multidim_analysis(all_periods, out_dir)

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"\n{'=' * 120}")
    logger.info(f"回测完成: {elapsed:.0f}s → {out_dir}")
    logger.info(f"{'=' * 120}")
    return all_periods


def generate_summary(records: list[dict], out_dir: Path):
    """生成汇总报告"""
    lines = []
    lines.append("# 集成分析模块回测实验报告\n")
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append(f"**目标公司**: {', '.join(cfg.NAME_MAP.get(t, t) for t in cfg.TARGET)}")
    lines.append(f"**排名对照组**: {len(cfg.RANKING_UNIVERSE)} 家")
    lines.append(f"**回测时点**: {len(cfg.CUTOFFS)} 个（5年，每半年）")
    lines.append(f"**集成模块**: 技术分析、内部人交易、机构持仓、财报分析、行业分析、竞争分析\n")

    # 统计
    total = len(records)
    bullish = sum(1 for r in records if r["composite_signal"] == "BULLISH")
    neutral = sum(1 for r in records if r["composite_signal"] == "NEUTRAL")
    bearish = sum(1 for r in records if r["composite_signal"] == "BEARISH")

    # 方向正确性统计
    correct_6m = sum(1 for r in records if r.get("accuracy", {}).get("direction_correct_6m") is True)
    wrong_6m = sum(1 for r in records if r.get("accuracy", {}).get("direction_correct_6m") is False)
    correct_1y = sum(1 for r in records if r.get("accuracy", {}).get("direction_correct_1y") is True)
    wrong_1y = sum(1 for r in records if r.get("accuracy", {}).get("direction_correct_1y") is False)

    lines.append(f"**总观测数**: {total}（BULLISH={bullish}, NEUTRAL={neutral}, BEARISH={bearish}）")
    if (correct_6m + wrong_6m) > 0:
        pct_6m = correct_6m / (correct_6m + wrong_6m) * 100
        lines.append(f"**6 月方向正确率**: {correct_6m}/{correct_6m + wrong_6m}（{pct_6m:.1f}%）")
    if (correct_1y + wrong_1y) > 0:
        pct_1y = correct_1y / (correct_1y + wrong_1y) * 100
        lines.append(f"**1 年方向正确率**: {correct_1y}/{correct_1y + wrong_1y}（{pct_1y:.1f}%）")
    lines.append("")

    # 按公司分组
    for ticker in cfg.TARGET:
        name = cfg.NAME_MAP.get(ticker, ticker)
        recs = [r for r in records if r["ticker"] == ticker]
        sym = "$" if ticker != "1810.HK" else "HK$"
        lines.append(f"## {name} ({ticker})\n")
        lines.append(f"| 时点 | 买入价 | 排名 | 排名信号 | 综合信号 | 技术 | 内部人 | 机构 | 6月实际 | 方向 |")
        lines.append(f"|------|--------|:----:|:-------:|:-------:|:----:|:------:|:----:|:-------:|:----:|")
        for r in recs:
            ep = f"{sym}{r['entry_price']:.2f}" if r['entry_price'] else "N/A"
            r6s = f"{r['ret_6m']:+.2f}%" if r['ret_6m'] is not None else "N/A"
            
            analysis = r.get("analysis_results", {})
            tech_sig = analysis.get("technical", {}).get("signal", "—") if analysis.get("technical") else "—"
            insider_sig = analysis.get("insider", {}).get("signal", "—") if analysis.get("insider") else "—"
            inst_sig = analysis.get("institutional", {}).get("signal", "—") if analysis.get("institutional") else "—"
            
            acc = r.get("accuracy", {})
            dir_6m = "✅" if acc.get("direction_correct_6m") is True else "❌" if acc.get("direction_correct_6m") is False else "—"
            
            lines.append(
                f"| {r['period']} | {ep} | {r['rank'] or 'N/A'} | "
                f"{r.get('rank_signal', 'N/A')} | {r['composite_signal']} | "
                f"{tech_sig} | {insider_sig} | {inst_sig} | "
                f"{r6s} | {dir_6m} |"
            )
        lines.append("")

    out_path = out_dir / "summary.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"  汇总报告: {out_path}")


def generate_multidim_analysis(records: list[dict], out_dir: Path):
    """生成多维度信号分析报告"""
    lines = []
    lines.append("# 多维度信号分析报告\n")
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # 按信号源统计正确率
    lines.append("## 信号源正确率对比\n")
    lines.append("| 信号源 | 6月正确率 | 样本数 |")
    lines.append("|--------|:---------:|:------:|")
    
    # 排名信号
    rank_correct = sum(1 for r in records if r.get("rank_signal") == "BULLISH" and r.get("ret_6m", 0) > 0)
    rank_total = sum(1 for r in records if r.get("rank_signal") in ["BULLISH", "BEARISH"])
    if rank_total > 0:
        lines.append(f"| 排名信号 | {rank_correct}/{rank_total} ({rank_correct/rank_total*100:.1f}%) | {rank_total} |")
    
    # 综合信号
    composite_correct = sum(1 for r in records if r.get("accuracy", {}).get("direction_correct_6m") is True)
    composite_total = sum(1 for r in records if r.get("accuracy", {}).get("direction_correct_6m") is not None)
    if composite_total > 0:
        lines.append(f"| 综合信号 | {composite_correct}/{composite_total} ({composite_correct/composite_total*100:.1f}%) | {composite_total} |")
    
    # 技术信号
    tech_correct = sum(1 for r in records 
                       if r.get("analysis_results", {}).get("technical", {}).get("signal") == "BULLISH" 
                       and r.get("ret_6m", 0) > 0)
    tech_total = sum(1 for r in records 
                     if r.get("analysis_results", {}).get("technical", {}).get("signal") in ["BULLISH", "BEARISH"])
    if tech_total > 0:
        lines.append(f"| 技术信号 | {tech_correct}/{tech_total} ({tech_correct/tech_total*100:.1f}%) | {tech_total} |")
    
    lines.append("")
    
    # 信号一致性分析
    lines.append("## 信号一致性分析\n")
    lines.append("| 时点 | 公司 | 排名 | 技术 | 内部人 | 机构 | 一致 | 实际 |")
    lines.append("|------|------|:----:|:----:|:------:|:----:|:----:|:----:|")
    
    for r in records:
        analysis = r.get("analysis_results", {})
        rank_sig = r.get("rank_signal", "—")
        tech_sig = analysis.get("technical", {}).get("signal", "—") if analysis.get("technical") else "—"
        insider_sig = analysis.get("insider", {}).get("signal", "—") if analysis.get("insider") else "—"
        inst_sig = analysis.get("institutional", {}).get("signal", "—") if analysis.get("institutional") else "—"
        
        # 检查一致性
        sigs = [s for s in [rank_sig, tech_sig, insider_sig, inst_sig] if s != "—"]
        if sigs:
            all_same = all(s == sigs[0] for s in sigs)
            consistent = "✅" if all_same else "❌"
        else:
            consistent = "—"
        
        actual = f"{r['ret_6m']:+.1f}%" if r.get('ret_6m') is not None else "N/A"
        
        lines.append(
            f"| {r['period']} | {cfg.NAME_MAP.get(r['ticker'], r['ticker'])} | "
            f"{rank_sig} | {tech_sig} | {insider_sig} | {inst_sig} | "
            f"{consistent} | {actual} |"
        )
    
    lines.append("")
    
    out_path = out_dir / "multidim_analysis.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"  多维度分析报告: {out_path}")


if __name__ == "__main__":
    run()
