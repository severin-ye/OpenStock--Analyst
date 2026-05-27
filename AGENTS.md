# 股市分析 — Agent 指令

**版本**: 3.0.1 | **更新**: 2026-05-27

本项目提供 **CLI 工具**（主入口）和 **Web App**（可视化前端）两套架构。

## 核心引擎（CLI 工具）

```
股市分析/
├── data/
│   ├── companies.json          ← 26家公司注册表 (Single Source of Truth)
│   └── prices.json.example     ← 缓存格式示例
├── src/
│   ├── stock_analysis/         ← 核心引擎 (全部 Python 运行时)
│   │   ├── cli.py              ← 主入口: scaffold→fetch→rank→LLM→render→validate
│   │   ├── batch.py            ← 多公司顺序批量分析
│   │   ├── data/
│   │   │   ├── fetcher.py      ← yfinance / CoinGecko / DeFiLlama
│   │   │   ├── sources.py      ← 数据源矩阵
│   │   │   └── prices.json     ← 26家公司缓存 (yfinance + CoinGecko 写入)
│   │   ├── ranking/
│   │   │   └── greenblatt.py   ← 四层加权排名 (纯数学, 无 LLM)
│   │   ├── reports/
│   │   │   ├── schema.py       ← Pydantic StockReport v3.0
│   │   │   ├── config.py       ← LLM 配置 (读取 opencode.jsonc)
│   │   │   ├── templates/
│   │   │   │   └── report.jinja2 ← Jinja2 报告模板
│   │   │   └── stages/
│   │   │       ├── scaffold.py ← Stage 0: 识别公司、初始化报告壳
│   │   │       ├── render.py   ← Stage 4: Jinja2 → HTML
│   │   │       └── validate.py ← Stage 5-6: schema + HTML + 数据真实性验证
│   │   ├── registry.py         ← 从 companies.json 派生所有映射
│   │   ├── llm_client.py       ← DeepSeek/OpenAI 客户端
│   │   └── generator.py        ← index.html 自动生成器
│   └── investskill/            ← 方法论层 (上游开源, prompts + 21 skills)
├── tests/                      ← pytest
├── 分析输出/                    ← 报告输出目录
├── index.html                  ← 排名总览 (自动生成)
└── webapp/                     ← Web App 前端 (见下方)
```

### Pipeline 执行流程

```
Stage 0:   scaffold  → 识别公司、初始化 StockReport 壳
Stage 0.5: refresh   → 自动刷新 prices.json (yfinance + CoinGecko/DeFiLlama)
Stage 1:   fetch     → 从 JSON 缓存加载多市场真实数据
Stage 2:   rank      → 纯 Python 计算四层排名 (greenblatt.py, 无 LLM)
Stage 3:   LLM       → 注入真实数据 + 预计算排名, LLM 仅生成叙述文本
Stage 4:   render    → Jinja2 模板 → HTML
Stage 5:   validate  → schema + HTML 结构 + 数据真实性交叉验证
Stage 6:   index     → 重建 index.html 排名总览
```

**反幻觉设计**: LLM 从不直接接触原始财务数据。所有数值由 yfinance/公开 API 预计算后注入 prompt，LLM 只写叙述。

### 核心命令

#### 安装（首次使用）

```bash
# 进入项目目录
cd /home/severin/Codelib/股市分析

# 激活虚拟环境
source .venv/bin/activate

# 安装项目（包含 stock-analysis 命令）
pip install -e .
```

#### 使用方式

```bash
# 方式 1: 使用 stock-analysis 命令（推荐，需先安装）
stock-analysis <公司中文名>

# 方式 2: 使用 python3 -m（无需安装，需设置 PYTHONPATH）
PYTHONPATH="src" python3 -m stock_analysis.cli <公司中文名>
```

#### 常用命令

```bash
# 完整分析
stock-analysis <公司中文名>

# Dry-run（fetch + rank，不调用 LLM）
stock-analysis <公司中文名> --dry-run

# 顺序批量分析
stock-analysis batch <公司1> <公司2> <公司3> ...

# 重新生成 index.html 排名总览
stock-analysis index

# 验证 HTML 报告
stock-analysis validate <报告路径>
```

### 开发命令

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
PYTHONPATH="src" pytest tests/ -v

# 代码检查
ruff check src/stock_analysis/

# 类型检查
mypy src/stock_analysis/ --exclude tests --ignore-missing-imports
```

## Web App（可视化前端）

### 架构

```
webapp/
├── backend/
│   ├── main.py             ← FastAPI API (端口 8001)
│   ├── supermemory.py      ← 持久化记忆存储
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/          ← Dashboard, CompanyDetail, Analysis, Reports
│   │   ├── components/     ← Layout, RankingChart, RankingRadar
│   │   ├── hooks/useApi.ts ← 数据获取 hooks
│   │   └── lib/api.ts      ← API 客户端
│   ├── vite.config.ts
│   └── package.json
└── start.sh                ← 一键启动脚本
```

### 端口

- **前端**: 5174 (3000/5173 已被占用)
- **后端**: 8001
- **API 文档**: http://localhost:8001/docs

### 启动命令

```bash
# 一键启动
cd webapp && ./start.sh

# 分别启动
cd webapp/backend && PYTHONPATH="../../src" python3 main.py
cd webapp/frontend && npm run dev

# 安装依赖
cd webapp/frontend && npm install
pip install fastapi uvicorn[standard] websockets
```

### 与核心引擎关系

- 后端复用 `src/stock_analysis/` 的 fetcher、ranking、cli 模块
- 报告存储读取 `分析输出/` 目录
- 前端通过 `/api/*` 代理到后端
- `PYTHONPATH` 必须包含 `../../src`（从 webapp/backend/ 目录）

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/rankings` | 排名数据，支持 `?market=US/HK/KR/CN/Crypto` |
| GET | `/api/companies` | 公司列表 |
| GET | `/api/company/{ticker}` | 公司详情 |
| POST | `/api/analyze` | 触发分析 |
| GET | `/api/reports` | 历史报告 |
| POST | `/api/refresh` | 刷新缓存 |
| WS | `/ws/updates` | 实时推送 |

### 前端路由

| 路径 | 页面 |
|------|------|
| `/` | 排名总览 Dashboard |
| `/company/{ticker}` | 公司详情 |
| `/analysis` | 交互式分析 |
| `/reports` | 历史报告 |

## 公司注册表

**`data/companies.json`** 是唯一公司数据源。

当前 26 家标的:

| 市场 | 标的 |
|:---|:---|
| 🇺🇸 美股 (8) | 英伟达 NVDA, 苹果 AAPL, 英特尔 INTC, 特斯拉 TSLA, AMD, 美光 MU, 礼来 LLY, 博通 AVGO |
| 🇭🇰 港股 (6) | 小米 1810.HK, 腾讯 0700.HK, 阿里巴巴 9988.HK, 美团 3690.HK, 比亚迪 1211.HK, 智谱 2513.HK |
| 🇯🇵 日股 (3) | 丰田 7203.T, 索尼 6758.T, 软银集团 9984.T |
| 🇰🇷 韩股 (4) | SK海力士 000660.KS, 三星电子 005930.KS, 三星生物制药 207940.KS, 现代汽车 005380.KS |
| 🇨🇳 A股 (1) | 寒武纪 688256.SS |
| ₿ 加密 (4) | 比特币 BTC, 以太坊 ETH, 索拉纳 SOL, BNB |

## 评分体系（四层加权排名 v3.0）

| Layer | 维度 | 主指标 | 权重 | 用法 |
|-------|------|--------|:---:|------|
| **L1** | 💰 便不便宜 | **EBIT/EV** | **40%** | 从高到低排名 |
| **L2** | 🏭 赚不赚钱 | **ROIC** | **25%** | 从高到低排名 |
| **L3** | 🛡️ 会不会崩 | **Piotroski F-Score (0-9)** | **25%** | 从高到低排名 |
| **L4** | 📈 增长值不值 | **PEG** | **10%** | 从低到高排名 |

```
综合分 = L1排名×0.40 + L2排名×0.25 + L3排名×0.25 + L4排名×0.10
综合排名 = 综合分从小到大排序 (越小越好)
```

### 特殊情况

- **加密货币（BTC）**: L1 MVRV Z-Score, L2 算力+网络强度, L3 改编版 F-Score, L4 减半周期
- **PoS 加密（ETH/SOL/BNB）**: L1 MCap/TVL, L2 Staking 比率, L3 Crypto F-Score, L4 年通胀率
- **港股/日股/韩股/A股**: 同一公式，币种标注差异

### 输出格式

- 四层排名表 + 权重 + 加权分
- Piotroski F-Score 明细卡 (9 项逐项打分)
- 投资信号块 + 综合分 + 综合排名
- HTML 报告: 8 节 (S1-S8) + verdict

### score_10 辅助指标说明

`score_10` 是将综合排名转换为 1-10 分制的**辅助指标**，用于：
- 提供更直观的分数展示（便于用户理解）
- 在 batch 模式中用于排序（当排名相同时）
- **非主要排名依据** — 主要排名依据是 `composite_rank`（综合排名）

**原则**：排名优于打分。`composite_rank` 是主要指标，`score_10` 仅作辅助参考。

## 🚨 防降级规则

市场支持状态**只影响数据源选择和缺失字段披露**，**不影响报告生成等级**。港股、日股、韩股、A股和加密资产必须按同一档位生成正式 HTML 报告。

## 分析档位

| 你说 | 出什么 |
|:---|:---|
| "综合分析"/"出报告"/"生成研报" | 1 份 HTML |
| "完整分析"/"出完整研报" | HTML + 3 MD |
| "快速看下"/"估值" | 1 份 01_整体分析.md |

## 归档规则

- 公司文件夹 → **中文名**
- 文件命名 → `YYMMDD-NN_分析类型.md`
- 新日期分析 → 旧文件移入 `以往分析/`

## HTML 验证（🚨 每次生成后必须运行）

```bash
PYTHONPATH="src" python3 -m stock_analysis.cli validate <报告路径>
```

## Git 提交

- **commit message 必须使用中文撰写**
- 前缀: `feat:` / `fix:` / `refactor:` / `perf:` / `docs:` / `test:` / `build:` / `ci:` / `chore:` / `style:` / `revert:`
- 提交后自动 `git push`

## 关键约束

- **禁止用模型训练数据** — 所有价格/财务数据必须实时搜索或从 yfinance/公开 API 获取
- **排名优于打分** — 禁止 ad-hoc "调整评分"
- **调输入不调输出** — 改数据来源和计算公式，不改最终呈现
- **百分比优先** — 涨跌用 `+X%`/`-X%`
- **LLM 仅叙述** — 数学由 Python 完成，LLM 只生成文本叙述
- **3+ 家公司同时分析时，禁止后台并发派发**

## 历史演进

- v1.0: Greenblatt 原始（EBIT/EV + ROIC）→ 两层
- v2.0: Greenblatt 扩展（+ F-Score 验证）→ 三层
- v3.0: 四层加权（L1 40% + L2 25% + L3 25% + L4 10%）→ 当前
