"""回测主引擎: 遍历时点 → 构建历史快照 → 排名 → 计算回报 → 对比"""

import json
import logging
from datetime import datetime
from pathlib import Path

from stock_analysis.backtest import config as cfg
from stock_analysis.backtest.historical_fetcher import build_all_snapshots, get_price_at_date
from stock_analysis.backtest.returns_calculator import compute_all_returns
from stock_analysis.data.fetcher import PriceSnapshot
from stock_analysis.ranking.greenblatt import compute_greenblatt

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


def _to_ebit_ev_pct(val):
    if val is None:
        return None
    return val  # Already a percentage value in decimal


def signal_from_rank(rank_str: str, f_score: int | None, total: int) -> tuple[str, str]:
    """根据排名判定信号 + 方向"""
    try:
        rank_num = int(rank_str.split("/")[0].replace("#", ""))
    except (ValueError, IndexError, AttributeError):
        return ("UNKNOWN", "未知")

    if f_score is not None and f_score <= 3:
        return ("AVOID", "看空")

    if rank_num <= max(1, total // 3):
        return ("BUY", "看涨")
    elif rank_num <= max(2, total * 2 // 3):
        return ("HOLD", "中性")
    else:
        return ("AVOID", "看空")


def check_deviation(signal: str, ret: float | None) -> str:
    if ret is None:
        return "—"
    if signal == "BUY":
        return "✅正确" if ret > 5 else ("❌错误" if ret < -5 else "➖持平")
    if signal == "AVOID":
        return "✅正确" if ret < -5 else ("❌错误" if ret > 5 else "➖持平")
    return f"➖中性({ret:+.0f}%)"


def run():
    start_time = datetime.now()
    logger.info("=" * 120)
    logger.info(f"回测实验开始: {start_time.isoformat()}")
    logger.info(f"目标公司: {cfg.TARGET}")
    logger.info(f"排名对照组: {cfg.RANKING_UNIVERSE} ({len(cfg.RANKING_UNIVERSE)} 家)")
    logger.info(f"回测时点: {[c[0] for c in cfg.CUTOFFS]}")
    logger.info("=" * 120)

    all_periods = []

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
        logger.info(f" 排名公司数: {total} (有 EBIT/EV)")

        # 4. 对每个目标公司计算排名
        period_results = {}
        for ticker in cfg.RANKING_UNIVERSE:
            if ticker not in snapshots:
                continue
            snap = snapshots[ticker]
            ebit_ev_val = _pv(snap, "ebit_ev")
            roic_val = _pv(snap, "roic")
            peg_val = _pv(snap, "peg_ratio")

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

            sig, dir_str = signal_from_rank(rank_result.composite_rank, snap.f_score, total)
            period_results[ticker] = {
                "ticker": ticker,
                "rank": rank_result.composite_rank,
                "composite_score": round(rank_result.composite_score, 2),
                "score_10": rank_result.score_10,
                "f_score": snap.f_score,
                "signal": sig,
                "direction": dir_str,
            }

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
            d6 = check_deviation(sig, ret_6m)
            d1 = check_deviation(sig, ret_1y)

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
                "ret_6m": ret_6m,
                "deviation_6m": d6,
                "ret_1y": ret_1y,
                "deviation_1y": d1,
            }
            period_records.append(record)

            name = cfg.NAME_MAP.get(ticker, ticker)
            sym = "$" if ticker != "1810.HK" else "HK$"
            ep = f"{sym}{rr.get('entry_price', 'N/A')}"
            r6s = f"{ret_6m:+.2f}%" if ret_6m is not None else "N/A"
            r1s = f"{ret_1y:+.2f}%" if ret_1y is not None else "N/A"
            logger.info(
                f"  {name:6s} {ep:>10s}  "
                f"排名={pr.get('rank', 'N/A'):>5s}  "
                f"信号={sig:>6s}({pr.get('direction',''):2s})  "
                f"实际:6m={r6s} {d6}  "
                f"1y={r1s} {d1}"
            )

        all_periods.extend(period_records)

    # ── 生成汇总 ──
    out_dir = RESULTS_DIR / "backtest_260527"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "all_results.json", "w", encoding="utf-8") as f:
        json.dump(all_periods, f, ensure_ascii=False, indent=2)

    # 生成 summary.md
    generate_summary(all_periods, out_dir)

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"\n{'=' * 120}")
    logger.info(f"回测完成: {elapsed:.0f}s → {out_dir}")
    logger.info(f"{'=' * 120}")
    return all_periods


def generate_summary(records: list[dict], out_dir: Path):
    lines = []
    lines.append("# 回测实验报告\n")
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append(f"**目标公司**: {', '.join(cfg.NAME_MAP.get(t, t) for t in cfg.TARGET)}")
    lines.append(f"**排名对照组**: {len(cfg.RANKING_UNIVERSE)} 家（含{cfg.NAME_MAP.get('1810.HK','小米')}混入美股）")
    lines.append("**PEG 近似**: trailingPE / 收入增速\n")

    # 统计
    total = len(records)
    buy = sum(1 for r in records if r["signal"] == "BUY")
    hold = sum(1 for r in records if r["signal"] == "HOLD")
    avoid = sum(1 for r in records if r["signal"] == "AVOID")

    correct_6m = sum(1 for r in records if "✅" in (r.get("deviation_6m") or ""))
    wrong_6m = sum(1 for r in records if "❌" in (r.get("deviation_6m") or ""))
    correct_1y = sum(1 for r in records if "✅" in (r.get("deviation_1y") or ""))
    wrong_1y = sum(1 for r in records if "❌" in (r.get("deviation_1y") or ""))

    lines.append(f"**总观测数**: {total}（BUY={buy}, HOLD={hold}, AVOID={avoid}）")
    if (correct_6m + wrong_6m) > 0:
        pct_6m = correct_6m / (correct_6m + wrong_6m) * 100
        lines.append(f"**6 月正确率**: {correct_6m}/{correct_6m + wrong_6m}（{pct_6m:.0f}%）")
    else:
        lines.append("")
    if (correct_1y + wrong_1y) > 0:
        pct_1y = correct_1y / (correct_1y + wrong_1y) * 100
        lines.append(f"**1 年正确率**: {correct_1y}/{correct_1y + wrong_1y}（{pct_1y:.0f}%）")
    else:
        lines.append("")
    lines.append("")

    # 按公司分组
    for ticker in cfg.TARGET:
        name = cfg.NAME_MAP.get(ticker, ticker)
        recs = [r for r in records if r["ticker"] == ticker]
        sym = "$" if ticker != "1810.HK" else "HK$"
        lines.append(f"## {name} ({ticker})\n")
        lines.append("| 时点 | 买入价 | 排名 | 综合分 | F | 信号 | 6月实际 | 偏差 | 1年实际 | 偏差 |")
        lines.append("|------|--------|:----:|:-----:|:-:|:----:|:-------:|:----:|:-------:|:----:|")
        for r in recs:
            ep = f"{sym}{r['entry_price']}" if r['entry_price'] else "N/A"
            r6s = f"{r['ret_6m']:+.2f}%" if r['ret_6m'] is not None else "N/A"
            r1s = f"{r['ret_1y']:+.2f}%" if r['ret_1y'] is not None else "N/A"
            lines.append(
                f"| {r['period']} | {ep} | {r['rank'] or 'N/A'} | "
                f"{r['composite_score'] or '—'} | {r['f_score'] or '—'} | "
                f"{r['signal']} | "
                f"{r6s} | {r.get('deviation_6m','—')} | "
                f"{r1s} | {r.get('deviation_1y','—')} |"
            )
        lines.append("")

    # 关键发现
    lines.append("## 关键发现\n")
    lines.append("- ✅ 绿色(正确): 信号与实际方向一致")
    lines.append("- ❌ 红色(错误): 实际与信号方向相反")
    lines.append("- ➖ 中性: HOLD/持平, 记录实际数值供参考")
    lines.append("- 小米混入美股排名, 统一公式")
    lines.append("- INTC(英特尔) 预期看跌, 实际排名往往靠后")
    lines.append("")

    out_path = out_dir / "summary.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"  汇总报告: {out_path}")


if __name__ == "__main__":
    run()
