# 快速启动脚本
# 1. 启动docker-compose
# 2. 安装Python依赖
# 3. 启动后端服务

echo "🚀 AI网关启动脚本"
echo "=================="

# 检查Docker是否运行
if (! docker stats --no-stream 2>&1 | grep -q "CONTAINER ID"); then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 启动基础设施
echo "📦 步骤1: 启动基础设施 (MongoDB/Redis/Qdrant/Searxng/LibreX/4get)..."
cd ../docker
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 安装Python依赖
echo "📥 步骤2: 安装Python依赖..."
cd ../backend
python -m pip install -r requirements.txt

# 启动后端服务
echo "🚀 步骤3: 启动后端服务..."
python main.py
