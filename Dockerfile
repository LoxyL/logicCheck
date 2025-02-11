# 使用精简版Python基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 只复制必要文件
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY requirements.txt /app/

# 安装依赖并清理缓存
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache/pip

# 设置工作目录为backend
WORKDIR /app/backend

# 暴露端口
EXPOSE 8402

# 启动应用
CMD ["python", "app.py"] 