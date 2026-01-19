@echo off
chcp 65001 >nul
echo 🛑 停止旧实例...
taskkill /F /IM streamlit.exe 2>nul
taskkill /F /IM python.exe 2>nul

echo 🚀 启动茶楼管理系统...
cd /d "%~dp0"
streamlit run app.py --server.headless true --server.port 8501

echo.
echo ✅ 应用已启动！
echo 📱 访问地址: http://localhost:8501
pause
