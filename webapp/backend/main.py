"""FastAPI 后端 — 投资分析 Web 应用

API 端点:
  GET  /api/rankings      — 获取当前排名数据
  GET  /api/companies     — 列出所有公司
  GET  /api/company/{ticker} — 获取公司详情
  POST /api/analyze       — 触发新分析
  GET  /api/reports       — 列出历史报告
  POST /api/refresh       — 刷新数据缓存
  WS   /ws/updates        — 实时更新推送
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stock_analysis.data.fetcher import PriceSnapshot, fetch_all_8, load_prices, sync_public_data_to_json
from stock_analysis.ranking.greenblatt import (
    apply_cross_asset_scores,
    compute_crypto_ranking,
    compute_greenblatt,
    compute_pos_crypto_ranking,
)
from stock_analysis.registry import MARKET_GROUPS, registry, ticker_to_name_zh

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webapp")

# FastAPI 应用
app = FastAPI(
    title="投资分析 API",
    description="Greenblatt 四层加权排名体系 Web API",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件 - 分析报告
ANALYSIS_DIR = PROJECT_ROOT / "分析输出"
if ANALYSIS_DIR.exists():
    app.mount("/reports", StaticFiles(directory=str(ANALYSIS_DIR)), name="reports")


# ═══════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════


class CompanyInfo(BaseModel):
    ticker: str
    name_zh: str
    name_en: str
    exchange: str
    sector: str
    market: str
    asset_category: str


class RankingData(BaseModel):
    ticker: str
    name_zh: str
    price: float
    currency: str
    market_cap: str
    score_10: float
    composite_score: float
    composite_rank: str
    l1_value: str
    l1_rank: str
    l2_value: str
    l2_rank: str
    l3_value: str
    l3_rank: str
    l4_value: str
    l4_rank: str
    asset_category: str


class AnalysisRequest(BaseModel):
    company_name: str
    dry_run: bool = False


class AnalysisResponse(BaseModel):
    status: str
    message: str
    report_path: Optional[str] = None


class RefreshResponse(BaseModel):
    status: str
    count: int
    message: str


# ═══════════════════════════════════════════════════════════
# WebSocket 管理
# ═══════════════════════════════════════════════════════════


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


# ═══════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════


def compute_rankings_for_all(prices: dict[str, PriceSnapshot]) -> dict[str, dict]:
    """为所有标的计算排名"""
    all_ebit_ev = {}
    all_roic = {}
    all_f_score = {}
    all_peg = {}

    for t, p in prices.items():
        if p.ebit_ev_num is not None:
            all_ebit_ev[t] = p.ebit_ev_num
        if p.roic_num is not None:
            all_roic[t] = p.roic_num
        if p.f_score is not None:
            all_f_score[t] = p.f_score
        if p.peg_num is not None:
            all_peg[t] = p.peg_num

    rankings = {}
    for t in prices:
        if t == "BTC":
            btc = prices.get("BTC")
            if btc and btc.mvrv_z_score:
                result = compute_crypto_ranking(
                    btc.mvrv_z_score,
                    btc.hash_rate_eh,
                    btc.f_score,
                    btc.days_since_halving,
                    {"BTC": btc.mvrv_z_score},
                    {"BTC": btc.hash_rate_eh},
                    {"BTC": btc.f_score},
                    {"BTC": btc.days_since_halving},
                )
                rankings[t] = result
        elif t in {"ETH", "SOL", "BNB"}:
            pos = prices.get(t)
            all_mcap_tvl = {k: v.mcap_tvl_ratio for k, v in prices.items() if k in {"ETH", "SOL", "BNB"} and v.mcap_tvl_ratio}
            all_staking = {k: v.staking_ratio for k, v in prices.items() if k in {"ETH", "SOL", "BNB"} and v.staking_ratio}
            all_crypto_f = {k: v.f_score for k, v in prices.items() if k in {"ETH", "SOL", "BNB"} and v.f_score}
            all_inflation = {k: v.supply_inflation for k, v in prices.items() if k in {"ETH", "SOL", "BNB"} and v.supply_inflation}
            if pos and all_mcap_tvl and all_staking and all_crypto_f and all_inflation:
                result = compute_pos_crypto_ranking(
                    t, pos.mcap_tvl_ratio, pos.staking_ratio, pos.f_score, pos.supply_inflation,
                    all_mcap_tvl, all_staking, all_crypto_f, all_inflation,
                )
                rankings[t] = result
        elif t in all_ebit_ev:
            result = compute_greenblatt(
                t, all_ebit_ev.get(t), all_roic.get(t), all_f_score.get(t), all_peg.get(t),
                all_ebit_ev, all_roic, all_f_score, all_peg,
            )
            rankings[t] = result

    # 计算跨资产统一分数
    apply_cross_asset_scores(prices, rankings)
    return rankings


def get_report_files(ticker: str) -> list[dict]:
    """获取指定公司的所有报告文件"""
    name_zh = ticker_to_name_zh().get(ticker, ticker)
    report_dir = ANALYSIS_DIR / name_zh
    if not report_dir.exists():
        return []

    reports = []
    for html_file in sorted(report_dir.glob("*.html"), reverse=True):
        stat = html_file.stat()
        reports.append({
            "filename": html_file.name,
            "path": f"/reports/{name_zh}/{html_file.name}",
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return reports


# ═══════════════════════════════════════════════════════════
# API 端点
# ═══════════════════════════════════════════════════════════


@app.get("/")
async def root():
    return {"message": "投资分析 API v1.0.0", "docs": "/docs"}


@app.get("/api/companies", response_model=list[CompanyInfo])
async def list_companies():
    """列出所有支持的公司"""
    reg = registry()
    companies = []
    for ticker, info in reg.items():
        companies.append(CompanyInfo(
            ticker=ticker,
            name_zh=info["name_zh"],
            name_en=info["name_en"],
            exchange=info["exchange"],
            sector=info["sector"],
            market=info["market"],
            asset_category=info["asset_category"].value,
        ))
    return companies


@app.get("/api/rankings", response_model=list[RankingData])
async def get_rankings(market: Optional[str] = None):
    """获取当前排名数据

    Args:
        market: 可选市场过滤 (US, HK, KR, CN, Crypto)
    """
    prices = load_prices()
    if not prices:
        raise HTTPException(status_code=404, detail="无缓存数据，请先刷新")

    rankings = compute_rankings_for_all(prices)
    name_map = ticker_to_name_zh()

    result = []
    for ticker, rank in rankings.items():
        info = prices.get(ticker)
        if not info:
            continue

        # 市场过滤
        if market:
            reg = registry()
            if reg.get(ticker, {}).get("market") != market:
                continue

        rows = rank.rows
        result.append(RankingData(
            ticker=ticker,
            name_zh=name_map.get(ticker, ticker),
            price=info.price,
            currency=info.currency,
            market_cap=info.market_cap,
            score_10=rank.score_10,
            composite_score=rank.composite_score,
            composite_rank=rank.composite_rank,
            l1_value=rows[0].value if len(rows) > 0 else "",
            l1_rank=rows[0].rank if len(rows) > 0 else "",
            l2_value=rows[1].value if len(rows) > 1 else "",
            l2_rank=rows[1].rank if len(rows) > 1 else "",
            l3_value=rows[2].value if len(rows) > 2 else "",
            l3_rank=rows[2].rank if len(rows) > 2 else "",
            l4_value=rows[3].value if len(rows) > 3 else "",
            l4_rank=rows[3].rank if len(rows) > 3 else "",
            asset_category=info.source.split("+")[0].strip() if info.source else "stock",
        ))

    # 按 score_10 降序排序
    result.sort(key=lambda x: (-x.score_10, x.ticker))
    return result


@app.get("/api/company/{ticker}")
async def get_company_detail(ticker: str):
    """获取公司详细数据"""
    prices = load_prices()
    info = prices.get(ticker)
    if not info:
        raise HTTPException(status_code=404, detail=f"未找到 {ticker} 的数据")

    name_map = ticker_to_name_zh()
    rankings = compute_rankings_for_all(prices)
    rank = rankings.get(ticker)

    # 获取报告文件
    reports = get_report_files(ticker)

    # 获取公司注册信息
    reg = registry()
    company_reg = reg.get(ticker, {})

    return {
        "ticker": ticker,
        "name_zh": name_map.get(ticker, ticker),
        "name_en": company_reg.get("name_en", ""),
        "exchange": company_reg.get("exchange", ""),
        "sector": company_reg.get("sector", ""),
        "market": company_reg.get("market", ""),
        "price": info.price,
        "currency": info.currency,
        "market_cap": info.market_cap,
        "pe_ratio": info.pe_ratio,
        "forward_pe": info.forward_pe,
        "peg_ratio": info.peg_ratio,
        "ebit_ev": info.ebit_ev,
        "roic": info.roic,
        "f_score": info.f_score,
        "fcf_yield": info.fcf_yield,
        "revenue_growth": info.revenue_growth,
        "week52_low": info.week52_low,
        "week52_high": info.week52_high,
        "beta": info.beta,
        "source": info.source,
        "ranking": {
            "score_10": rank.score_10 if rank else 0,
            "composite_score": rank.composite_score if rank else 0,
            "composite_rank": rank.composite_rank if rank else "",
            "rows": [
                {"layer": r.layer, "dimension": r.dimension, "metric": r.metric, "value": r.value, "rank": r.rank, "weight": r.weight, "verdict": r.verdict}
                for r in rank.rows
            ] if rank else [],
        },
        "reports": reports,
    }


@app.post("/api/analyze", response_model=AnalysisResponse)
async def trigger_analysis(request: AnalysisRequest):
    """触发新的分析任务"""
    # 异步运行分析
    asyncio.create_task(_run_analysis_background(request.company_name, request.dry_run))
    return AnalysisResponse(
        status="started",
        message=f"分析任务已启动: {request.company_name}",
    )


async def _run_analysis_background(company_name: str, dry_run: bool):
    """后台运行分析"""
    try:
        from stock_analysis.cli import run_analysis

        await manager.broadcast({"type": "analysis_started", "company": company_name})

        # 在线程池中运行同步分析
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: run_analysis(company_name, dry_run=dry_run))

        await manager.broadcast({
            "type": "analysis_completed",
            "company": company_name,
            "success": result is not None,
            "path": str(result) if result else None,
        })
    except Exception as e:
        logger.error(f"分析失败: {e}")
        await manager.broadcast({
            "type": "analysis_error",
            "company": company_name,
            "error": str(e),
        })


@app.get("/api/reports")
async def list_reports(ticker: Optional[str] = None):
    """列出历史报告"""
    if ticker:
        return {"reports": get_report_files(ticker)}

    # 列出所有报告
    all_reports = {}
    if ANALYSIS_DIR.exists():
        for company_dir in ANALYSIS_DIR.iterdir():
            if company_dir.is_dir():
                company_name = company_dir.name
                reports = []
                for html_file in sorted(company_dir.glob("*.html"), reverse=True):
                    stat = html_file.stat()
                    reports.append({
                        "filename": html_file.name,
                        "path": f"/reports/{company_name}/{html_file.name}",
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
                if reports:
                    all_reports[company_name] = reports
    return {"reports": all_reports}


@app.post("/api/refresh", response_model=RefreshResponse)
async def refresh_data():
    """刷新数据缓存"""
    try:
        loop = asyncio.get_event_loop()
        count = await loop.run_in_executor(None, lambda: sync_public_data_to_json(logger=logger))
        await manager.broadcast({"type": "data_refreshed", "count": count})
        return RefreshResponse(
            status="success",
            count=count,
            message=f"已刷新 {count} 家标的数据",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新失败: {str(e)}")


@app.get("/api/markets")
async def get_market_groups():
    """获取市场分组"""
    return {"markets": MARKET_GROUPS}


@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 实时更新"""
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ═══════════════════════════════════════════════════════════
# 启动
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
