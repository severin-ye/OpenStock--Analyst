<div align="center">

# 📊 Stock Analysis

**Rank, don't score. Buy the cheapest, not the best.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version 3.2.0](https://img.shields.io/badge/version-3.2.0-green.svg)]()

[English](README.md) · [中文](README-zh.md)

</div>

---

## What It Does

A professional investment analysis toolkit that combines **Greenblatt's ranking formula** with **9 AI-powered analysis frameworks** — all backed by real-time market data, zero hallucination.

```bash
# One command for a full analysis report
PYTHONPATH="src" python3 -m stock_analysis.cli NVIDIA
```

You get:
- 📊 **Four-layer weighted ranking** (EBIT/EV · ROIC · F-Score · PEG)
- 🔬 **9 analysis modules** (Technical · Insider · Institutional · Earnings · Sector · Economics · Competitor · Narrative · Validator)
- 📄 **Professional HTML report** with Chart.js visualizations
- 🧪 **Backtesting system** to validate prediction accuracy against historical data
- 🌍 **26 assets across 5 markets** (US · HK · JP · KR · CN · Crypto)

---

## Why This Exists

Most investment "AI" tools give you a **score**. "NVDA is 8.5/10."

**This is useless.** A great company at a terrible price is a terrible investment. A mediocre company at a firesale price can make you rich.

| Other Tools | Stock Analysis |
|-------------|----------------|
| LLM guesses PE ratios from training data | yfinance fetches real PE in real-time |
| "NVDA score: 8.5/10" | "NVDA rank: #2/9 on EBIT/EV" |
| Single market, single currency | US/HK/JP/KR/CN + Crypto, unified |
| Black box | Transparent four-layer formula |
| LLM writes everything | LLM only narrates; Python does the math |

Greenblatt proved it: **ranking by EBIT/EV + ROIC outperforms 96% of fund managers.** Not scoring. Not vibes. Pure, cold ranking.

---

## Quick Start

```bash
git clone https://github.com/severin/stock-analysis.git
cd stock-analysis
pip install -r requirements.txt

# Dry-run: fetch + rank, no LLM
PYTHONPATH="src" python3 -m stock_analysis.cli NVIDIA --dry-run

# Full report: fetch → rank → LLM narrates → HTML
PYTHONPATH="src" python3 -m stock_analysis.cli NVIDIA

# Backtest the system against 3 years of history
PYTHONPATH="src" python3 -m stock_analysis.backtest.backtest_v2

# View the dashboard
python3 -m http.server 8888
# → http://localhost:8888/index.html
```

---

## The Ranking Formula

```
Composite = L1_rank × 0.40 + L2_rank × 0.25 + L3_rank × 0.25 + L4_rank × 0.10
```

| Layer | Dimension | Metric | Weight | Sort |
|:-----:|-----------|--------|:------:|------|
| **L1** | 💰 Is it cheap? | EBIT/EV (Acquirer's Multiple) | 40% | High → Low |
| **L2** | 🏭 Is it profitable? | ROIC | 25% | High → Low |
| **L3** | 🛡️ Will it crash? | Piotroski F-Score (0-9) | 25% | High → Low |
| **L4** | 📈 Is growth cheap? | PEG | 10% | Low → High |

**v3.2 enhancements:**
- Growth-adjusted EBIT/EV: revenue growth > 30% gets a ranking bonus
- Healthy expansion bonus: ROIC > 10% + revenue growth > 20% → F-Score +1
- Narrative analysis: captures "AI", "EV", and other market themes

### Crypto Adaptation

| Asset | L1 | L2 | L3 | L4 |
|-------|----|----|----|-----|
| **BTC** | MVRV Z-Score | Hash Rate | On-chain F-Score | Halving Cycle |
| **ETH/SOL/BNB** | MCap/TVL | Staking Ratio | Crypto F-Score | Inflation |

---

## Analysis Modules (InvestSkill Integration)

Nine professional analysis frameworks, each independently callable:

```python
from stock_analysis.analysis import *

# Technical analysis (MTF, RSI, MACD)
tech = TechnicalAnalyzer()
signal = tech.analyze("NVDA", period="1y")

# SEC Form 4 insider trading
insider = InsiderAnalyzer()
signal = insider.analyze("NVDA")

# SEC 13F institutional ownership
inst = InstitutionalAnalyzer()
signal = inst.analyze("NVDA")

# Earnings call sentiment and guidance
earnings = EarningsAnalyzer()
signal = earnings.analyze("NVDA")

# Sector rotation and economic cycle
sector = SectorAnalyzer()
signal = sector.analyze("NVDA")

# Macro: GDP, yield curve, Fed stance
economics = EconomicsAnalyzer()
signal = economics.analyze()

# Porter's Five Forces and moat
competitor = CompetitorAnalyzer()
signal = competitor.analyze("NVDA")

# AI / EV / theme detection
narrative = NarrativeAnalyzer()
signal = narrative.analyze("1810.HK")

# Five-dimension validation (0-100)
validator = ResultValidator()
result = validator.validate_analysis(
    ticker="NVDA", signal="BULLISH", confidence="HIGH",
    f_score=7, composite_rank="#2/9",
)
print(f"Confidence: {result.total_score}/100 ({result.tier.value})")
```

| Module | Source | Score | Quick Check |
|--------|--------|:-----:|-------------|
| ✅ Technical | Price + Trends | MTF 0-3 | `TechnicalAnalyzer().analyze("NVDA")` |
| ✅ Insider | SEC Form 4 | -1 to +1 | `InsiderAnalyzer().analyze("NVDA")` |
| ✅ Institutional | SEC 13F | Accum/Distrib | `InstitutionalAnalyzer().analyze("NVDA")` |
| ✅ Earnings | Guidance + Tone | CONFIDENT/CAUTIOUS | `EarningsAnalyzer().analyze("NVDA")` |
| ✅ Sector | 11 Sectors | 1-10 | `SectorAnalyzer().analyze("NVDA")` |
| ✅ Economics | GDP, VIX, Yield | HAWKISH/DOVISH | `EconomicsAnalyzer().analyze()` |
| ✅ Competitor | Porter 5 Forces | WIDE/NARROW | `CompetitorAnalyzer().analyze("NVDA")` |
| ✅ Narrative | AI/EV Theme | STRONG/WEAK | `NarrativeAnalyzer().analyze("NVDA")` |
| ✅ Validator | 5 Dimensions | 0-100 | `ResultValidator().validate_analysis(...)` |

---

## Backtesting System

Validate prediction accuracy against 3 years of historical data:

```bash
PYTHONPATH="src" python3 -m stock_analysis.backtest.backtest_v2
```

**Design principle:** The backtest is NOT a separate system. It isolates historical data, then feeds it into the real analysis pipeline.

```
Historical Data → Isolate (90-day reporting lag)
              → Call real greenblatt ranking
              → Call real analysis modules
              → Record predictions vs actual returns
```

### Validation Results (NVDA / 1810.HK / TSLA, 6 timepoints)

| Metric | Before Integration | After Integration | 
|--------|:-----------------:|:-----------------:|
| 6-month direction accuracy | 23.1% | **61.5%** |
| 1-year direction accuracy | 40.0% | **60.0%** |

**Key finding:** Technical analysis corrected ranking errors. When fundamentals said "BEARISH" but trend said "BULLISH", the trend was right.

---

## Asset Coverage (26 Companies)

| Market | Tickers |
|--------|---------|
| 🇺🇸 US (8) | NVDA, AAPL, INTC, TSLA, AMD, MU, LLY, AVGO |
| 🇭🇰 HK (6) | 1810.HK, 0700.HK, 9988.HK, 3690.HK, 1211.HK, 2513.HK |
| 🇯🇵 JP (3) | 7203.T, 6758.T, 9984.T |
| 🇰🇷 KR (4) | 000660.KS, 005930.KS, 207940.KS, 005380.KS |
| 🇨🇳 CN (1) | 688256.SS |
| ₿ Crypto (4) | BTC, ETH, SOL, BNB |

Edit `data/companies.json` to add your own.

---

## Architecture

```
src/stock_analysis/
├── cli.py              # Main entry point
├── batch.py            # Sequential multi-company batch
├── data/
│   ├── fetcher.py      # yfinance / CoinGecko / DeFiLlama
│   └── sources.py      # Data source matrix
├── ranking/
│   └── greenblatt.py   # Four-layer weighted ranking (no LLM)
├── analysis/           # InvestSkill modules
│   ├── technical.py    # Multi-timeframe technical analysis
│   ├── insider.py      # SEC Form 4 insider trading
│   ├── institutional.py# SEC 13F ownership
│   ├── earnings.py     # Earnings call analysis
│   ├── sector.py       # Sector rotation
│   ├── economics.py    # Macroeconomic analysis
│   ├── competitor.py   # Porter's Five Forces
│   ├── narrative.py    # Theme and sentiment detection
│   └── validator.py    # Five-dimension confidence scoring
├── backtest/           # Historical validation
│   ├── backtest_v2.py  # Real-system backtesting
│   ├── historical_fetcher.py  # Look-ahead bias prevention
│   └── returns_calculator.py  # Actual holding period returns
├── reports/
│   ├── schema.py       # Pydantic StockReport v3.0
│   ├── config.py       # LLM configuration
│   ├── templates/
│   │   └── report.jinja2  # HTML report template
│   └── stages/
│       ├── scaffold.py # Stage 0: initialize report shell
│       ├── render.py   # Stage 4: Jinja2 → HTML
│       └── validate.py # Stage 5-6: schema + HTML validation
├── registry.py         # Company registry from companies.json
├── llm_client.py       # DeepSeek/OpenAI client
└── generator.py        # index.html auto-generator
```

### MCP Server (Model Context Protocol)

```
src/stock_analysis/mcp/
├── __init__.py         # MCP 服务器模块
├── __main__.py         # 入口点
├── server.py           # MCP 服务器主入口
├── tools/              # 工具实现
│   ├── analysis.py     # 分析工具 (技术分析、内部人交易等)
│   ├── ranking.py      # 排名计算工具
│   ├── data.py         # 数据获取工具
│   └── report.py       # 报告生成工具
├── resources/          # 资源实现
│   ├── companies.py    # 公司数据资源
│   ├── prices.py       # 价格数据资源
│   └── reports.py      # 报告资源
└── prompts/            # 提示模板
    ├── analysis.py     # 分析提示模板
    └── report.py       # 报告生成提示模板
```

```bash
# 启动 MCP 服务器 (stdio 传输)
PYTHONPATH="src" python3 -m stock_analysis.mcp

# 启动 MCP 服务器 (HTTP 传输)
PYTHONPATH="src" python3 -m stock_analysis.mcp --transport streamable-http --port 8000

# 使用 stock-analysis-mcp 命令
stock-analysis-mcp
```

#### MCP 工具 (Tools)

| 工具 | 功能 | 参数 |
|------|------|------|
| `technical_analysis` | 技术分析 | `ticker`, `period` |
| `insider_analysis` | 内部人交易分析 | `ticker` |
| `institutional_analysis` | 机构持仓分析 | `ticker` |
| `earnings_analysis` | 财报分析 | `ticker` |
| `sector_analysis` | 行业分析 | `ticker` |
| `economics_analysis` | 宏观经济分析 | 无参数 |
| `competitor_analysis` | 竞争分析 | `ticker` |
| `narrative_analysis` | 叙事分析 | `ticker` |
| `validate_analysis` | 验证分析结果 | `ticker`, `signal`, `confidence`, `f_score`, `composite_rank` |
| `full_analysis` | 完整分析 | `ticker`, `analysis_type` |
| `calculate_ranking` | 计算排名 | `ticker` |
| `get_rankings` | 获取排名列表 | `market`, `limit` |
| `compare_rankings` | 比较排名 | `tickers` |
| `refresh_data` | 刷新数据 | `ticker` (可选) |
| `get_price_data` | 获取价格数据 | `ticker`, `period` |
| `get_financial_data` | 获取财务数据 | `ticker` |
| `get_market_data` | 获取市场数据 | `market` |
| `generate_report` | 生成报告 | `ticker`, `report_type`, `output_dir` |
| `list_reports` | 列出报告 | `ticker` (可选) |

#### MCP 资源 (Resources)

| 资源 URI | 功能 |
|----------|------|
| `companies://list` | 获取所有公司列表 |
| `companies://{ticker}` | 获取特定公司信息 |
| `companies://market/{market}` | 获取特定市场的公司 |
| `companies://search/{query}` | 搜索公司 |
| `prices://{ticker}` | 获取价格数据 |
| `prices://all` | 获取所有价格数据 |
| `prices://market/{market}` | 获取市场价格数据 |
| `reports://list` | 获取所有报告列表 |
| `reports://{ticker}` | 获取特定公司报告 |
| `reports://{ticker}/{filename}` | 获取报告内容 |

#### MCP 提示 (Prompts)

| 提示 | 功能 | 参数 |
|------|------|------|
| `stock_analysis_prompt` | 股票分析提示 | `ticker`, `analysis_depth` |
| `comparison_prompt` | 公司对比提示 | `ticker1`, `ticker2` |
| `sector_analysis_prompt` | 行业分析提示 | `sector` |
| `risk_assessment_prompt` | 风险评估提示 | `ticker` |
| `report_generation_prompt` | 报告生成提示 | `ticker`, `report_type` |
| `batch_report_prompt` | 批量报告提示 | `tickers` |
| `report_update_prompt` | 报告更新提示 | `ticker`, `existing_report` |

#### Claude Desktop 配置

```json
{
  "mcpServers": {
    "stock-analysis": {
      "command": "python",
      "args": ["-m", "stock_analysis.mcp"],
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

### Web App (React + FastAPI)

```
webapp/
├── frontend/           # React + Vite (port 5174)
│   └── src/
│       ├── pages/      # Dashboard, CompanyDetail, Analysis
│       └── components/ # RankingChart, RankingRadar
├── backend/            # FastAPI (port 8001)
│   └── main.py         # /api/rankings, /api/companies, etc.
└── start.sh            # One-click launch
```

```bash
cd webapp && ./start.sh
# Frontend: http://localhost:5174
# API docs: http://localhost:8001/docs
```

---

## Anti-Hallucination Design

The LLM never sees raw financial data. Period.

```
                   ┌─────────────────┐
                   │   yfinance API  │
                   │   CoinGecko     │
                   └────────┬────────┘
                            │ real-time data
                   ┌────────▼────────┐
                   │  Python Ranking │  ← pure math, no LLM
                   │  EBIT/EV, ROIC  │
                   │  F-Score, PEG   │
                   └────────┬────────┘
                            │ pre-computed blocks
                   ┌────────▼────────┐
                   │      LLM        │  ← only writes narrative
                   │  "NVDA leads    │
                   │   our ranking." │
                   └────────┬────────┘
                            │
                   ┌────────▼────────┐
                   │  Jinja2 → HTML  │
                   └─────────────────┘
```

The LLM receives structured data blocks like *"NVDA: EBIT/EV=2.52%, ROIC=90.55%, F-Score=7/9, Rank=#2/9"* and writes narrative around them. **It cannot hallucinate numbers because it never generates them.**

---

## Report Output

Each analysis produces a professional 8-section HTML report:

| Section | Content |
|---------|---------|
| Cover | KPI strip, price, market cap, YTD change |
| S1 | Price change overview, core judgment |
| S2 | Company/asset overview |
| S3 | 1-year price chart with MA overlay |
| S4 | Competitive landscape |
| S5 | Valuation: ranking table, F-Score card, DCF, radar chart |
| S6 | Forward scenarios (bull/base/bear) |
| S7 | Risk matrix |
| S8 | Investment signal block (BULLISH/NEUTRAL/BEARISH) |

---

## Development

```bash
pip install -r requirements-dev.txt

# Lint
ruff check src/stock_analysis/

# Type check
mypy src/stock_analysis/ --exclude tests --ignore-missing-imports

# Test
PYTHONPATH="src" pytest tests/ -v

# Analysis modules test
PYTHONPATH="src" python3 tests/test_analysis.py
```

---

## Philosophy

We spent money on LLM tools that **guessed** financial data. They'd tell us AAPL's PE was 28 when it was 31. They'd rank NVDA "#1" because it's a great company — ignoring that the price already priced in perfection.

**This tool does one thing: tells you what's cheap right now.** Not what's good. Not what will grow. What's cheap.

Greenblatt's formula isn't sexy. It doesn't predict the future. But it beats 96% of fund managers because most investors buy great companies at terrible prices.

Don't be most investors.

---

## License

MIT. See [LICENSE](LICENSE).
