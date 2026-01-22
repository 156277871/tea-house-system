# 连锁茶楼管理系统 V4.1.2 - 安装说明

## 📦 压缩包内容

本次更新包含以下文件：
1. **app.py** - 主应用文件（V4.1.2版本）
2. **init_sample_data.py** - 数据初始化脚本
3. **README_V4.1.2.md** - 版本说明文档
4. **USAGE_GUIDE.md** - 使用指南
5. **requirements.txt** - Python依赖列表

## 🚀 安装步骤

### 1. 解压文件
```bash
tar -xzf tea_house_lite_v4.1.2.tar.gz
```

解压后会得到以下文件：
- app.py
- init_sample_data.py
- README_V4.1.2.md
- USAGE_GUIDE.md
- requirements.txt

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

或者手动安装：
```bash
pip install streamlit sqlalchemy pandas
```

### 3. 初始化示例数据（推荐）
```bash
python init_sample_data.py
```

**成功后会显示**：
```
✅ 示例数据初始化完成！
门店数: 6
商品数: 18
会员数: 8
订单数: 20
```

### 4. 启动系统
```bash
streamlit run app.py
```

浏览器会自动打开，访问：http://localhost:8501

## 📋 V4.1.2 新功能

### 1. 库存台账页面
- **库存流水**：查看所有库存变动记录，支持点击查看详情
- **库存详情**：查看各门店库存，支持点击商品查看流水历史
- **自动记录**：入库和结账时自动记录库存流水

### 2. 示例数据
- 6家门店
- 18种商品（茶叶、花茶、零食、菜品）
- 8名会员（不同等级）
- 20条订单
- 198条库存流水记录
- 48个桌台
- 8名员工

### 3. 点击查看详情功能
- 库存流水记录详情
- 商品库存流水历史
- 库存变动对比

## 📖 使用说明

详细使用说明请查看：
- **README_V4.1.2.md** - 版本功能和快速开始
- **USAGE_GUIDE.md** - 详细使用指南和业务场景

## ⚠️ 注意事项

1. **数据库文件**：
   - 首次运行会自动创建 `tea_house.db`
   - 如需重新初始化数据，删除 `tea_house.db` 后重新运行 `init_sample_data.py`

2. **数据备份**：
   - 建议定期备份 `tea_house.db` 文件
   - 备份命令：`cp tea_house.db tea_house_backup.db`

3. **端口占用**：
   - 默认端口为 8501
   - 如需修改端口：`streamlit run app.py --server.port 8080`

## 🔄 从旧版本升级

如果你已有旧版本：

1. **备份数据**：
   ```bash
   cp tea_house.db tea_house_backup.db
   ```

2. **替换文件**：
   - 备份旧的 app.py
   - 使用新的 app.py 替换

3. **运行系统**：
   ```bash
   streamlit run app.py
   ```

4. **可选**：如果需要示例数据，运行：
   ```bash
   python init_sample_data.py
   ```
   ⚠️ 注意：这会添加新的示例数据，不会覆盖现有数据

## 🐛 常见问题

**Q: 运行 init_sample_data.py 报错？**
A: 确保已安装所有依赖：`pip install -r requirements.txt`

**Q: 启动后看不到示例数据？**
A: 检查是否成功运行了 `python init_sample_data.py`

**Q: 如何清除所有数据重新开始？**
A:
   ```bash
   rm tea_house.db
   python init_sample_data.py
   ```

**Q: 库存流水记录在哪里？**
A: 进入"📦 库存台账" > "库存流水"标签查看

**Q: 如何查看某个商品的库存历史？**
A: 进入"📦 库存台账" > "库存详情"，点击商品的"🔍 查看详情"

## 📞 技术支持

如有问题，请查看：
- USAGE_GUIDE.md - 详细使用指南
- README_V4.1.2.md - 功能说明

---

**版本**：V4.1.2
**更新日期**：2026-01-22
**技术栈**：Python + Streamlit + SQLAlchemy + SQLite
