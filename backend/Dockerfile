# CRM 销售管理系统 Docker 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 先安装依赖（利用 Docker 缓存层）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 数据目录：容器内的数据库文件存放路径（部署时映射到宿主机实现持久化）
ENV DATA_DIR=/app/data

# 暴露端口（云端平台通常通过 $PORT 注入，默认 8000）
EXPOSE 8000

# 使用 gunicorn + uvicorn worker 启动生产级服务
CMD gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --timeout 120
