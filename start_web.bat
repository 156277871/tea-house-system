@echo off
chcp 65001 >nul
echo 🚀 启动连锁茶楼管理系统...
echo.

REM 设置环境变量
set PYTHONPATH=%CD%\src;%PYTHONPATH%

REM 启动Streamlit应用
streamlit run src\web\app.py --server.port 8501 --server.address 0.0.0.0

pause
