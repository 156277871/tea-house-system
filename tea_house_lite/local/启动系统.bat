@echo off
chcp 65001 >nul
title 连锁茶楼管理系统 - 正在启动...

echo ========================================
echo   连锁茶楼管理系统
echo ========================================
echo.

REM 检查 Python 是否已安装
echo [1/3] 正在检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：未检测到 Python！
    echo.
    echo 请先安装 Python：
    echo 1. 访问 https://www.python.org/downloads/
    echo 2. 下载 Python 3.10 或 3.11 版本
    echo 3. 安装时务必勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo ✅ Python 环境检查通过
echo.

REM 安装依赖包
echo [2/3] 正在安装依赖包...
echo 这可能需要几分钟，请耐心等待...
echo.
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ 依赖包安装失败！
    echo.
    echo 请检查网络连接，然后重试
    echo.
    pause
    exit /b 1
)

echo ✅ 依赖包安装完成
echo.

REM 启动系统
echo [3/3] 正在启动系统...
echo.
echo 系统启动成功后，会自动在浏览器打开
echo 如果浏览器没有自动打开，请访问：http://localhost:8501
echo.
echo 按 Ctrl+C 可以停止系统
echo ========================================
echo.

streamlit run app.py

pause
