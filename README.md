# LogicCheck

一键文档检查工具

## 快速部署

### 方法1：使用 Docker（推荐）

```bash
docker pull 你的Docker用户名/logiccheck:latest
docker run -d -p 8402:8402 你的Docker用户名/logiccheck:latest
```

### 方法2：使用 docker-compose 部署

```bash
docker-compose up -d
```

### 访问应用

部署完成后，访问 http://localhost:8402 即可使用

## 环境要求

- Docker
- Docker Compose (可选)

## 配置说明

默认端口：8402
如需修改端口，请编辑 docker-compose.yml 文件
