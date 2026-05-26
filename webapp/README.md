# InvestSkill Web App

交互式投资分析 Web 应用，基于 Greenblatt 四层加权排名体系。

## 功能特性

- 📊 **实时排名总览** — 查看所有标的的四层加权排名
- 🔍 **交互式分析** — 选择标的触发实时分析
- 📈 **详细报告** — 查看历史分析报告
- 🔄 **数据刷新** — 一键刷新 yfinance/CoinGecko 数据
- 💾 **Supermemory 集成** — 持久化投资分析记忆

## 技术栈

### 后端
- **FastAPI** — 高性能异步 API 框架
- **Python 3.10+** — 与现有 stock_analysis 模块集成
- **WebSocket** — 实时更新推送

### 前端
- **React 18** — 组件化 UI
- **TypeScript** — 类型安全
- **Tailwind CSS** — 原子化样式
- **Recharts** — 数据可视化
- **Vite** — 快速开发构建

## 快速开始

### 方式一：一键启动

```bash
cd webapp
./start.sh
```

### 方式二：分别启动

#### 启动后端

```bash
cd webapp/backend

# 激活虚拟环境
source ../../.venv/bin/activate

# 安装依赖
pip install fastapi uvicorn[standard] websockets

# 设置 Python 路径
export PYTHONPATH="../../src"

# 启动服务
python main.py
```

后端将运行在 http://localhost:8001

#### 启动前端

```bash
cd webapp/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在 http://localhost:5174

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/rankings` | 获取排名数据 |
| GET | `/api/companies` | 列出所有公司 |
| GET | `/api/company/{ticker}` | 获取公司详情 |
| POST | `/api/analyze` | 触发新分析 |
| GET | `/api/reports` | 列出历史报告 |
| POST | `/api/refresh` | 刷新数据缓存 |
| GET | `/api/markets` | 获取市场分组 |
| WS | `/ws/updates` | 实时更新推送 |

完整 API 文档: http://localhost:8001/docs

## 目录结构

```
webapp/
├── backend/
│   ├── main.py          # FastAPI 主应用
│   ├── supermemory.py   # Supermemory 集成
│   └── requirements.txt # 后端依赖
├── frontend/
│   ├── src/
│   │   ├── components/  # React 组件
│   │   ├── pages/       # 页面组件
│   │   ├── hooks/       # 自定义 Hooks
│   │   └── lib/         # 工具库
│   ├── package.json
│   └── vite.config.ts
├── start.sh             # 一键启动脚本
└── README.md
```

## 与现有系统集成

本 Web 应用与现有 `stock_analysis` Python 模块完全集成：

- **数据源**: 复用 `fetcher.py` 的 yfinance/CoinGecko 数据采集
- **排名计算**: 复用 `greenblatt.py` 的四层加权排名算法
- **报告生成**: 复用 `cli.py` 的完整分析流程
- **报告存储**: 直读 `分析输出/` 目录的 HTML 报告

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `PYTHONPATH` | Python 模块路径 | `../../src` |
| `LLM_MODE` | LLM 调用模式 | `api` |

## 开发

### 构建前端

```bash
cd webapp/frontend
npm run build
```

构建产物将输出到 `frontend/dist/`，可部署到任何静态文件服务器。

### 类型检查

```bash
cd webapp/frontend
npm run typecheck
```

## 许可证

MIT License
