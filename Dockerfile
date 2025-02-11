# 使用Python基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY requirements.txt /app/

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 8402

# 启动命令
CMD ["python", "backend/app.py"] 