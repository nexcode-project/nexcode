#!/bin/bash

# 数据库设置脚本
# 用于一键创建和初始化数据库

set -e  # 遇到错误立即退出

echo "🚀 开始设置数据库..."
echo "=================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -f "app/main.py" ]; then
    echo "❌ 请在 nexcode_server 目录下运行此脚本"
    exit 1
fi

# 安装依赖
echo "📦 检查依赖..."
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements_server.txt

echo "✅ 依赖检查完成"
echo

# 创建数据库
echo "🗄️  创建数据库..."
python3 scripts/create_database.py

if [ $? -ne 0 ]; then
    echo "❌ 数据库创建失败"
    exit 1
fi

echo "✅ 数据库创建完成"
echo

# 运行迁移
echo "🔄 运行数据库迁移..."
python3 scripts/create_migration.py

if [ $? -ne 0 ]; then
    echo "❌ 数据库迁移失败"
    exit 1
fi

echo "✅ 数据库迁移完成"
echo

# 初始化数据
echo "🌱 初始化数据..."
python3 scripts/init_db.py

if [ $? -ne 0 ]; then
    echo "❌ 数据初始化失败"
    exit 1
fi

echo "✅ 数据初始化完成"
echo

echo "🎉 数据库设置完成！"
echo "=================================="
echo
echo "📋 接下来可以:"
echo "   1. 启动服务: uvicorn app.main:app --reload"
echo "   2. 访问文档: http://localhost:8000/docs"
echo "   3. 使用以下账户登录:"
echo "      管理员: admin / admin"
echo "      演示用户: demo / demo123"
echo