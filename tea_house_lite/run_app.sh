#!/bin/bash

# 停止所有正在运行的 Streamlit 实例
echo "🛑 停止旧实例..."
pkill -9 -f streamlit
pkill -9 -f "python.*app.py"

# 等待进程完全停止
sleep 2

# 清理可能存在的锁文件
rm -f .streamlit/health.lock 2>/dev/null

# 启动应用
echo "🚀 启动茶楼管理系统..."
cd "$(dirname "$0")"
streamlit run app.py --server.headless true --server.port 8501

echo ""
echo "✅ 应用已启动！"
echo "📱 访问地址: http://localhost:8501"
