---
title: 连锁茶楼管理系统
emoji: 🏪
colorFrom: green
colorTo: yellow
sdk: streamlit
sdk_version: 1.28.0
app_file: app.py
pinned: false
license: mit
---

# 🏪 连锁茶楼管理系统

基于 Streamlit 的轻量级连锁茶楼管理系统，**完全免费部署到 Hugging Face Spaces！**

## ✨ 功能特性

- 📊 **控制台** - 实时监控营业数据
- 🏪 **门店管理** - 创建和管理门店信息
- 👥 **员工管理** - 员工档案管理
- 💎 **会员管理** - 会员信息与充值
- 🛍️ **商品管理** - 商品分类管理
- 📦 **库存管理** - 库存监控与入库
- 📝 **订单管理** - 订单创建与查询
- 💰 **财务报表** - 数据分析

## 🚀 如何使用

### 本地运行（推荐使用启动脚本）

#### Windows 系统
双击运行 `run_app.bat` 文件，或在命令行中执行：
```bash
run_app.bat
```

#### Linux/Mac 系统
在终端中执行：
```bash
chmod +x run_app.sh
./run_app.sh
```

#### 手动启动
```bash
pip install -r requirements.txt
streamlit run app.py
```

启动成功后，在浏览器中访问：**http://localhost:8501**

### 部署到 Hugging Face Spaces
1. 注册 Hugging Face 账号：https://huggingface.co/join
2. 创建新的 Space：https://huggingface.co/new-space
3. 选择 SDK：Streamlit
4. 上传所有文件（app.py, requirements.txt, README.md）
5. 等待自动部署完成（约2-3分钟）

## 📝 使用顺序

1. **创建门店** - 先建立基础门店信息
2. **创建商品** - 添加商品和价格
3. **创建员工** - 分配员工到各门店
4. **创建会员** - 建立会员档案
5. **库存入库** - 为各门店补充库存
6. **创建订单** - 开始日常销售业务

## 💡 特色

✅ **完全免费** - 无需购买服务器或域名  
✅ **无需GitHub** - 直接在 Hugging Face 上传文件  
✅ **开箱即用** - 无需配置数据库  
✅ **操作简单** - 直观易用的界面  

## ⚠️ 注意事项

- 本系统使用 SQLite 数据库，每次 Space 重启后数据会重置
- 如需数据持久化，建议定期导出数据或升级到付费版本
- 免费版 Space 有一定的流量和运行时间限制

## 🔧 故障排除

### 问题：应用启动失败或显示 "Error running app"

**解决方案 1：清理旧进程**
- Windows：在任务管理器中结束所有 `streamlit.exe` 和 `python.exe` 进程
- Linux/Mac：执行 `pkill -9 streamlit` 清理旧进程

**解决方案 2：使用启动脚本**
- Windows：双击运行 `run_app.bat`
- Linux/Mac：执行 `./run_app.sh`

**解决方案 3：检查依赖**
```bash
pip install -r requirements.txt --upgrade
```

**解决方案 4：清理 Streamlit 缓存**
```bash
rm -rf .streamlit/
streamlit run app.py
```

### 问题：端口已被占用

如果 8501 端口被占用，可以指定其他端口：
```bash
streamlit run app.py --server.port 8502
```

### 问题：数据库文件损坏

删除旧数据库文件，让应用重新创建：
```bash
rm tea_house.db
streamlit run app.py
```

### 问题：页面显示异常

尝试清理浏览器缓存：
- 按 `Ctrl + F5` 强制刷新页面
- 或使用无痕模式打开应用

## 📄 许可证

MIT License
