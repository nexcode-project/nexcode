#!/usr/bin/env python3
"""
MongoDB 连接测试脚本
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo import MongoClient
except ImportError:
    print("❌ 请先安装 MongoDB 驱动:")
    print("pip install motor pymongo")
    sys.exit(1)

# MongoDB 配置
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "nexcode_docs"

async def test_mongodb_connection():
    """测试MongoDB连接"""
    print("🔍 测试 MongoDB 连接...")
    
    try:
        # 测试异步连接
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        # 测试连接
        await client.admin.command('ping')
        print("✅ MongoDB 异步连接成功")
        
        # 测试数据库操作
        collections = await db.list_collection_names()
        print(f"📁 数据库中的集合: {collections}")
        
        # 测试文档查询
        doc_count = await db.documents.count_documents({})
        print(f"📊 documents 集合中的文档数量: {doc_count}")
        
        # 测试文档查询
        if doc_count > 0:
            doc = await db.documents.find_one({})
            print(f"📝 示例文档标题: {doc.get('title', 'N/A')}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB 连接测试失败: {e}")
        return False

def test_sync_connection():
    """测试同步连接"""
    print("🔍 测试 MongoDB 同步连接...")
    
    try:
        client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ MongoDB 同步连接成功")
        
        db = client[DATABASE_NAME]
        collections = db.list_collection_names()
        print(f"📁 数据库中的集合: {collections}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB 同步连接测试失败: {e}")
        return False

async def main():
    """主函数"""
    print("🧪 MongoDB 连接测试工具")
    print("=" * 40)
    
    # 测试同步连接
    sync_success = test_sync_connection()
    
    # 测试异步连接
    async_success = await test_mongodb_connection()
    
    if sync_success and async_success:
        print("\n🎉 所有测试通过!")
        print("✅ MongoDB 已准备就绪")
        print("✅ 可以开始开发协作文档功能")
    else:
        print("\n❌ 部分测试失败")
        print("请检查 MongoDB 服务状态")

if __name__ == "__main__":
    asyncio.run(main()) 