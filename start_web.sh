#!/bin/bash

echo "🚀 启动连锁茶楼管理系统..."
echo ""

# 设置环境变量
export PYTHONPATH=/workspace/projects/src:$PYTHONPATH

# 启动Streamlit应用
streamlit run src/web/app.py --server.port 8501 --server.address 0.0.0.0

