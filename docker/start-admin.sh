#!/bin/bash

# NexCode Admin 启动脚本
echo "🚀 启动 NexCode Admin 服务..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 检查docker-compose.yml是否存在
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 未找到 docker-compose.yml 文件"
    echo "请确保在 docker 目录下运行此脚本"
    exit 1
fi

# 构建并启动admin服务
echo "📦 构建 admin 服务..."
docker-compose build nexcode_admin

echo "🚀 启动 admin 服务..."
docker-compose up -d nexcode_admin

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
if docker-compose ps nexcode_admin | grep -q "Up"; then
    echo "✅ NexCode Admin 启动成功！"
    echo "🌐 访问地址: http://localhost:5433"
    echo "🔑 默认管理员账号: admin / admin"
    echo ""
    echo "📋 其他服务:"
    echo "   Web界面: http://localhost:3000"
    echo "   API文档: http://localhost:8000/docs"
    echo "   MongoDB管理: http://localhost:8081"
else
    echo "❌ Admin 服务启动失败"
    echo "📋 查看日志: docker-compose logs nexcode_admin"
    exit 1
fi 