# 部署指南

本文档介绍连锁茶楼管理系统V4.1的部署方案。

## 目录

- [本地部署](#本地部署)
- [Docker部署](#docker部署)
- [云平台部署](#云平台部署)
- [常见问题](#常见问题)

---

## 本地部署

### 方法一：直接运行（推荐）

1. **安装Python环境**
   ```bash
   # 确保Python版本 >= 3.7
   python --version
   ```

2. **克隆项目**
   ```bash
   git clone <repository-url>
   cd tea_house_lite
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **运行应用**
   ```bash
   streamlit run app.py
   ```

5. **访问应用**
   - 本地访问: http://localhost:8501
   - 局域网访问: http://<your-ip>:8501

### 方法二：虚拟环境（推荐）

1. **创建虚拟环境**
   ```bash
   # Windows
   python -m venv venv

   # Linux/Mac
   python3 -m venv venv
   ```

2. **激活虚拟环境**
   ```bash
   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **安装依赖并运行**
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

---

## Docker部署

### 1. 创建Dockerfile

在项目根目录创建 `Dockerfile`：

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app.py .

# 暴露端口
EXPOSE 8501

# 运行应用
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. 构建镜像

```bash
docker build -t tea-house-lite .
```

### 3. 运行容器

```bash
docker run -d \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  --name tea-house \
  tea-house-lite
```

### 4. 使用Docker Compose（推荐）

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  tea-house:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

运行：
```bash
docker-compose up -d
```

---

## 云平台部署

### Streamlit Cloud

1. **准备代码**
   - 将代码推送到GitHub
   - 确保有 `requirements.txt`

2. **部署步骤**
   - 访问 https://share.streamlit.io
   - 连接GitHub账号
   - 选择仓库
   - 点击"Deploy"

3. **配置**（可选）
   - 添加环境变量
   - 配置域名

### 其他云平台

系统基于Streamlit，可以部署到支持Python的任何平台：

- **Heroku**: 需要添加 `Procfile`
- **PythonAnywhere**: 支持Streamlit
- **Railway**: 一键部署
- **Render**: 免费额度

---

## 配置选项

### Streamlit配置文件

创建 `.streamlit/config.toml`：

```toml
[server]
port = 8501
address = "0.0.0.0"
headless = true

[theme]
base = "light"
primaryColor = "#ff6b6b"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8f9fa"
textColor = "#1f1f1f"
font = "sans serif"
```

### 环境变量

- `STREAMLIT_SERVER_PORT`: 服务端口（默认8501）
- `STREAMLIT_SERVER_ADDRESS`: 服务地址（默认localhost）

---

## 数据备份

### 数据库备份

```bash
# 备份
cp tea_house.db tea_house_backup_$(date +%Y%m%d).db

# 恢复
cp tea_house_backup_YYYYMMDD.db tea_house.db
```

### 定期备份脚本

创建 `backup.sh`：

```bash
#!/bin/bash
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR
cp tea_house.db $BACKUP_DIR/tea_house_$(date +%Y%m%d_%H%M%S).db
# 保留最近7天的备份
find $BACKUP_DIR -name "tea_house_*.db" -mtime +7 -delete
```

添加到crontab：
```bash
0 2 * * * /path/to/backup.sh
```

---

## 常见问题

### 1. 端口被占用

```bash
# 查找占用端口的进程
lsof -i :8501

# 或使用其他端口
streamlit run app.py --server.port=8502
```

### 2. 数据库文件权限错误

```bash
# 修改权限
chmod 644 tea_house.db
```

### 3. 依赖安装失败

```bash
# 使用清华源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. 无法局域网访问

```bash
# 允许外网访问
streamlit run app.py --server.address=0.0.0.0
```

### 5. Streamlit版本不兼容

```bash
# 卸载旧版本
pip uninstall streamlit

# 安装指定版本
pip install streamlit==1.28.0
```

---

## 性能优化

### 1. 数据库优化

- 定期清理旧数据
- 添加索引（已内置）
- 使用连接池

### 2. 应用优化

- 启用缓存
- 减少不必要的数据加载
- 使用异步操作

---

## 安全建议

1. **数据备份**: 定期备份数据库
2. **访问控制**: 在反向代理层添加认证
3. **HTTPS**: 生产环境使用HTTPS
4. **防火墙**: 限制访问端口
5. **更新**: 定期更新依赖包

---

## 技术支持

- 文档: 查看 README.md
- 问题: 提交 GitHub Issue
- 邮件: support@example.com

---

**祝部署顺利！🎉**
