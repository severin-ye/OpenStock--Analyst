<div align="center">

# 📊 股市分析

**排名优于打分。买最便宜的，不是最好的。**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version 3.2.0](https://img.shields.io/badge/version-3.2.0-green.svg)]()

[English](README.md) · [中文](README-zh.md)

</div>

---

## 它做什么

专业投资分析工具，将 **Greenblatt 排名公式**与 **9 个 AI 分析框架**结合——基于实时市场数据，零幻觉。

```bash
# 一条命令生成完整分析报告
PYTHONPATH="src" python3 -m stock_analysis.cli 英伟达
```

你能得到：
- 📊 **四层加权排名**（EBIT/EV · ROIC · F-Score · PEG）
- 🔬 **9 个分析模块**（技术 · 内部人 · 机构 · 财报 · 行业 · 宏观 · 竞争 · 叙事 · 验证）
- 📄 **专业 HTML 报告**，含 Chart.js 可视化
- 🧪 **回测系统**，验证历史预测准确性
- 🌍 **26 只标的，5 个市场**（美 · 港 · 日 · 韩 · A股 · 加密）

---

## 为什么做这个

大多数投资"AI"工具给你一个**评分**。"英伟达 8.5/10"。

**这没用。** 伟大的公司在糟糕的价格买入，就是糟糕的投资。平庸公司在跳楼价买入，可以让你暴富。

| 其他工具 | 股市分析 |
|----------|----------|
| LLM 从训练数据猜 PE | yfinance 实时抓取真实 PE |
| "英伟达评分：8.5/10" | "英伟达 EBIT/EV 排名：#2/9" |
| 单一市场、单一货币 | 美/港/日/韩/A股 + 加密，统一排名 |
| 黑盒 | 透明四层公式 |
| LLM 写全部 | LLM 只叙述；Python 算数学 |

Greenblatt 证明了：**按 EBIT/EV + ROIC 排名，跑赢 96% 的基金经理。** 不是打分。不是 vibe。纯粹、冷酷的排名。

---

## 快速开始

```bash
git clone https://github.com/severin/stock-analysis.git
cd stock-analysis
pip install -r requirements.txt

# Dry-run：抓取 + 排名，不调 LLM
PYTHONPATH="src" python3 -m stock_analysis.cli 英伟达 --dry-run

# 完整报告：抓取 → 排名 → LLM 叙述 → HTML
PYTHONPATH="src" python3 -m stock_analysis.cli 英伟达

# 回测系统：3 年历史数据验证预测准确性
PYTHONPATH="src" python3 -m stock_analysis.backtest.backtest_v2

# 本地预览看板
python3 -m http.server 8888
# → http://localhost:8888/index.html
```

---

## 排名公式

```
综合分 = L1排名 × 0.40 + L2排名 × 0.25 + L3排名 × 0.25 + L4排名 × 0.10
```

| 层级 | 维度 | 指标 | 权重 | 排序 |
|:-----:|------|------|:------:|------|
| **L1** | 💰 便不便宜 | EBIT/EV（收购者倍数） | 40% | 高 → 低 |
| **L2** | 🏭 赚不赚钱 | ROIC | 25% | 高 → 低 |
| **L3** | 🛡️ 会不会崩 | Piotroski F-Score (0-9) | 25% | 高 → 低 |
| **L4** | 📈 增长值不值 | PEG | 10% | 低 → 高 |

**v3.2 增强：**
- 增长调整 EBIT/EV：营收增速 > 30% 获得排名加成
- 健康扩张加分：ROIC > 10% + 营收增速 > 20% → F-Score +1
- 叙事分析：捕获 "AI"、"EV" 等市场主题

### 加密资产适配

| 资产 | L1 | L2 | L3 | L4 |
|------|----|----|----|-----|
| **BTC** | MVRV Z-Score | 算力 | 链上 F-Score | 减半周期 |
| **ETH/SOL/BNB** | MCap/TVL | Staking 比率 | Crypto F-Score | 年通胀率 |

---

## 分析模块（InvestSkill 集成）

9 个专业分析框架，每个可独立调用：

```python
from stock_analysis.analysis import *

# 技术分析（MTF, RSI, MACD）
tech = TechnicalAnalyzer()
signal = tech.analyze("NVDA", period="1y")

# SEC Form 4 内部人交易
insider = InsiderAnalyzer()
signal = insider.analyze("NVDA")

# SEC 13F 机构持仓
inst = InstitutionalAnalyzer()
signal = inst.analyze("NVDA")

# 财报电话会议情绪和指引
earnings = EarningsAnalyzer()
signal = earnings.analyze("NVDA")

# 行业轮动和经济周期
sector = SectorAnalyzer()
signal = sector.analyze("NVDA")

# 宏观经济：GDP、收益率曲线、美联储
economics = EconomicsAnalyzer()
signal = economics.analyze()

# Porter 五力 + 护城河
competitor = CompetitorAnalyzer()
signal = competitor.analyze("NVDA")

# AI / EV / 题材检测
narrative = NarrativeAnalyzer()
signal = narrative.analyze("1810.HK")

# 五维验证 (0-100)
validator = ResultValidator()
result = validator.validate_analysis(
    ticker="NVDA", signal="BULLISH", confidence="HIGH",
    f_score=7, composite_rank="#2/9",
)
print(f"可信度: {result.total_score}/100 ({result.tier.value})")
```

| 模块 | 数据源 | 指标 | 快速调用 |
|------|--------|:-----:|----------|
| ✅ 技术分析 | 价格 + 趋势 | MTF 0-3 | `TechnicalAnalyzer().analyze("NVDA")` |
| ✅ 内部人 | SEC Form 4 | -1 到 +1 | `InsiderAnalyzer().analyze("NVDA")` |
| ✅ 机构持仓 | SEC 13F | 积累/分发 | `InstitutionalAnalyzer().analyze("NVDA")` |
| ✅ 财报 | 指引 + 情绪 | 自信/谨慎 | `EarningsAnalyzer().analyze("NVDA")` |
| ✅ 行业 | 11 个行业 | 1-10 | `SectorAnalyzer().analyze("NVDA")` |
| ✅ 宏观 | GDP, VIX, 利差 | 鹰派/鸽派 | `EconomicsAnalyzer().analyze()` |
| ✅ 竞争 | Porter 五力 | 宽护城河/窄 | `CompetitorAnalyzer().analyze("NVDA")` |
| ✅ 叙事 | AI/EV 主题 | 强/弱 | `NarrativeAnalyzer().analyze("NVDA")` |
| ✅ 验证 | 5 个维度 | 0-100 | `ResultValidator().validate_analysis(...)` |

---

## 回测系统

用 3 年历史数据验证预测准确性：

```bash
PYTHONPATH="src" python3 -m stock_analysis.backtest.backtest_v2
```

**设计原则：** 回测不是独立系统。它隔离历史数据，然后注入真实分析流水线。

```
历史数据 → 隔离（90天财报滞后期）
        → 调用真实 greenblatt 排名
        → 调用真实分析模块
        → 记录预测 vs 实际回报
```

### 验证结果（英伟达/小米/特斯拉，6 个时点）

| 指标 | 集成前 | 集成后 |
|------|:-----:|:-----:|
| 6月方向正确率 | 23.1% | **61.5%** |
| 1年方向正确率 | 40.0% | **60.0%** |

**关键发现：** 技术分析纠正了排名错误。当基本面说"看空"但趋势说"看多"时，趋势是对的。

---

## 标的覆盖（26 家）

| 市场 | 代码 |
|------|------|
| 🇺🇸 美股 (8) | NVDA, AAPL, INTC, TSLA, AMD, MU, LLY, AVGO |
| 🇭🇰 港股 (6) | 1810.HK, 0700.HK, 9988.HK, 3690.HK, 1211.HK, 2513.HK |
| 🇯🇵 日股 (3) | 7203.T, 6758.T, 9984.T |
| 🇰🇷 韩股 (4) | 000660.KS, 005930.KS, 207940.KS, 005380.KS |
| 🇨🇳 A股 (1) | 688256.SS |
| ₿ 加密 (4) | BTC, ETH, SOL, BNB |

编辑 `data/companies.json` 添加你自己的标的。

---

## 架构

```
src/stock_analysis/
├── cli.py              # 主入口
├── batch.py            # 多公司顺序批量
├── data/
│   ├── fetcher.py      # yfinance / CoinGecko / DeFiLlama
│   └── sources.py      # 数据源矩阵
├── ranking/
│   └── greenblatt.py   # 四层加权排名（无 LLM）
├── analysis/           # InvestSkill 分析模块
│   ├── technical.py    # 多时间框架技术分析
│   ├── insider.py      # SEC Form 4 内部人交易
│   ├── institutional.py# SEC 13F 机构持仓
│   ├── earnings.py     # 财报电话会议分析
│   ├── sector.py       # 行业轮动
│   ├── economics.py    # 宏观经济
│   ├── competitor.py   # Porter 五力竞争分析
│   ├── narrative.py    # 题材和情绪检测
│   └── validator.py    # 五维可信度评分
├── backtest/           # 历史回测验证
│   ├── backtest_v2.py  # 真实系统回测
│   ├── historical_fetcher.py  # 前瞻偏差预防
│   └── returns_calculator.py  # 实际持有期回报
├── reports/
│   ├── schema.py       # Pydantic StockReport v3.0
│   ├── config.py       # LLM 配置
│   ├── templates/
│   │   └── report.jinja2  # HTML 报告模板
│   └── stages/
│       ├── scaffold.py # Stage 0: 初始化报告壳
│       ├── render.py   # Stage 4: Jinja2 → HTML
│       └── validate.py # Stage 5-6: 验证
├── registry.py         # companies.json 派生映射
├── llm_client.py       # DeepSeek/OpenAI 客户端
└── generator.py        # index.html 自动生成
```

### Web App（React + FastAPI）

```
webapp/
├── frontend/           # React + Vite (端口 5174)
│   └── src/
│       ├── pages/      # Dashboard, CompanyDetail, Analysis
│       └── components/ # RankingChart, RankingRadar
├── backend/            # FastAPI (端口 8001)
│   └── main.py         # /api/rankings, /api/companies 等
└── start.sh            # 一键启动
```

```bash
cd webapp && ./start.sh
# 前端: http://localhost:5174
# API 文档: http://localhost:8001/docs
```

---

## 反幻觉设计

LLM 从不接触原始财务数据。

```
                   ┌─────────────────┐
                   │   yfinance API  │
                   │   CoinGecko     │
                   └────────┬────────┘
                            │ 实时数据
                   ┌────────▼────────┐
                   │  Python 排名    │  ← 纯数学，无 LLM
                   │  EBIT/EV, ROIC  │
                   │  F-Score, PEG   │
                   └────────┬────────┘
                            │ 预计算数据块
                   ┌────────▼────────┐
                   │      LLM        │  ← 只写叙述
                   │  "英伟达在排名  │
                   │   中领先。"     │
                   └────────┬────────┘
                            │
                   ┌────────▼────────┐
                   │  Jinja2 → HTML  │
                   └─────────────────┘
```

LLM 接收结构化数据块，如 *"英伟达: EBIT/EV=2.52%, ROIC=90.55%, F-Score=7/9, 排名=#2/9"*，然后围绕它们写叙述。**它无法幻觉数字，因为它从不生成数字。**

---

## 报告输出

每次分析生成专业的 8 节 HTML 报告：

| 章节 | 内容 |
|------|------|
| 封面 | KPI 条、价格、市值、YTD 变动 |
| S1 | 涨跌比例总览、核心判断 |
| S2 | 公司/资产概览 |
| S3 | 1年走势图 + 均线叠加 |
| S4 | 竞争格局 |
| S5 | 估值：排名表、F-Score 卡、DCF、雷达图 |
| S6 | 未来情景（悲观/基准/乐观） |
| S7 | 风险矩阵 |
| S8 | 投资信号块（看多/中性/看空） |

---

## 开发

```bash
pip install -r requirements-dev.txt

# 代码检查
ruff check src/stock_analysis/

# 类型检查
mypy src/stock_analysis/ --exclude tests --ignore-missing-imports

# 测试
PYTHONPATH="src" pytest tests/ -v

# 分析模块测试
PYTHONPATH="src" python3 tests/test_analysis.py
```

---

## 哲学

我们在那些**猜**财务数据的 LLM 工具上花了无数钱。它们告诉我们 AAPL 的 PE 是 28，实际是 31。它们把 NVDA 排"#1"因为它是伟大的公司——无视价格已经计入了完美预期。

**这个工具只做一件事：告诉你现在什么便宜。** 不是什么是好的。不是什么会增长。什么是便宜的。

Greenblatt 的公式不性感。它不预测未来。但它跑赢 96% 的基金经理，因为大多数投资者以糟糕的价格买入伟大的公司。

不要做大多数投资者。

---

## 许可证

MIT。详见 [LICENSE](LICENSE)。
