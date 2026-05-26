# InvestSkill Web App — Agent 指令

## 架构

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

## 端口

- **前端**: 5174 (3000/5173 已被占用)
- **后端**: 8001
- **API 文档**: http://localhost:8001/docs

## 命令

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

## 与主项目关系

- 后端复用 `src/stock_analysis/` 的 fetcher、ranking、cli 模块
- 报告存储读取 `分析输出/` 目录
- 前端通过 `/api/*` 代理到后端
- `PYTHONPATH` 必须包含 `../../src`

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/rankings` | 排名数据，支持 `?market=US/HK/KR/CN/Crypto` |
| GET | `/api/companies` | 公司列表 |
| GET | `/api/company/{ticker}` | 公司详情 |
| POST | `/api/analyze` | 触发分析 |
| GET | `/api/reports` | 历史报告 |
| POST | `/api/refresh` | 刷新缓存 |
| WS | `/ws/updates` | 实时推送 |

## 前端路由

| 路径 | 页面 |
|------|------|
| `/` | 排名总览 Dashboard |
| `/company/{ticker}` | 公司详情 |
| `/analysis` | 交互式分析 |
| `/reports` | 历史报告 |
