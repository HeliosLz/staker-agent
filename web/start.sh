#!/bin/bash

# Staker Agent Web UI - 启动脚本

echo "🚀 Starting Staker Agent Web UI..."
echo ""

# 检查是否在 web 目录
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the web/ directory"
    exit 1
fi

# 启动后端
echo "📡 Starting backend server..."
cd backend
python3 app.py &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 2

# 启动前端
echo "🎨 Starting frontend dev server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Servers started successfully!"
echo ""
echo "📍 Frontend: http://localhost:5173"
echo "📍 Backend:  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# 捕获 Ctrl+C 信号
trap "echo ''; echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# 等待进程
wait
