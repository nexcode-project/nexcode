#!/bin/bash

# NexCode Admin 配置测试脚本
echo "🔍 测试 NexCode Admin 配置..."

# 检查端口配置
echo "📋 端口配置检查:"
echo "   - Admin服务端口: 5433"
echo "   - API服务端口: 8000"
echo "   - Web服务端口: 3000"

# 检查Docker配置
echo ""
echo "🐳 Docker配置检查:"
if [ -f "docker-compose.yml" ]; then
    echo "✅ docker-compose.yml 存在"
    
    # 检查admin服务配置
    if grep -q "nexcode_admin:" docker-compose.yml; then
        echo "✅ nexcode_admin 服务已配置"
        
        # 检查端口映射
        if grep -q "5433:5433" docker-compose.yml; then
            echo "✅ 端口映射正确 (5433:5433)"
        else
            echo "❌ 端口映射配置错误"
        fi
        
        # 检查环境变量
        if grep -q "VITE_API_BASE_URL=http://localhost:8000" docker-compose.yml; then
            echo "✅ API基础URL配置正确"
        else
            echo "❌ API基础URL配置错误"
        fi
    else
        echo "❌ nexcode_admin 服务未配置"
    fi
else
    echo "❌ docker-compose.yml 不存在"
fi

# 检查Dockerfile
echo ""
echo "📦 Dockerfile检查:"
if [ -f "nexcode_admin/Dockerfile" ]; then
    echo "✅ nexcode_admin Dockerfile 存在"
    
    if grep -q "EXPOSE 5433" nexcode_admin/Dockerfile; then
        echo "✅ 端口暴露配置正确"
    else
        echo "❌ 端口暴露配置错误"
    fi
else
    echo "❌ nexcode_admin Dockerfile 不存在"
fi

# 检查Vite配置
echo ""
echo "⚙️ Vite配置检查:"
if [ -f "../nexcode_admin/vite.config.ts" ]; then
    echo "✅ vite.config.ts 存在"
    
    if grep -q "port: 5433" ../nexcode_admin/vite.config.ts; then
        echo "✅ 开发服务器端口配置正确"
    else
        echo "❌ 开发服务器端口配置错误"
    fi
    
    if grep -q "VITE_API_BASE_URL.*localhost:8000" ../nexcode_admin/vite.config.ts; then
        echo "✅ API基础URL配置正确"
    else
        echo "❌ API基础URL配置错误"
    fi
else
    echo "❌ vite.config.ts 不存在"
fi

echo ""
echo "🎯 配置总结:"
echo "   Admin服务将在端口 5433 运行"
echo "   连接到后端API (端口 8000)"
echo "   可以通过 http://localhost:5433 访问" 