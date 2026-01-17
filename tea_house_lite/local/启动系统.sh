#!/bin/bash

echo "========================================"
echo "  连锁茶楼管理系统"
echo "========================================"
echo ""

# 检查 Python 是否已安装
echo "[1/3] 正在检查 Python 环境..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ 错误：未检测到 Python！"
    echo ""
    echo "请先安装 Python："
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "MacOS: brew install python3"
    echo ""
    exit 1
fi

# 确定使用的 Python 命令
if command -v python3 &> /dev/null; then
    PYTHON=python3
    PIP=pip3
else
    PYTHON=python
    PIP=pip
fi

echo "✅ Python 环境检查通过 ($($PYTHON --version))"
echo ""

# 安装依赖包
echo "[2/3] 正在安装依赖包..."
echo "这可能需要几分钟，请耐心等待..."
echo ""
$PIP install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ 依赖包安装失败！"
    echo ""
    echo "请检查网络连接，然后重试"
    echo ""
    exit 1
fi

echo "✅ 依赖包安装完成"
echo ""

# 启动系统
echo "[3/3] 正在启动系统..."
echo ""
echo "系统启动成功后，会自动在浏览器打开"
echo "如果浏览器没有自动打开，请访问：http://localhost:8501"
echo ""
echo "按 Ctrl+C 可以停止系统"
echo "========================================"
echo ""

$PYTHON -m streamlit run app.py
