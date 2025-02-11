# 使用Python基础镜像
FROM python:3.8

# 设置工作目录
WORKDIR /app

# 复制整个项目到容器中
COPY . .

# 安装依赖
RUN pip install -r requirements.txt

# 设置工作目录为backend
WORKDIR /app/backend

# 暴露端口
EXPOSE 8402

# 启动应用
CMD ["python", "app.py"] 