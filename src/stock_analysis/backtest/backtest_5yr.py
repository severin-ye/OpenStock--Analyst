"""五年回测实验 — 小米、特斯拉、英伟达

功能：
1. 10个时点（每半年）回测
2. 概率加权预测 vs 实际回报对比
3. 生成综合分析报告
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


def weighted_prediction(signal: str, composite_score: float, total: int) -> dict:
    """概率加权预测
    
    Args:
        signal: 信号类型 (BULLISH/NEUTRAL/BEARISH)
        composite_score: 综合分（越小越好）
        total: 排名总数
    
    Returns:
        dict: {
            "prob_up": 上涨概率,
            "expected_return_6m": 6个月预期回报,
            "expected_return_1y": 1年预期回报,
            "confidence": 置信度
        }
    """
    weights = cfg.SIGNAL_WEIGHTS.get(signal, cfg.SIGNAL_WEIGHTS["NEUTRAL"])
    
    # 基础概率和预期回报
    base_prob = weights["prob"]
    base_return = weights["expected_return"]
    
    # 根据排名位置调整
    try:
        rank_num = int(composite_score)  # composite_score 越小越好
        rank_pct = rank_num / total if total > 0 else 0.5  # 排名百分比（0-1，越小越好）
    except (ValueError, TypeError):
        rank_pct = 0.5
    
    # 排名越靠前（rank_pct越小），概率和回报越高
    rank_adjustment = 1.0 - rank_pct  # 0-1，越大越好
    
    # 调整概率
    prob_up = base_prob + (rank_adjustment - 0.5) * 0.2  # ±10%调整
    
    # 调整预期回报
    return_adjustment = rank_adjustment * 0.1  # ±10%调整
    expected_return_6m = base_return + return_adjustment
    expected_return_1y = expected_return_6m * 1.5  # 1年回报约为6个月的1.5倍
    
    # 置信度
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
    """检查预测准确性
    
    Returns:
        dict: {
            "direction_correct_6m": 方向是否正确（6个月）,
            "direction_correct_1y": 方向是否正确（1年）,
            "return_error_6m": 回报误差（6个月）,
            "return_error_1y": 回报误差（1年）,
            "prob_calibration": 概率校准度
        }
    """
    result = {
        "direction_correct_6m": None,
        "direction_correct_1y": None,
        "return_error_6m": None,
        "return_error_1y": None,
        "prob_calibration": None,
    }
    
    # 方向正确性（6个月）
    if actual_6m is not None:
        predicted_up = prediction["prob_up"] > 0.5
        actual_up = actual_6m > 0
        result["direction_correct_6m"] = predicted_up == actual_up
        
        # 回报误差
        result["return_error_6m"] = abs(prediction["expected_return_6m"] - actual_6m / 100)
    
    # 方向正确性（1年）
    if actual_1y is not None:
        predicted_up = prediction["prob_up"] > 0.5
        actual_up = actual_1y > 0
        result["direction_correct_1y"] = predicted_up == actual_up
        
        # 回报误差
        result["return_error_1y"] = abs(prediction["expected_return_1y"] - actual_1y / 100)
    
    # 概率校准度（预测概率与实际结果的匹配程度）
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
    logger.info("=" * 120)

    all_periods = []
    all_snapshots: dict[str, dict[str, PriceSnapshot]] = {}
    all_rank_results: dict[str, dict[str, RankingResult]] = {}

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

        # 4. 对每个目标公司计算排名
        period_results = {}
        rank_results_for_cutoff: dict[str, RankingResult] = {}
        
        # 检查是否有有效的财报数据
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
            
            # 跳过没有有效数据的公司
            if ebit_ev_val is None:
                logger.warning(f"  {ticker}: 无 EBIT/EV 数据，跳过排名")
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

            sig, dir_str = signal_from_rank(rank_result.composite_rank, snap.f_score, total)
            
            # 概率加权预测
            prediction = weighted_prediction(sig, rank_result.composite_score, total)
            
            period_results[ticker] = {
                "ticker": ticker,
                "rank": rank_result.composite_rank,
                "composite_score": round(rank_result.composite_score, 2),
                "score_10": rank_result.score_10,
                "f_score": snap.f_score,
                "signal": sig,
                "direction": dir_str,
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
            sig = pr.get("signal", "N/A")
            ret_6m = rr.get("ret_6m")
            ret_1y = rr.get("ret_1y")
            
            # 检查预测准确性
            prediction = pr.get("prediction", {})
            accuracy = check_prediction_accuracy(prediction, ret_6m, ret_1y)

            record = {
                "period": label,
                "cutoff": cutoff,
                "ticker": ticker,
                "entry_price": rr.get("entry_price"),
                "rank": pr.get("rank", "N/A"),
                "composite_score": pr.get("composite_score"),
                "score_10": pr.get("score_10"),
                "f_score": pr.get("f_score"),
                "signal": sig,
                "direction": pr.get("direction", ""),
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
            
            logger.info(
                f"  {name:6s} {ep:>10s}  "
                f"排名={pr.get('rank', 'N/A'):>5s}  "
                f"信号={sig:>8s}  "
                f"预测上涨概率={prob_up:>6s}  "
                f"实际:6m={r6s:>8s} {dir_correct}  "
                f"1y={r1s:>8s}"
            )

        all_periods.extend(period_records)

    # ── 生成汇总 ──
    out_dir = RESULTS_DIR / "backtest_5yr_260528"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "all_results.json", "w", encoding="utf-8") as f:
        json.dump(all_periods, f, ensure_ascii=False, indent=2, default=str)

    # 生成 summary.md
    generate_summary(all_periods, out_dir)
    
    # 生成 HTML 报告
    from stock_analysis.backtest.backtest_report import generate_backtest_html_reports
    html_files = generate_backtest_html_reports(all_periods, all_snapshots, all_rank_results, out_dir)
    logger.info(f"  HTML 报告: {len(html_files)} 份")
    
    # 生成概率加权分析报告
    generate_probability_analysis(all_periods, out_dir)

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"\n{'=' * 120}")
    logger.info(f"回测完成: {elapsed:.0f}s → {out_dir}")
    logger.info(f"{'=' * 120}")
    return all_periods


def generate_summary(records: list[dict], out_dir: Path):
    """生成汇总报告"""
    lines = []
    lines.append("# 五年回测实验报告\n")
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append(f"**目标公司**: {', '.join(cfg.NAME_MAP.get(t, t) for t in cfg.TARGET)}")
    lines.append(f"**排名对照组**: {len(cfg.RANKING_UNIVERSE)} 家（含{cfg.NAME_MAP.get('1810.HK','小米')}混入美股）")
    lines.append(f"**回测时点**: {len(cfg.CUTOFFS)} 个（5年，每半年）")
    lines.append(f"**概率加权**: 基于信号类型和排名位置\n")

    # 统计
    total = len(records)
    bullish = sum(1 for r in records if r["signal"] == "BULLISH")
    neutral = sum(1 for r in records if r["signal"] == "NEUTRAL")
    bearish = sum(1 for r in records if r["signal"] == "BEARISH")

    # 方向正确性统计
    correct_6m = sum(1 for r in records if r.get("accuracy", {}).get("direction_correct_6m") is True)
    wrong_6m = sum(1 for r in records if r.get("accuracy", {}).get("direction_correct_6m") is False)
    correct_1y = sum(1 for r in records if r.get("accuracy", {}).get("direction_correct_1y") is True)
    wrong_1y = sum(1 for r in records if r.get("accuracy", {}).get("direction_correct_1y") is False)

    lines.append(f"**总观测数**: {total}（BULLISH={bullish}, NEUTRAL={neutral}, BEARISH={bearish}）")
    if (correct_6m + wrong_6m) > 0:
        pct_6m = correct_6m / (correct_6m + wrong_6m) * 100
        lines.append(f"**6 月方向正确率**: {correct_6m}/{correct_6m + wrong_6m}（{pct_6m:.1f}%）")
    else:
        lines.append("")
    if (correct_1y + wrong_1y) > 0:
        pct_1y = correct_1y / (correct_1y + wrong_1y) * 100
        lines.append(f"**1 年方向正确率**: {correct_1y}/{correct_1y + wrong_1y}（{pct_1y:.1f}%）")
    else:
        lines.append("")
    lines.append("")

    # 按公司分组
    for ticker in cfg.TARGET:
        name = cfg.NAME_MAP.get(ticker, ticker)
        recs = [r for r in records if r["ticker"] == ticker]
        sym = "$" if ticker != "1810.HK" else "HK$"
        lines.append(f"## {name} ({ticker})\n")
        lines.append(f"| 时点 | 买入价 | 排名 | 信号 | 预测概率 | 预期回报 | 6月实际 | 方向 | 1年实际 | 方向 |")
        lines.append(f"|------|--------|:----:|:----:|:-------:|:-------:|:-------:|:----:|:-------:|:----:|")
        for r in recs:
            ep = f"{sym}{r['entry_price']:.2f}" if r['entry_price'] else "N/A"
            r6s = f"{r['ret_6m']:+.2f}%" if r['ret_6m'] is not None else "N/A"
            r1s = f"{r['ret_1y']:+.2f}%" if r['ret_1y'] is not None else "N/A"
            pred = r.get("prediction", {})
            prob_up = f"{pred.get('prob_up', 0)*100:.1f}%" if pred else "N/A"
            exp_ret = f"{pred.get('expected_return_6m', 0)*100:+.1f}%" if pred else "N/A"
            acc = r.get("accuracy", {})
            dir_6m = "✅" if acc.get("direction_correct_6m") is True else "❌" if acc.get("direction_correct_6m") is False else "—"
            dir_1y = "✅" if acc.get("direction_correct_1y") is True else "❌" if acc.get("direction_correct_1y") is False else "—"
            
            lines.append(
                f"| {r['period']} | {ep} | {r['rank'] or 'N/A'} | "
                f"{r['signal']} | {prob_up} | {exp_ret} | "
                f"{r6s} | {dir_6m} | {r1s} | {dir_1y} |"
            )
        lines.append("")

    # 关键发现
    lines.append("## 关键发现\n")
    lines.append("- ✅ 方向正确: 预测方向与实际方向一致")
    lines.append("- ❌ 方向错误: 预测方向与实际方向相反")
    lines.append("- 概率加权: 基于信号类型和排名位置计算的上涨概率")
    lines.append("- 预期回报: 基于概率加权的预期回报率")
    lines.append("")

    out_path = out_dir / "summary.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"  汇总报告: {out_path}")


def generate_probability_analysis(records: list[dict], out_dir: Path):
    """生成概率加权分析报告"""
    lines = []
    lines.append("# 概率加权分析报告\n")
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # 按信号类型统计
    signal_stats = {}
    for r in records:
        signal = r["signal"]
        if signal not in signal_stats:
            signal_stats[signal] = {
                "count": 0,
                "correct_6m": 0,
                "wrong_6m": 0,
                "total_prob": 0,
                "total_actual_6m": 0,
            }
        signal_stats[signal]["count"] += 1
        signal_stats[signal]["total_prob"] += r.get("prediction", {}).get("prob_up", 0)
        
        acc = r.get("accuracy", {})
        if acc.get("direction_correct_6m") is True:
            signal_stats[signal]["correct_6m"] += 1
        elif acc.get("direction_correct_6m") is False:
            signal_stats[signal]["wrong_6m"] += 1
        
        if r.get("ret_6m") is not None:
            signal_stats[signal]["total_actual_6m"] += 1
    
    lines.append("## 信号类型统计\n")
    lines.append("| 信号类型 | 观测数 | 预测概率 | 实际正确率 | 校准度 |")
    lines.append("|---------|:------:|:-------:|:---------:|:-----:|")
    
    for signal, stats in signal_stats.items():
        count = stats["count"]
        if count == 0:
            continue
        
        avg_prob = stats["total_prob"] / count
        correct = stats["correct_6m"]
        wrong = stats["wrong_6m"]
        total = correct + wrong
        actual_rate = correct / total if total > 0 else 0
        calibration = 1.0 - abs(avg_prob - actual_rate)
        
        lines.append(
            f"| {signal} | {count} | {avg_prob*100:.1f}% | "
            f"{actual_rate*100:.1f}% ({correct}/{total}) | {calibration*100:.1f}% |"
        )
    
    lines.append("")
    
    # 按公司统计
    lines.append("## 公司统计\n")
    lines.append("| 公司 | 观测数 | 平均预测概率 | 6月正确率 | 平均回报 |")
    lines.append("|------|:------:|:----------:|:--------:|:-------:|")
    
    for ticker in cfg.TARGET:
        name = cfg.NAME_MAP.get(ticker, ticker)
        recs = [r for r in records if r["ticker"] == ticker]
        count = len(recs)
        
        if count == 0:
            continue
        
        avg_prob = sum(r.get("prediction", {}).get("prob_up", 0) for r in recs) / count
        
        correct = sum(1 for r in recs if r.get("accuracy", {}).get("direction_correct_6m") is True)
        wrong = sum(1 for r in recs if r.get("accuracy", {}).get("direction_correct_6m") is False)
        total = correct + wrong
        correct_rate = correct / total if total > 0 else 0
        
        actual_returns = [r["ret_6m"] for r in recs if r.get("ret_6m") is not None]
        avg_return = sum(actual_returns) / len(actual_returns) if actual_returns else 0
        
        lines.append(
            f"| {name} | {count} | {avg_prob*100:.1f}% | "
            f"{correct_rate*100:.1f}% ({correct}/{total}) | {avg_return:+.2f}% |"
        )
    
    lines.append("")
    
    # 预测 vs 实际散点图数据
    lines.append("## 预测 vs 实际对比\n")
    lines.append("```json")
    scatter_data = []
    for r in records:
        if r.get("ret_6m") is not None and r.get("prediction"):
            scatter_data.append({
                "ticker": r["ticker"],
                "period": r["period"],
                "predicted_prob": r["prediction"]["prob_up"],
                "actual_return": r["ret_6m"],
                "direction_correct": r.get("accuracy", {}).get("direction_correct_6m"),
            })
    lines.append(json.dumps(scatter_data, indent=2, ensure_ascii=False))
    lines.append("```\n")
    
    out_path = out_dir / "probability_analysis.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"  概率分析报告: {out_path}")


if __name__ == "__main__":
    run()
