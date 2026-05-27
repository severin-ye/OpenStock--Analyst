# 股市分析 — Agent 指令

**版本**: 3.0.1 | **更新**: 2026-05-26

## 架构（重构后）

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
│   │   │   │   └── report.jinja2 ← Jinja2 报告模板 (渲染实际使用)
│   │   │   └── stages/
│   │   │       ├── scaffold.py ← Stage 0: 识别公司、初始化报告壳
│   │   │       ├── render.py   ← Stage 4: Jinja2 → HTML
│   │   │       └── validate.py ← Stage 5-6: schema + HTML + 数据真实性验证
│   │   ├── registry.py         ← 从 companies.json 派生所有映射
│   │   ├── llm_client.py       ← DeepSeek/OpenAI 客户端
│   │   └── generator.py        ← index.html 自动生成器
│   └── investskill/            ← 方法论层 (上游开源, prompts + 21 skills)
│       ├── prompts/            ← 分析框架 prompt (.md)
│       └── plugins/us-stock-analysis/skills/ ← 21 个独立 SKILL.md
├── tests/                      ← pytest (comprehensive, engine, pipeline, ranker, batch, validate_crypto, mock)
├── 分析输出/                    ← 报告输出目录
└── index.html                  ← 排名总览 (自动生成)
```

### Pipeline 执行流程 (cli.py::run_analysis)

```
Stage 0:   scaffold  → 识别公司、初始化 StockReport 壳 (registry.py 查 companies.json)
Stage 0.5: refresh   → 自动刷新 prices.json (yfinance + CoinGecko/DeFiLlama)
Stage 1:   fetch     → 从 JSON 缓存加载多市场真实数据
Stage 2:   rank      → 纯 Python 计算四层排名 (greenblatt.py, 无 LLM)
Stage 3:   LLM       → 注入真实数据 + 预计算排名, LLM 仅生成叙述文本
Stage 4:   render    → Jinja2 模板 (reports/templates/report.jinja2) → HTML
Stage 5:   validate  → schema + HTML 结构 + 数据真实性交叉验证
Stage 6:   index     → 重建 index.html 排名总览
```

**反幻觉设计**: LLM 从不直接接触原始财务数据。所有数值由 yfinance/公开 API 预计算后注入 prompt，LLM 只写叙述。

## 核心命令

```bash
# 完整分析（fetch → rank → LLM → render → validate，默认 API 模式）
stock-analysis <公司中文名>

# 使用 OpenCode Agent IPC 模式调用 LLM（仅限单公司、交互式终端）
stock-analysis <公司中文名> --use-opencode-llm

# 或通过环境变量持久化选择:
export LLM_MODE=opencode   # 永久使用 OpenCode IPC
export LLM_MODE=api        # 永久使用直接 API（默认）

# Dry-run（fetch + rank，不调用 LLM，验证数据管道）
stock-analysis <公司中文名> --dry-run

# 顺序批量分析 (3+ 家公司，自动强制 API 模式)
stock-analysis batch <公司1> <公司2> <公司3> ...

# 重新生成 index.html 排名总览
stock-analysis index

# 监听分析输出目录，自动重建 index.html
stock-analysis watch

# 验证 HTML 报告
stock-analysis validate <报告路径>

# 等价的 python3 -m 调用
PYTHONPATH="src" python3 -m stock_analysis.cli <公司中文名>
```

### LLM 双模式说明

| 模式 | 触发方式 | 适用场景 | 限制 |
|:---|:---|:---|:---|
| **API 模式** (默认) | 不加参数，或 `LLM_MODE=api` | 所有场景：单公司、批量、CI | 需要配置 API key |
| **OpenCode IPC** | `--use-opencode-llm` 或 `LLM_MODE=opencode` | 仅单公司、交互式终端 | 不支持批量（多进程 stdout 冲突），批量自动切回 API |

环境变量优先级: `LLM_MODE` > `--use-opencode-llm` > 默认 API。

### 开发命令

```bash
# 安装 (含 dev 依赖)
pip install -e ".[dev]"

# 全量测试
PYTHONPATH="src" pytest tests/ -v

# 测试 (CI 运行子集)
PYTHONPATH="src" pytest tests/test_comprehensive.py tests/test_engine.py tests/test_pipeline.py tests/test_ranker.py tests/test_validate_crypto.py -v

# Lint
ruff check src/stock_analysis/

# Type check
mypy src/stock_analysis/ --exclude tests --ignore-missing-imports

# 验证 HTML (程序化)
PYTHONPATH="src" python3 -c "
from stock_analysis.reports.stages.validate import validate_html_file
issues = validate_html_file('<报告路径>')
print('OK' if not issues else 'FAIL'); [print(f'  {i}') for i in issues]
"
```

## 公司注册表 (Single Source of Truth)

**`data/companies.json`** 是唯一公司数据源。新增/修改公司只需编辑此文件，`registry.py` 自动派生所有映射（ticker ↔ 中文名、yfinance symbol、市场分组等）。

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

> **核心原则**: 排名优于打分。简单的 EBIT/EV + ROIC + F-Score + PEG 四层加权排名，学术验证比任何主观评分更稳健。

| Layer | 维度 | 主指标 | 权重 | 用法 |
|-------|------|--------|:---:|------|
| **L1** | 💰 便不便宜 | **EBIT/EV**（Carlisle 收购者倍数） | **40%** | 从高到低排名 |
| **L2** | 🏭 赚不赚钱 | **ROIC**（Greenblatt 原始选择） | **25%** | 从高到低排名 |
| **L3** | 🛡️ 会不会崩 | **Piotroski F-Score (0-9)** | **25%** | 安全底线，从高到低排名 |
| **L4** | 📈 增长值不值 | **PEG** (Forward PEG < 1 才划算) | **10%** | 从低到高排名 |

```
综合分 = L1排名×0.40 + L2排名×0.25 + L3排名×0.25 + L4排名×0.10
综合排名 = 综合分从小到大排序 (越小越好)
```

PEG 权重 10% 且排在最后——深度价值投资不追求成长性，以避坑和安全边际为主要任务。

### 特殊情况

- **加密货币（BTC）**: L1 MVRV Z-Score（反向映射）, L2 算力+网络强度, L3 改编版 F-Score, L4 减半周期
- **PoS 加密（ETH/SOL/BNB）**: L1 MCap/TVL, L2 Staking 比率, L3 Crypto F-Score(0-6), L4 年通胀率
- **港股/日股/韩股/A股**: 同一公式，币种标注差异，部分字段待完善
- **困境反转**: 统一使用 Non-GAAP Forward Estimate，排名对口径不敏感

### 输出格式（必须）

每次分析必须输出:
- 四层排名表 (`greenblatt_ranking`) + 权重 + 加权分
- Piotroski F-Score 明细卡 (9 项逐项打分)
- 投资信号块 + 综合分 + 综合排名
- HTML 报告: 8 节 (S1-S8) + verdict, CSS 内嵌在 `reports/templates/report.jinja2` 中

## 多市场支持状态

| 市场 | 价格源 | 财务源 | 排名适配 | 状态 |
|:---|:---|:---|:---|:---:|
| 美股 | yfinance (实时) | yfinance BS/IS/CF 自动推算 | 标准四层 | ✅ |
| 港股 | yfinance (1810.HK 等) | yfinance BS/IS/CF | 标准四层 + HKD标注 | 🟡 数据源待完善 |
| 日股 | yfinance (7203.T 等) | yfinance BS/IS/CF | 标准四层 + JPY标注 | 🟡 数据源待完善 |
| 韩股 | yfinance (000660.KS 等) | yfinance BS/IS/CF | 标准四层 + KRW标注 | 🟡 数据源待完善 |
| A股 | yfinance (688256.SS) | yfinance BS/IS/CF | 标准四层 + CNY标注 | 🟡 仅1家试验 |
| 加密 BTC | CoinGecko + yfinance | mempool.space / LookIntoBitcoin | MVRV+算力+F-Score+减半 | ✅ |
| 加密 PoS | CoinGecko + DeFiLlama | 链浏览器 / 官方 staking | MCap/TVL+Staking+CF-Score+通胀 | 🟡 staking/通胀待补强 |

### 🚨 防降级规则（必须遵守）

市场支持状态**只影响数据源选择和缺失字段披露**，**不影响报告生成等级**。用户要求"综合分析/出报告/生成研报"时，港股、日股、韩股、A股和加密资产必须按同一档位生成正式 HTML 报告。不得因为"数据源待完善""非美股"而降级为聊天摘要。

### 数据源优先级

1. **官方披露/公司 IR** (最高优先级)
2. **交易所/XBRL** (EDINET, DART, HKEXnews)
3. **行情层** (yfinance, Google Finance)
4. **二手聚合站** (StockAnalysis, MarketBeat — 仅交叉验证)

## 分析档位（触发词 → 输出）

| 你说 | 出什么 |
|:---|:---|
| "综合分析"/"出报告"/"生成研报" | 1 份 HTML |
| "完整分析"/"出完整研报" | HTML + 3 MD |
| "快速看下"/"估值" | 1 份 01_整体分析.md |
| "收纳以往分析" | 归档旧分析到 `以往分析/` |
| "重算排名" | 只跑 Greenblatt 四层排名 |

## 归档规则

- 公司文件夹 → **中文名**
- 文件命名 → `YYMMDD-NN_分析类型.md`
- 新日期分析 → 旧文件移入 `以往分析/`

## 批量分析执行策略（🚫 禁止并发）

**3+ 家公司同时分析时，必须逐家自行执行，禁止后台并发派发。**

原因: 后台子代理并发槽位仅 1-2 个，多发必饿死。
正确节奏: 搜索→评分→写文件，完成一家再下一家。

## HTML 验证（🚨 每次生成后必须运行）

```bash
PYTHONPATH="src" python3 -m stock_analysis.cli validate <报告路径>
```

验证内容:
- 8 个 section (S1-S8) 存在
- verdict 裁决区存在
- Chart.js 图表存在
- 文件大小 ≥ 15KB
- F-Score 9 项完整 (股票类)
- S7 风险矩阵 ≥ 5 项

验证失败 → 修复 → 重新验证。严禁交付未通过验证的 HTML 报告。

## Git 提交

| 你说 | 执行 |
|:---|:---|
| "帮我提交git" / "提交一下" / "git commit" | 自动执行：查看变更 → 撰写详细提交消息 → 提交 → 推送 |

**规则**:
- **commit message 必须使用中文撰写**：subject 用中文，body 用中文，禁止英文 subject 和英文 highlights
- 前缀遵循约定式提交：`feat:` / `fix:` / `refactor:` / `perf:` / `docs:` / `test:` / `build:` / `ci:` / `chore:` / `style:` / `revert:`（前缀本身用英文简写，冒号后内容用中文）
- 只写详细版（不做选择题），格式统一（二级缩进 `  · `）
- 评分/数据变化标注 `旧值 → 新值`，括号附理由
- 排序固定：项目级变更在前，公司按字母序在后
- 提交后自动 `git push`，不询问

## 关键约束

- **禁止用模型训练数据** — 所有价格/财务数据必须实时搜索或从 yfinance/公开 API 获取
- **排名优于打分** — 禁止 ad-hoc "调整评分"，禁止合成单一总分
- **调输入不调输出** — 改数据来源和计算公式，不改最终呈现
- **百分比优先** — 涨跌用 `+X%`/`-X%`，目标价辅助
- **LLM 仅叙述** — 数学由 Python 完成，LLM 只生成文本叙述

## Web App（可选前端）

本项目同时提供 **CLI 工具**（主入口）和 **Web App**（可视化前端）。

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

## 历史演进

- v1.0: Greenblatt 原始（EBIT/EV + ROIC）→ 两层
- v2.0: Greenblatt 扩展（EBIT/EV + ROIC + F-Score 验证不参与排名）→ 三层
- v3.0: 四层加权（L1 40% + L2 25% + L3 25% + L4 10%）→ 当前
