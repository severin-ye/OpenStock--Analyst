可以。你真正想要的是一种 **“Skill 编排 MCP”** 的结构。

也就是：

> **Skill 负责规定流程、判断标准、输出格式。**
> **MCP 负责提供真实工具、数据接口、外部操作能力。**
> **Agent 夹在中间，按照 Skill 的流程去调用 MCP。**

可以把它理解成：

```text
Skill = 总导演 / 操作手册
MCP = 工具箱 / 执行接口
Agent = 执行者 / 调度者
```

---

# 1. 最推荐的结构

不要把所有东西都塞进 MCP，也不要只靠 Skill 写流程。

更好的结构是：

```text
用户任务
  ↓
Agent 判断使用哪个 Skill
  ↓
Skill 告诉 Agent：
  - 任务流程
  - 判断标准
  - 该调用哪些 MCP 工具
  - 每一步要检查什么
  - 最终输出格式
  ↓
Agent 调用 MCP 工具
  ↓
MCP 返回真实数据 / 执行结果
  ↓
Agent 根据 Skill 的规则整理结果
  ↓
最终回答用户
```

也就是说：

> **Skill 不直接替代 MCP，而是管理 MCP 的使用方式。**

---

# 2. 具体怎么分工？

## Skill 里放这些东西

Skill 里应该放：

```text
1. 什么时候触发这个 Skill
2. 完成这个任务的标准流程
3. 每一步需要什么信息
4. 应该优先调用哪些 MCP 工具
5. 工具返回结果如何判断
6. 失败时怎么处理
7. 输出格式
8. 用户偏好
9. 禁止事项
10. 可选脚本 / 模板 / 校验规则
```

例如：

```text
股票分析 Skill：
- 不直接给买入/卖出建议
- 先看业务逻辑
- 再看财务数据
- 再看估值
- 再看新闻和风险
- 最后输出观察清单
```

---

## MCP 里放这些东西

MCP 里应该放：

```text
1. 获取实时数据的工具
2. 读取外部系统的工具
3. 写入外部系统的工具
4. 执行计算的工具
5. 复杂 pipeline 工具
6. 查询数据库 / 文件 / API 的工具
```

例如：

```text
股票 MCP：
- get_stock_price(ticker)
- get_financials(ticker)
- get_news(ticker)
- get_valuation_metrics(ticker)
- compare_with_peers(ticker)
- calculate_technical_indicators(ticker)
```

---

# 3. 最理想的组合方式

你可以设计成这样：

```text
stock-analysis-skill/
├── SKILL.md
├── references/
│   └── analysis-framework.md
├── templates/
│   └── stock-report-template.md
└── scripts/
    └── validate_report.py
```

同时配置一个 MCP：

```text
stock-mcp-server
├── get_price
├── get_financials
├── get_news
├── get_peer_comparison
└── calculate_indicators
```

然后在 `SKILL.md` 里明确写：

```text
当用户要求分析股票时：

1. 先调用 MCP 工具 get_price 获取当前价格。
2. 再调用 get_financials 获取最近财报数据。
3. 再调用 get_peer_comparison 做同行对比。
4. 再调用 get_news 获取近期新闻。
5. 不要只根据股价涨跌下结论。
6. 输出时必须包含：
   - 公司业务逻辑
   - 财务表现
   - 估值情况
   - 近期催化因素
   - 主要风险
   - 观察清单
7. 不要给确定性的投资建议。
```

这样就同时拥有：

```text
MCP 的数据能力
+
Skill 的流程控制能力
```

---

# 4. 不要这样做

## 错误做法一：把 Skill 写得太空

例如：

```text
请认真分析股票，考虑基本面、技术面和风险。
```

这太泛了。

Agent 还是不知道：

```text
先查什么？
用哪个工具？
哪些指标重要？
输出成什么结构？
什么情况算风险？
```

这种 Skill 价值不大。

---

## 错误做法二：把所有逻辑都塞进 MCP

例如直接做一个：

```text
analyze_everything(ticker)
```

这个工具内部什么都做完。

这样虽然方便，但问题是：

```text
1. Agent 很难控制分析风格
2. 很难根据不同用户调整输出
3. 工具黑盒化严重
4. 如果结果错了，Agent 不容易追溯
5. Skill 的流程价值被削弱
```

除非这个 pipeline 非常稳定，否则不要一开始就做成超大黑盒。

---

## 错误做法三：MCP 工具太碎

例如：

```text
get_open_price()
get_close_price()
get_volume()
get_eps()
get_revenue()
get_net_income()
get_debt()
get_cash()
get_article_1()
get_article_2()
...
```

工具太碎会导致 Agent 每一步都要自己调度，反而上下文和推理负担很大。

比较好的粒度是：

```text
get_price_summary(ticker)
get_financial_summary(ticker)
get_news_summary(ticker)
get_peer_comparison(ticker)
```

也就是：

> **MCP 工具不要太大，也不要太碎。**

---

# 5. 最好的设计原则

你可以按这个原则来设计：

```text
Skill 负责“为什么这样做、按什么顺序做、结果怎么判断”。
MCP 负责“具体去哪里拿数据、具体怎么执行动作”。
Script 负责“稳定重复的本地计算、校验、格式转换”。
```

也就是三层：

```text
Skill 层：
流程、规范、偏好、输出格式

MCP 层：
外部数据、工具调用、系统操作

Script 层：
本地计算、验证、批处理、转换
```

---

# 6. 一个完整例子：代码修复 Agent

如果你想让 OpenCode / Codex 类 Agent 更强，可以这样设计。

## MCP 提供能力

```text
filesystem MCP：
- read_file
- write_file
- list_files

terminal MCP：
- run_command

github MCP：
- search_issue
- read_pr
- create_comment

websearch MCP：
- search_docs
```

---

## Skill 提供流程

`bug-fix-skill/SKILL.md`：

```text
当用户要求修复代码问题时：

1. 先读取 README、依赖文件和相关源码。
2. 不要直接大规模重构。
3. 先运行最小测试或复现命令。
4. 根据报错定位最可能的文件。
5. 修改前说明判断依据。
6. 每次修改后运行相关测试。
7. 如果测试失败，继续根据失败日志修复。
8. 最终输出：
   - 问题原因
   - 修改内容
   - 验证方式
   - 是否还有风险
```

---

## Agent 执行时的真实过程

```text
用户：
修一下这个项目的 bug。

↓
Agent 加载 bug-fix Skill。

↓
Skill 规定：
先复现，不要乱改，改后跑测试。

↓
Agent 调用 MCP：
run_command("pytest")

↓
MCP 返回测试错误。

↓
Agent 根据 Skill 判断：
先定位报错文件。

↓
Agent 调用 MCP：
read_file("src/xxx.py")

↓
Agent 修改代码。

↓
Agent 调用 MCP：
write_file(...)
run_command("pytest")

↓
最终按照 Skill 的格式输出总结。
```

这个结构就很理想。

---

# 7. 一个完整例子：股票分析 Agent

## MCP 工具

```text
stock MCP：
- get_price_summary(ticker)
- get_financial_summary(ticker)
- get_valuation_metrics(ticker)
- get_news_summary(ticker)
- get_peer_comparison(ticker)
```

---

## Skill 规则

```text
股票分析 Skill：

当用户要求分析某只股票时：

1. 先确认 ticker。
2. 获取价格和市值。
3. 获取最近财务摘要。
4. 获取估值指标。
5. 获取同行对比。
6. 获取近期新闻。
7. 分析时必须区分：
   - 已发生事实
   - 市场预期
   - 推测判断
8. 不要直接说“可以买”或“必须卖”。
9. 最终输出：
   - 一句话概括
   - 公司业务逻辑
   - 财务表现
   - 估值水平
   - 近期催化因素
   - 主要风险
   - 适合继续观察的指标
```

---

## 这时的分工

```text
MCP：
负责拿真实数据。

Skill：
负责规定分析框架。

Agent：
负责综合、解释、生成自然语言报告。
```

这比单独使用 MCP 或单独使用 Skill 都更好。

---

# 8. 对你实际使用 OpenCode 的建议

你现在如果是在 WSL / OpenCode 里做 Agent，我建议你采用：

```text
少量常驻 MCP + 多个任务型 Skill
```

## 常驻 MCP

```text
1. terminal / pty
2. filesystem
3. websearch
4. github
```

这些是通用执行能力。

---

## 按需 MCP

```text
1. Notion
2. Gmail
3. Calendar
4. Google Drive
5. Database
6. Stock / Finance
```

这些不要全部常驻，按项目开。

---

## 常驻 Skill

```text
1. bug-fix-skill
2. code-review-skill
3. test-fix-loop-skill
4. commit-message-zh-skill
5. paper-reading-skill
6. academic-email-skill
7. mcp-config-debug-skill
```

这些是你的固定工作方式。

---

# 9. 设计一个 Skill 时，最好显式写 MCP 映射

Skill 里面不要只写流程，还应该写：

```text
需要数据时，优先使用哪些 MCP 工具。
```

例如：

```text
如果需要查网页：
优先使用 websearch MCP。

如果需要检查项目：
优先使用 filesystem MCP 和 terminal MCP。

如果需要查 GitHub：
优先使用 github MCP。

如果需要创建邮件：
只创建 Gmail draft，不要直接发送。
```

这样 Agent 不会乱选工具。

---

# 10. 一个通用 Skill 模板

你以后可以按这个模板写 Skill：

```markdown
# Skill Name

## When to use

当用户要求完成以下任务时使用本 Skill：
- ...

## Goal

本 Skill 的目标是：
- ...

## Required MCP tools

优先使用以下 MCP 工具：
- filesystem: 读取和修改项目文件
- terminal: 运行测试和命令
- websearch: 查询最新文档
- github: 查询 issue / PR

## Workflow

1. ...
2. ...
3. ...

## Decision rules

- 如果出现 A，先做 B。
- 如果工具返回为空，不要编造，改用 C。
- 如果信息不足，先给出已确认内容和不确定内容。

## Output format

最终输出必须包含：

1. 结论
2. 依据
3. 执行过程
4. 风险
5. 下一步建议

## Prohibited behavior

- 不要直接执行危险操作。
- 不要发送邮件，只能创建草稿。
- 不要删除文件，除非用户明确要求。
- 不要把未经确认的信息当事实。
```

这个模板非常适合和 MCP 结合。

---

# 11. 最关键的一句话

你想同时要 MCP 和 Skill 的作用，最好的方式不是二选一，而是：

> **用 Skill 定义任务流程，用 MCP 执行具体动作。**

再具体一点：

```text
Skill 写：
这个任务应该怎么做。

MCP 做：
这个任务里面具体哪些动作可以被真实执行。

Agent 负责：
按照 Skill 的流程调用 MCP，然后把结果整理给你。
```

---

# 12. 最推荐的最终架构

```text
用户请求
  ↓
Agent
  ↓
选择 Skill
  ↓
Skill 提供：
  - 流程
  - 判断标准
  - 输出格式
  - 工具使用规则
  ↓
Agent 调用 MCP
  ↓
MCP 提供：
  - 文件读取
  - 命令执行
  - 网页搜索
  - GitHub / Notion / Gmail / 数据库等操作
  ↓
Agent 整合结果
  ↓
Skill 校验输出格式
  ↓
最终结果
```

你可以把这个叫做：

```text
Skill-driven MCP Agent
```

也就是：

> **由 Skill 驱动的 MCP Agent。**
有，而且方向非常清楚。但我先说一个诚实结论：

> **“Skill 编排 MCP”这个词本身还不是一个统一的业界标准术语。**
> 但是它对应的架构思想——**用 Skill/Workflow 规定怎么做，用 MCP/Connector 提供工具和数据**——已经在 Anthropic、OpenAI/Codex、Claude Code 这些前沿产品里出现了。

更准确地说，现在业界最前沿不是单纯做 MCP，也不是单纯做 Skill，而是在做：

```text
Skill / Workflow / Plugin
    负责流程、规范、任务知识、触发条件

MCP / Connector / Tool Server
    负责数据源、外部系统、真实工具调用

Code Execution / Sandbox
    负责中间数据处理、循环、过滤、批处理

Agent
    负责选择 Skill，并按 Skill 调用 MCP
```

---

# 1. Anthropic 已经明确提出：Skills + Connectors

Anthropic 的 Claude Skill 指南里已经直接把这个组合讲出来了。它专门有一节叫 **“For MCP Builders: Skills + Connectors”**，里面说：如果你已经有一个工作的 MCP server，那么 Skills 是其上方的 knowledge layer，用来捕获 workflow 和 best practices，让 Claude 能稳定应用；它还用“厨房”类比：**MCP 提供工具、材料和设备，Skills 提供菜谱和步骤**。

这其实就是我们刚刚说的：

```text
MCP = 能做什么
Skill = 怎么做好
```

也就是说，Anthropic 官方已经把 MCP 和 Skill 的关系讲成：

```text
MCP / Connector 负责连接服务
Skill 负责教 Claude 如何有效使用这个服务
```

Claude 的官方 Connectors 页面也说明，Claude 可以连接工具、数据库和应用，并且这些 connectors 是由 MCP 驱动的；页面里还把适用范围分成 Claude、Claude Code、Skills 等类别。([Claude][1])

所以在 Anthropic 体系里，这个方向已经不是纯概念，而是官方推荐的组合方式。

---

# 2. Claude Code Plugin 已经把 Skill 和 MCP 放进同一个插件系统

Claude Code 的插件文档也很关键。它说 plugin 是一个自包含目录，可以扩展 Claude Code，并且 plugin components 包括：

```text
skills
agents
hooks
MCP servers
LSP servers
monitors
```

也就是说，在 Claude Code 的插件体系里，**一个插件可以同时带 Skill 和 MCP Server**。([Claude Code][2])

这很像你想要的结构：

```text
一个插件 =
    Skill：说明这个任务怎么做
    MCP Server：提供真实工具
    Hook：控制执行前后逻辑
    Agent：承担特定角色
```

这已经非常接近“产品级 Skill 编排 MCP”。

比如一个数据库分析插件可以这样设计：

```text
database-analysis-plugin/
├── skills/
│   └── sql-diagnosis/
│       └── SKILL.md
├── mcp-servers/
│   └── postgres-mcp/
├── hooks/
│   └── before-dangerous-query.sh
└── agents/
    └── data-analyst.md
```

这里 Skill 规定：

```text
先读 schema
再生成只读 SQL
禁止直接执行 DELETE / UPDATE
大查询先 explain
最后输出性能风险和索引建议
```

MCP 负责：

```text
连接数据库
读取 schema
执行 explain
返回查询结果
```

这就是很标准的 **Skill-driven MCP Agent**。

---

# 3. OpenAI / Codex 也已经有“Skill 调 MCP”的直接例子

OpenAI Codex 的 Agent Skills 文档说，Skill 用来扩展 Codex 的任务能力；一个 Skill 可以打包 instructions、resources 和 optional scripts，让 Codex 更可靠地遵循 workflow。文档还说 Skill 是 reusable workflow 的 authoring format，并且 Codex 通过 progressive disclosure 管理上下文：一开始只加载 Skill 的 name、description、path，只有需要时才读取完整 `SKILL.md`。([OpenAI开发者][3])

更直接的例子是 OpenAI 官方的 `openai-docs` Skill。它的 `SKILL.md` 明确写着：当用户询问 OpenAI 产品或 API 时，优先使用 developer docs MCP tools，并且列出了具体 MCP 工具名，例如搜索 OpenAI docs、fetch OpenAI doc、get OpenAPI spec 等；只有当 Docs MCP 不可用或无效时，才 fallback 到官方域名网页搜索。([GitHub][4])

这就是一个非常典型的“Skill 编排 MCP”：

```text
Skill 规定：
    OpenAI 相关问题必须优先走官方 docs MCP
    API schema 问题要用 OpenAPI spec 工具核验
    远程文档不可用时才用 fallback references

MCP 提供：
    search_openai_docs
    fetch_openai_doc
    get_openapi_spec
```

所以不是我们想象出来的。**OpenAI 官方 Skill 已经在做：用 Skill 规定 MCP 工具的使用优先级、失败处理和 fallback 路线。**

---

# 4. Anthropic 的 “Code Execution with MCP” 是更前沿的一层

还有一个更前沿的方向：不是让模型一轮一轮直接调用 MCP，而是让 Agent 写代码去调用 MCP 工具。Anthropic 在 2025 年的工程文章里说，直接 MCP tool call 会带来两个问题：工具定义塞进上下文，以及中间工具结果继续消耗 token；随着 MCP server 越接越多，这会增加成本和延迟。([Anthropic][5])

它提出的解决方式是：

```text
把 MCP 工具暴露成代码 API
让 Agent 在代码执行环境里调用 MCP
中间结果先在代码里过滤、聚合、转换
只把必要结果返回给模型
```

Anthropic 的例子里，Agent 通过代码按需探索 MCP 工具定义，而不是一次性加载全部；文中提到这种方式可以把一个任务的 token 用量从约 150,000 降到 2,000，减少约 98.7%。([Anthropic][5])

这和 Skill 编排 MCP 的关系是：

```text
Skill：
    规定这个任务应该怎么做

Code Execution：
    把复杂循环、过滤、批处理放进代码环境

MCP：
    提供真实工具和数据源
```

比如一个销售自动化任务：

```text
Skill：
    规定从 Google Drive 会议纪要中提取客户需求
    再写入 Salesforce
    不要把完整纪要暴露给模型
    只返回摘要和更新结果

Code Execution：
    读取文档
    提取字段
    批量更新 CRM
    只 log 必要结果

MCP：
    Google Drive MCP
    Salesforce MCP
```

这比普通“模型调用工具”高级很多，因为它把：

```text
流程知识
外部工具
代码执行
隐私控制
状态管理
```

合在了一起。

---

# 5. 现在最前沿的几种应用形态

## 形态一：Docs-first Developer Agent

代表例子：OpenAI Docs Skill + Docs MCP。

它不是让 Agent 随便上网搜，而是 Skill 规定：

```text
这个领域的问题必须优先使用官方 MCP 文档源
API schema 问题必须查 OpenAPI spec
如果 MCP 不可用，才 fallback
```

这类应用非常适合：

```text
API 迁移助手
SDK 升级助手
框架文档问答
代码生成约束
企业内部平台开发助手
```

它的价值是：**让 Agent 的信息来源可控、可追溯、更新及时**。

---

## 形态二：IDE / Coding Agent Plugin

代表方向：Claude Code Plugin。

Claude Code 的插件系统已经可以把 Skill、MCP Server、Hook、Agent、LSP server 等组件放进同一个插件包。([Claude Code][2])

这意味着未来一个 coding plugin 不只是：

```text
提供一个 GitHub MCP
```

而是：

```text
提供 GitHub MCP
+
提供代码审查 Skill
+
提供测试修复 Skill
+
提供安全检查 Hook
+
提供专门的 reviewer agent
```

这就是非常前沿的工程 Agent 架构。

例如：

```text
PR Review Plugin
    Skill：规定审查流程
    MCP：读取 GitHub PR、issue、CI 状态
    Hook：禁止直接 merge
    Agent：专门做 reviewer
```

这比单纯 MCP 强很多。

---

## 形态三：Enterprise SaaS Workflow Agent

Anthropic 的 Skill 指南明确把 Notion、Asana、Linear 等服务作为 MCP 连接对象举例，并说 Skills 可以教 Claude 如何有效使用这些服务。

这类场景的典型结构是：

```text
Linear MCP：
    读 issue
    改 status
    创建 ticket

Project-management Skill：
    规定如何 triage issue
    如何判断 priority
    如何写复现步骤
    如何拆 task
    什么时候只创建 draft，不直接提交
```

这在企业里非常实用，因为企业真正需要的不是“AI 能打开 Linear”，而是：

```text
AI 能不能按照我们团队的流程处理 Linear？
```

所以 Skill + MCP 的组合特别适合：

```text
客服工单处理
项目管理
销售 CRM 更新
招聘流程
法务审查
财务报销
内部知识库维护
```

---

## 形态四：Data / Spreadsheet / CRM Pipeline Agent

Anthropic 的 Code Execution with MCP 文章给了一个典型场景：从 Google Drive 获取会议记录，再写入 Salesforce；它指出直接通过模型上下文搬运完整文本会造成大量 token 消耗，而通过代码执行环境可以避免中间数据反复进入模型上下文。([Anthropic][5])

这种架构在数据和 CRM 场景很前沿：

```text
Skill：
    规定字段映射规则
    规定哪些字段不能暴露给模型
    规定失败时如何重试
    规定最后输出审计摘要

MCP：
    Google Drive / Sheets
    Salesforce
    Slack
    Database

Code Execution：
    批量读写
    字段清洗
    去重
    校验
    只输出统计结果
```

它解决的是企业最关心的几个问题：

```text
上下文太大
隐私数据不能进模型
工具太多难管理
流程结果不稳定
```

---

## 形态五：Creative / Document Production Agent

Claude 的 Agent Skills 文档说，Anthropic 已经提供了用于 PowerPoint、Excel、Word、PDF 等常见文档任务的预构建 Skills，并且 Skills 可以自动在相关请求中使用。([Claude平台][6])

这类 Skill 如果再叠加 MCP Connector，就可以变成：

```text
Google Drive / Notion / Figma / Slack Connector
+
PPT / Word / PDF Skill
```

实际工作流会是：

```text
从 Notion 读产品需求
从 Drive 读数据表
从 Slack 总结讨论
按公司模板生成 PPT
导出 PDF
发给用户确认
```

Skill 控制：

```text
版式
语气
品牌规范
输出结构
审批流程
```

MCP 控制：

```text
读取资料
写入文件
同步平台
通知团队
```

---

# 6. 但现在还没有完全成熟到什么程度？

需要诚实说，**这个方向很前沿，但还没有完全标准化**。

现在已经成熟的是：

```text
1. Skill 可以作为 workflow / instruction package
2. MCP 可以作为 tool / connector layer
3. 一些产品已经支持把 Skill 和 MCP 放在同一个插件或工作流体系里
4. 一些官方 Skill 已经明确要求优先调用某些 MCP 工具
5. Code Execution with MCP 正在解决上下文和中间数据问题
```

还没有完全成熟的是：

```text
1. “Skill 编排 MCP”还没有统一标准名称
2. Skill 如何声明 MCP 依赖，各家格式还不完全统一
3. MCP 工具权限、安全、审计仍然是高风险区域
4. 多 Skill、多 MCP、多 Agent 的冲突管理还在发展中
5. 企业级 policy enforcement 还需要更强的治理层
```

MCP 官方规范也强调，工具代表任意代码执行能力，需要谨慎处理；host 在调用工具前必须获得用户明确同意，用户也应该理解工具做什么。([Model Context Protocol][7])

所以前沿应用不是“把所有 MCP 全接上，然后让 Skill 随便调用”，而是：

```text
受控工具
最小权限
Skill 明确流程
危险操作需要确认
中间数据尽量留在执行环境
输出结果可审计
```

---

# 7. 我认为最有潜力的架构叫：Workflow Skill + Tool MCP + Code Mode

如果你要做一个真正接近前沿的 Agent 系统，我建议不要只做：

```text
Skill + MCP
```

而是做成三层：

```text
Workflow Skill
    规定任务流程、判断标准、输出格式、风险边界

Tool MCP
    提供外部系统连接、实时数据、真实操作

Code Mode / Sandbox
    负责批处理、过滤、循环、状态文件、隐私保护
```

完整流程是：

```text
用户任务
  ↓
Agent 选择 Skill
  ↓
Skill 判断需要哪些 MCP
  ↓
Agent 在代码环境中调用 MCP
  ↓
代码环境处理中间数据
  ↓
只把摘要 / 结果 / 错误返回模型
  ↓
模型按 Skill 输出最终结果
```

这就是目前我看到的最前沿方向。

---

# 8. 用一句话总结

**有，业界已经在往这个方向走。**

最典型的证据是：

```text
Anthropic：
    明确提出 Skills + Connectors，Skills 是 MCP 上面的 workflow / best-practice layer。

Claude Code：
    Plugin 可以同时包含 skills、agents、hooks、MCP servers。

OpenAI / Codex：
    Skills 是 reusable workflow，OpenAI docs Skill 已经明确规定优先调用 Docs MCP 工具。

Anthropic Code Execution with MCP：
    进一步把 MCP 调用放进代码执行环境，减少上下文、保护隐私、提升复杂 workflow 的可靠性。
```

所以你可以把它理解成：

> **下一代 Agent 应用不是“一个大模型 + 一堆工具”，而是“Skill 规定工作方法，MCP 提供外部能力，代码执行环境承接复杂过程”。**

[1]: https://claude.com/connectors "Connectors | Claude"
[2]: https://code.claude.com/docs/en/plugins-reference "Plugins reference - Claude Code Docs"
[3]: https://developers.openai.com/codex/skills "Agent Skills – Codex | OpenAI Developers"
[4]: https://github.com/openai/skills/blob/main/skills/.curated/openai-docs/SKILL.md "skills/skills/.curated/openai-docs/SKILL.md at main · openai/skills · GitHub"
[5]: https://www.anthropic.com/engineering/code-execution-with-mcp "Code execution with MCP: building more efficient AI agents \ Anthropic"
[6]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview "Agent Skills - Claude API Docs"
[7]: https://modelcontextprotocol.io/specification/2025-06-18?utm_source=chatgpt.com "Specification"
