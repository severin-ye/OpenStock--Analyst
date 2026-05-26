#!/bin/bash

# InvestSkill Web App 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 启动 InvestSkill Web App..."
echo ""

# 检查 Python 虚拟环境
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "📦 创建 Python 虚拟环境..."
    python3 -m venv "$PROJECT_ROOT/.venv"
fi

# 激活虚拟环境
source "$PROJECT_ROOT/.venv/bin/activate"

# 安装后端依赖
echo "📦 安装后端依赖..."
pip install -q fastapi uvicorn[standard] websockets

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 未找到 Node.js，请先安装 Node.js 18+"
    exit 1
fi

# 安装前端依赖
echo "📦 安装前端依赖..."
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    npm install
fi

# 启动后端
echo ""
echo "🔧 启动后端 API (端口 8001)..."
cd "$SCRIPT_DIR/backend"
PYTHONPATH="$PROJECT_ROOT/src" python main.py &
BACKEND_PID=$!

# 等待后端启动
sleep 2

# 启动前端
echo "🎨 启动前端开发服务器 (端口 5174)..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ InvestSkill Web App 已启动!"
echo ""
echo "   前端: http://localhost:5174"
echo "   后端 API: http://localhost:8001"
echo "   API 文档: http://localhost:8001/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 捕获退出信号
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

# 等待
wait
