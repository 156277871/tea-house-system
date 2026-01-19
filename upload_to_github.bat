@echo off
chcp 65001 >nul
REM 连锁茶楼管理系统 V4.1 - GitHub一键上传脚本 (Windows版本)

echo ========================================
echo 连锁茶楼管理系统 V4.1 - GitHub上传脚本
echo ========================================
echo.

REM 检查Git是否安装
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: Git未安装，请先安装Git
    echo 下载地址: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM 检查是否在正确的目录
if not exist "app.py" (
    echo ❌ 错误: 请在tea_house_lite目录下运行此脚本
    pause
    exit /b 1
)

echo ✅ 检查通过，开始准备上传...
echo.

REM 初始化Git仓库（如果还没有）
if not exist ".git" (
    echo 📦 初始化Git仓库...
    git init
    git branch -M main
    echo ✅ Git仓库初始化完成
    echo.
)

REM 添加文件
echo 📝 添加文件到Git...
git add .gitignore
git add README.md
git add DEPLOY.md
git add UPLOAD_GUIDE.md
git add requirements.txt
git add app.py
echo ✅ 文件添加完成
echo.

REM 提交更改
echo 💾 提交更改...
git commit -m "Initial commit: 连锁茶楼管理系统 V4.1

✨ 新功能:
- 控制台实时数据展示
- 经营管理（开台、点单、结账）
- 系统设置（门店、桌台、员工、商品、库存）
- 会员管理
- 订单管理
- 财务报表

🎨 优化:
- 亮色主题设计
- 导航栏重构（6个一级菜单）
- 按钮颜色优化
- 响应式布局

🐛 修复:
- 员工管理门店ID显示问题
- 按钮文字可见性问题"

if %errorlevel% neq 0 (
    echo ⚠️  警告: 没有新的更改需要提交
) else (
    echo ✅ 提交完成
)
echo.

REM 检查是否已配置远程仓库
git remote get-url origin >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%i in ('git remote get-url origin') do set REPO_URL=%%i
    echo 🔗 远程仓库已配置: %REPO_URL%
    echo.
    set /p choice="是否推送到远程仓库？(y/n): "
    if /i "%choice%"=="y" (
        echo 📤 推送代码到GitHub...
        git push -u origin main
        if %errorlevel% equ 0 (
            echo ✅ 推送成功！
            echo.
            echo 🎉 项目已成功上传到GitHub！
            echo.
            echo 📍 仓库地址: %REPO_URL%
        ) else (
            echo ❌ 推送失败，请检查网络连接或仓库配置
        )
    ) else (
        echo ⏸️  已取消推送
    )
) else (
    echo 🔗 尚未配置远程仓库
    echo.
    echo 请按以下步骤配置：
    echo 1. 在GitHub创建新仓库
    echo 2. 复制仓库URL
    echo 3. 运行以下命令：
    echo.
    echo    git remote add origin https://github.com/你的用户名/tea-house-lite.git
    echo    git push -u origin main
    echo.
)

echo.
echo ========================================
echo ✅ 准备工作完成！
echo ========================================
echo.
echo 已上传的文件：
echo   ✓ .gitignore
echo   ✓ README.md
echo   ✓ DEPLOY.md
echo   ✓ UPLOAD_GUIDE.md
echo   ✓ requirements.txt
echo   ✓ app.py
echo.
echo 文件总数: 6个
echo 项目大小: 约 60 KB
echo.
pause
