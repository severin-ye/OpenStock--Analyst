# 股市分析 — 项目知识库

**生成**: 2026-05-10 | **分支**: main

## 概述

美股 + 加密资产综合投资分析项目。基于 InvestSkill v1.6.0（yennanliu，MIT）框架，按 Greenblatt 排名法（EBIT/EV + ROIC + F-Score），输出 Markdown 分析 + Chart.js 交互 HTML 报告。

## 目录结构

```
股市分析/
├── AGENTS.md              ← 本文件
├── index.html             ← 导航首页（本地 localhost:8888）
├── InvestSkill/            ← 分析框架源码（MIT，含20个prompt、CSS模板）
│   ├── _template.html      ← HTML 报告 CSS 主模板（所有报告共用）
│   ├── prompts/            ← 20个分析框架（stock-eval, dcf-valuation...）
│   ├── CLAUDE.md           ← InvestSkill 自身的知识库
│   └── output/             ← 示例报告
├── 英伟达/                  ← NVDA（8家公司各含01整体/02过去/03未来 + HTML报告）
├── 苹果/                   ← AAPL
├── 特斯拉/                 ← TSLA
├── 英特尔/                 ← INTC
├── AMD/                    ← AMD
├── 美光/                   ← MU
├── 小米/                   ← 1810.HK
├── 比特币/                 ← BTC
└── .sisyphus/             ← 会话数据
```

## 分析档位（触发词 → 输出）

| 你说 | 出什么 |
|---|---|
| "综合分析"/"出报告" | 1 份 HTML |
| "做研报"/"完整分析" | HTML + 3 MD |
| "快速看下"/"估值" | 1 份 01_整体分析.md |
| "收纳以往分析" | 归档旧分析到 `以往分析/` |
| "重算排名" | 只跑 Greenblatt 三层排名 |

## 核心规则（每次分析必须遵守）

### 数据采集（先搜后写）
1. marketbeat.com → 股价、PE、市值、YTD
2. trefis.com → 营收、增长驱动
3. 交叉验证 → 至少2个源一致

### 输出格式
- **百分比优先**：涨跌用 `+X%`/`-X%`，目标价辅助
- **涨跌总览表**：固定5列 `维度|涨跌比例|对应价格|概率权重|行业对比`
- **三层排名表**：固定格式 `Layer|维度|主指标|数值|排名|判断`
- **Piotroski F-Score 明细卡**：9 项逐项打分
- **HTML 报告**：8节（S1-S8+verdict），CSS 来自 `InvestSkill/_template.html`，评分区块替换为三层排名+F-Score卡
- **HTML 验证（🚨 必须）**：每次生成/修改 HTML 报告后，**必须**运行验证：
  ```bash
  python3 /home/severin/Codelib/股市分析/InvestSkill/validate_html.py <报告路径>
  ```
  验证失败 → 检查缺失 sections → 修复后重新验证。严禁交付未通过验证的 HTML 报告。
  原因：LLM 单次输出长 HTML 容易丢失中间 section（如苹果 260510 报告缺 S3/S4/S6/S7）。

### 批量分析执行策略（🚫 禁止并发派发）
- **3+ 家公司同时分析时，必须逐家自行执行，禁止 `task(background=true)` 并发派发**
- 原因：后台子代理并发槽位仅 1-2 个，多发必饿死
- 正确节奏：搜索→评分→写文件，完成一家再下一家
- 详见 invest-skill SKILL.md "批量分析执行策略" 章节

### 归档
- 公司文件夹→中文名
- 文件命名→`YYMMDD-NN_分析类型.md`
- 新日期分析→旧文件移入 `以往分析/`

## Git 提交（触发词 → 自动执行）

| 你说 | 执行 |
|---|---|
| "帮我提交git" / "提交一下" / "git commit" | 自动执行：查看变更 → 撰写详细提交消息 → 提交 → 推送 |

**工作流详见**: `InvestSkill/prompts/git-commit.md`

**关键规则**：
- 只写详细版（不做选择题），格式死板统一（二级缩进 `  · `）
- commit message 用中文，前缀遵循约定式提交（`feat:` / `fix:` 等）
- 评分/数据变化标注 `旧值 → 新值`，括号附理由
- 排序固定：项目级变更在前，公司按字母序在后
- 提交后自动 `git push`，不询问

## 命令

```bash
# 启动本地预览
cd /home/severin/Codelib/股市分析 && python3 -m http.server 8888
# 访问 http://localhost:8888/index.html

# Git
cd /home/severin/Codelib/股市分析 && git push origin main

# 运行 InvestSkill 测试
cd InvestSkill && npm test
```

## 评分体系（四层加权排名 v3.0）

> **核心原则**：排名优于打分。简单的 EBIT/EV + ROIC + F-Score + PEG 四层加权排名相加，F-Score 权重比 PEG 高，学术验证比任何主观加权评分更稳健。

### 四层排名（加权合成综合分）

| Layer | 维度 | 主指标 | 权重 | 用法 |
|-------|------|--------|:---:|------|
| **L1** | 💰 便不便宜 | **EBIT/EV**（Carlisle 收购者倍数） | **40%** | 从高到低排名 |
| **L2** | 🏭 赚不赚钱 | **ROIC**（Greenblatt 原始选择） | **25%** | 从高到低排名 |
| **L3** | 🛡️ 会不会崩 | **Piotroski F-Score (0-9)** | **25%** | 安全底线(避坑)，从高到低排名 |
| **L4** | 📈 增长值不值 | **PEG** (Forward PEG < 1 才划算) | **10%** | 从低到高排名 (PEG 越低越好) |

### 综合推荐公式

```
综合分 = L1排名×0.40 + L2排名×0.25 + L3排名×0.25 + L4排名×0.10
综合排名 = 综合分从小到大排序 (越小越好)
```

PEG 权重 10% 且排在最后——深度价值投资不追求成长性，以避坑和安全边际为主要任务。

### 8 家统一排名

所有标的在同一个排名体系内 (`#1~8/8`):
英伟达、苹果、特斯拉、英特尔、AMD、美光、小米(1810.HK)、比特币

### 特殊情况

- **加密货币（BTC）**：L1 用 MVRV Z-Score（反向映射），L2 用算力+网络强度，L3 用改编版 F-Score（链上指标），L4 用减半周期位置
- **港股（小米）**：同一公式但标注跨市场差异
- **困境反转**：统一使用 Non-GAAP Forward Estimate 计算 EBIT/EV 和 ROIC，排名对口径不敏感

### 输出格式

每次分析必须输出四层排名表 + Piotroski F-Score 明细卡 + 投资信号块 + 综合分 + 综合排名。

### 历史演进

- v1.0: Greenblatt 原始（EBIT/EV + ROIC）→ 两层
- v2.0: Greenblatt 扩展（EBIT/EV + ROIC + F-Score 验证不参与排名）→ 三层
- v3.0: 四层加权（L1 40% + L2 25% + L3 25% + L4 10%）→ 当前版本

## 注意事项

- 排名衡量**在当前价格下值不值得买**，非公司优质程度
- 禁止用模型训练数据——所有价格/财务数据必须实时搜索
- 加密货币/港股分析为扩展能力，原生框架为美股
- Skill 配置：`/home/severin/.config/opencode/skills/invest-skill/SKILL.md`
