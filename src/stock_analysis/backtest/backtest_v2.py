"""回测系统 v2 — 数据隔离 + 调用真实系统

核心逻辑：
1. 数据隔离：获取历史价格和财报，避免前瞻偏差
2. 调用真实系统：用真实排名和分析模块生成信号
3. 记录结果：对比预测 vs 实际回报
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
    NarrativeAnalyzer,
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


def get_signal_from_rank(rank_result: RankingResult, f_score: int | None, total: int) -> tuple[str, str, str]:
    """从真实排名结果获取信号（与 cli.py 逻辑一致）
    
    Returns:
        tuple: (signal, action, conviction)
    """
    try:
        rank_num = int(rank_result.composite_rank.split("/")[0].replace("#", ""))
    except (ValueError, IndexError, AttributeError):
        return "NEUTRAL", "HOLD", "MODERATE"

    # F-Score 过低 → 强制 BEARISH
    if f_score is not None and f_score <= 3:
        return "BEARISH", "SELL", "WEAK"

    # 基于排名位置
    if rank_num <= max(1, total // 3):
        return "BULLISH", "BUY", "STRONG"
    elif rank_num <= max(2, total * 2 // 3):
        return "NEUTRAL", "HOLD", "MODERATE"
    else:
        return "BEARISH", "SELL", "WEAK"


def run_real_analysis(ticker: str) -> dict:
    """调用真实分析系统
    
    Args:
        ticker: 股票代码
    
    Returns:
        dict: 各模块分析结果（与真实系统输出一致）
    """
    results = {}
    
    # 技术分析（真实模块）
    try:
        tech = TechnicalAnalyzer()
        tech_signal = tech.analyze(ticker, period="1y")
        if tech_signal:
            results["technical"] = {
                "signal": tech_signal.signal,
                "confidence": tech_signal.confidence,
                "mtf_score": tech_signal.mtf_score,
            }
    except Exception as e:
        logger.debug(f"  技术分析失败: {e}")
    
    # 内部人交易（真实模块）
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
        logger.debug(f"  内部人分析失败: {e}")
    
    # 机构持仓（真实模块）
    try:
        inst = InstitutionalAnalyzer()
        inst_signal = inst.analyze(ticker)
        if inst_signal:
            results["institutional"] = {
                "signal": inst_signal.signal,
                "confidence": inst_signal.confidence,
            }
    except Exception as e:
        logger.debug(f"  机构持仓分析失败: {e}")
    
    # 财报分析（真实模块）
    try:
        earnings = EarningsAnalyzer()
        earnings_signal = earnings.analyze(ticker)
        if earnings_signal:
            results["earnings"] = {
                "signal": earnings_signal.signal,
                "confidence": earnings_signal.confidence,
            }
    except Exception as e:
        logger.debug(f"  财报分析失败: {e}")
    
    # 行业分析（真实模块）
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
        logger.debug(f"  行业分析失败: {e}")
    
    # 竞争分析（真实模块）
    try:
        competitor = CompetitorAnalyzer()
        competitor_signal = competitor.analyze(ticker)
        if competitor_signal:
            results["competitor"] = {
                "signal": competitor_signal.signal,
                "confidence": competitor_signal.confidence,
            }
    except Exception as e:
        logger.debug(f"  竞争分析失败: {e}")
    
    # 叙事分析（真实模块）
    try:
        narrative = NarrativeAnalyzer()
        narrative_signal = narrative.analyze(ticker)
        if narrative_signal:
            results["narrative"] = {
                "signal": narrative_signal.signal,
                "confidence": narrative_signal.confidence,
                "strength": narrative_signal.narrative_strength.value,
            }
    except Exception as e:
        logger.debug(f"  叙事分析失败: {e}")
    
    return results


def get_final_signal(rank_signal: str, analysis_results: dict) -> tuple[str, str]:
    """综合所有信号得到最终判断（与真实系统逻辑一致）
    
    Args:
        rank_signal: 排名信号
        analysis_results: 分析模块结果
    
    Returns:
        tuple: (signal, confidence)
    """
    signals = [rank_signal]
    
    # 收集所有分析模块的信号
    for module_name, module_result in analysis_results.items():
        if module_result and "signal" in module_result:
            signals.append(module_result["signal"])
    
    # 投票机制
    bullish_count = signals.count("BULLISH")
    bearish_count = signals.count("BEARISH")
    total = len(signals)
    
    if bullish_count > total * 0.5:
        final_signal = "BULLISH"
    elif bearish_count > total * 0.5:
        final_signal = "BEARISH"
    elif bullish_count > bearish_count:
        final_signal = "BULLISH"
    elif bearish_count > bullish_count:
        final_signal = "BEARISH"
    else:
        final_signal = "NEUTRAL"
    
    # 置信度
    high_count = sum(1 for r in analysis_results.values() if r and r.get("confidence") == "HIGH")
    if high_count >= len(analysis_results) * 0.5:
        confidence = "HIGH"
    elif high_count >= len(analysis_results) * 0.3:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    return final_signal, confidence


def run():
    """运行回测实验"""
    start_time = datetime.now()
    logger.info("=" * 120)
    logger.info(f"回测实验开始: {start_time.isoformat()}")
    logger.info(f"目标公司: {cfg.TARGET}")
    logger.info(f"回测时点: {[c[0] for c in cfg.CUTOFFS]} ({len(cfg.CUTOFFS)} 个)")
    logger.info("核心逻辑: 数据隔离 → 调用真实系统 → 记录结果")
    logger.info("=" * 120)

    all_periods = []
    all_snapshots: dict[str, dict[str, PriceSnapshot]] = {}
    all_rank_results: dict[str, dict[str, RankingResult]] = {}

    # 宏观经济分析（全局，调用真实模块）
    logger.info("\n📊 宏观经济分析...")
    economics = EconomicsAnalyzer()
    econ_signal = economics.analyze()
    logger.info(f"  经济周期: {econ_signal.phase.value}, 信号: {econ_signal.signal}")

    for label, cutoff in cfg.CUTOFFS:
        logger.info(f"\n{'─' * 100}")
        logger.info(f"▶ {label} (截止日 {cutoff})")
        logger.info(f"{'─' * 100}")

        # ── 步骤 1: 数据隔离 ──
        # 获取历史价格（避免前瞻偏差）
        prices = {}
        for ticker in cfg.RANKING_UNIVERSE:
            p = get_price_at_date(ticker, cutoff)
            if p:
                prices[ticker] = p

        if not prices:
            logger.warning(f"  {label}: 无价格数据，跳过")
            continue

        # 获取历史财报（90天滞后期）
        snapshots = build_all_snapshots(list(prices.keys()), cutoff, prices)

        if not snapshots:
            logger.warning(f"  {label}: 无财报快照，跳过")
            continue
        
        all_snapshots[cutoff] = snapshots

        # ── 步骤 2: 调用真实排名系统 ──
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
        
        # 检查有效数据
        valid_snapshots = {t: s for t, s in snapshots.items() if _pv(s, "ebit_ev") is not None}
        if not valid_snapshots:
            logger.warning(f"  {label}: 无有效财报数据，跳过")
            continue
        
        # 调用真实排名计算
        period_results = {}
        rank_results_for_cutoff: dict[str, RankingResult] = {}
        
        for ticker in cfg.RANKING_UNIVERSE:
            if ticker not in snapshots:
                continue
            snap = snapshots[ticker]
            ebit_ev_val = _pv(snap, "ebit_ev")
            roic_val = _pv(snap, "roic")
            peg_val = _pv(snap, "peg_ratio")
            
            if ebit_ev_val is None:
                continue

            # 调用真实的 greenblatt 排名函数（v3.2 增强版）
            rev_growth_val = _pv(snap, "revenue_growth")
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
                revenue_growth=rev_growth_val,
            )
            
            rank_results_for_cutoff[ticker] = rank_result

            # 从真实排名获取信号
            rank_signal, rank_action, rank_conviction = get_signal_from_rank(
                rank_result, snap.f_score, total
            )
            
            # ── 步骤 3: 调用真实分析模块（仅目标公司）──
            analysis_results = {}
            if ticker in cfg.TARGET:
                logger.info(f"  📈 运行分析模块 {ticker}...")
                analysis_results = run_real_analysis(ticker)
            
            # 综合信号
            final_signal, final_confidence = get_final_signal(rank_signal, analysis_results)
            
            period_results[ticker] = {
                "ticker": ticker,
                "rank": rank_result.composite_rank,
                "composite_score": round(rank_result.composite_score, 2),
                "f_score": snap.f_score,
                "rank_signal": rank_signal,
                "final_signal": final_signal,
                "final_confidence": final_confidence,
                "analysis_results": analysis_results,
            }
        
        all_rank_results[cutoff] = rank_results_for_cutoff

        # ── 步骤 4: 计算实际回报 ──
        raw_returns = compute_all_returns(cfg.TARGET, cutoff)

        # ── 步骤 5: 记录结果 ──
        for ticker in cfg.TARGET:
            pr = period_results.get(ticker, {})
            rr = raw_returns.get(ticker, {})
            
            record = {
                "period": label,
                "cutoff": cutoff,
                "ticker": ticker,
                "entry_price": rr.get("entry_price"),
                "rank": pr.get("rank"),
                "f_score": pr.get("f_score"),
                "rank_signal": pr.get("rank_signal"),
                "final_signal": pr.get("final_signal"),
                "final_confidence": pr.get("final_confidence"),
                "analysis_results": pr.get("analysis_results", {}),
                "ret_6m": rr.get("ret_6m"),
                "ret_1y": rr.get("ret_1y"),
            }
            all_periods.append(record)

            # 输出
            name = cfg.NAME_MAP.get(ticker, ticker)
            sym = "$" if ticker != "1810.HK" else "HK$"
            ep = f"{sym}{rr.get('entry_price', 'N/A')}"
            r6s = f"{rr.get('ret_6m'):+.2f}%" if rr.get("ret_6m") is not None else "N/A"
            
            # 检查方向正确性
            final_sig = pr.get("final_signal", "NEUTRAL")
            ret_6m = rr.get("ret_6m")
            if ret_6m is not None:
                if final_sig == "BULLISH" and ret_6m > 0:
                    dir_check = "✅"
                elif final_sig == "BEARISH" and ret_6m < 0:
                    dir_check = "✅"
                elif final_sig == "NEUTRAL":
                    dir_check = "➖"
                else:
                    dir_check = "❌"
            else:
                dir_check = "—"
            
            # 分析模块信号
            tech_sig = pr.get("analysis_results", {}).get("technical", {}).get("signal", "—")
            
            logger.info(
                f"  {name:6s} {ep:>10s}  "
                f"排名={pr.get('rank', 'N/A'):>5s}  "
                f"排名信号={pr.get('rank_signal', 'N/A'):>8s}  "
                f"技术={tech_sig:>8s}  "
                f"最终={final_sig:>8s}  "
                f"6m={r6s:>8s} {dir_check}"
            )

    # ── 生成报告 ──
    out_dir = RESULTS_DIR / "backtest_v2_260528"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "all_results.json", "w", encoding="utf-8") as f:
        json.dump(all_periods, f, ensure_ascii=False, indent=2, default=str)

    generate_summary(all_periods, out_dir)
    
    # 生成 HTML 报告
    from stock_analysis.backtest.backtest_report import generate_backtest_html_reports
    html_files = generate_backtest_html_reports(all_periods, all_snapshots, all_rank_results, out_dir)
    logger.info(f"  HTML 报告: {len(html_files)} 份")

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"\n{'=' * 120}")
    logger.info(f"回测完成: {elapsed:.0f}s → {out_dir}")
    logger.info(f"{'=' * 120}")
    return all_periods


def generate_summary(records: list[dict], out_dir: Path):
    """生成汇总报告"""
    lines = []
    lines.append("# 回测实验报告 v2\n")
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append(f"**目标公司**: {', '.join(cfg.NAME_MAP.get(t, t) for t in cfg.TARGET)}")
    lines.append(f"**核心逻辑**: 数据隔离 → 调用真实系统 → 记录结果\n")

    # 统计
    total = len(records)
    valid_records = [r for r in records if r.get("ret_6m") is not None]
    
    # 方向正确性
    correct = 0
    wrong = 0
    neutral = 0
    for r in valid_records:
        sig = r.get("final_signal", "NEUTRAL")
        ret = r.get("ret_6m")
        if ret is None:
            continue
        if sig == "BULLISH" and ret > 0:
            correct += 1
        elif sig == "BEARISH" and ret < 0:
            correct += 1
        elif sig == "NEUTRAL":
            neutral += 1
        else:
            wrong += 1
    
    lines.append(f"**总观测数**: {total}")
    lines.append(f"**有效观测**: {len(valid_records)} (有6月回报)")
    lines.append(f"**方向正确**: {correct}/{correct + wrong} ({correct/(correct + wrong)*100:.1f}%)" if (correct + wrong) > 0 else "")
    lines.append("")

    # 按公司分组
    for ticker in cfg.TARGET:
        name = cfg.NAME_MAP.get(ticker, ticker)
        recs = [r for r in records if r["ticker"] == ticker]
        sym = "$" if ticker != "1810.HK" else "HK$"
        lines.append(f"## {name} ({ticker})\n")
        lines.append(f"| 时点 | 买入价 | 排名 | 排名信号 | 技术 | 最终信号 | 6月实际 | 方向 |")
        lines.append(f"|------|--------|:----:|:-------:|:----:|:-------:|:-------:|:----:|")
        for r in recs:
            ep = f"{sym}{r['entry_price']:.2f}" if r.get('entry_price') else "N/A"
            r6s = f"{r['ret_6m']:+.2f}%" if r.get('ret_6m') is not None else "N/A"
            
            tech_sig = r.get("analysis_results", {}).get("technical", {}).get("signal", "—")
            final_sig = r.get("final_signal", "NEUTRAL")
            ret = r.get("ret_6m")
            
            if ret is not None:
                if final_sig == "BULLISH" and ret > 0:
                    dir_check = "✅"
                elif final_sig == "BEARISH" and ret < 0:
                    dir_check = "✅"
                elif final_sig == "NEUTRAL":
                    dir_check = "➖"
                else:
                    dir_check = "❌"
            else:
                dir_check = "—"
            
            lines.append(
                f"| {r['period']} | {ep} | {r.get('rank', 'N/A')} | "
                f"{r.get('rank_signal', 'N/A')} | {tech_sig} | {final_sig} | "
                f"{r6s} | {dir_check} |"
            )
        lines.append("")

    out_path = out_dir / "summary.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"  汇总报告: {out_path}")


if __name__ == "__main__":
    run()
