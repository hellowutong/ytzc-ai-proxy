# ============== Proxy API Dockerfile ==============
# 支持多阶段构建，优化镜像大小

# ---------- 构建阶段 ----------
FROM python:3.11-slim AS builder

WORKDIR /build

# 安装构建依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# 复制应用代码
COPY . .

# ---------- 运行阶段 ----------
FROM python:3.11-slim AS production

# 安全：创建非root用户
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# 从构建阶段复制安装的包
COPY --from=builder /install /usr/local
COPY --from=builder /build /app

# 设置文件权限
RUN chown -R appuser:appgroup /app

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# 环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 启动命令（生产模式）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]

# ---------- 开发变体 ----------
FROM production AS development

# 重新切换回root用户以支持热重载
USER root

# 安装开发依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# 重新复制代码（覆盖生产代码）
COPY . .

# 设置权限
RUN chown -R appuser:appgroup /app

USER appuser

# 开发模式启动（带热重载）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload", "--log-level", "debug"]
