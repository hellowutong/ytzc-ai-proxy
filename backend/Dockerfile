# AI Gateway Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建 skills 目录（如果不存在）
RUN mkdir -p /app/skills/system /app/skills/custom

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "main.py"]
