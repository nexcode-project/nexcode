#!/usr/bin/env python3
"""
MongoDB 初始化脚本
用于本地MongoDB的初始化和配置
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

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

async def init_mongodb():
    """初始化MongoDB数据库"""
    print("🗄️ 初始化 MongoDB 数据库...")
    
    try:
        # 连接MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        # 测试连接
        await client.admin.command('ping')
        print("✅ MongoDB 连接成功")
        
        # 创建集合
        collections = [
            "documents",
            "document_versions", 
            "document_collaborators",
            "document_comments",
            "document_sessions"
        ]
        
        for collection_name in collections:
            # 检查集合是否存在，如果不存在则创建
            if collection_name not in await db.list_collection_names():
                await db.create_collection(collection_name)
                print(f"✅ 创建集合: {collection_name}")
            else:
                print(f"📝 集合已存在: {collection_name}")
        
        # 创建索引
        print("\n🔍 创建索引...")
        
        # documents 集合索引
        await db.documents.create_index("owner_id")
        await db.documents.create_index([("title", "text"), ("content", "text")])
        await db.documents.create_index([("created_at", -1)])
        await db.documents.create_index([("updated_at", -1)])
        print("✅ documents 索引创建完成")
        
        # document_versions 集合索引
        await db.document_versions.create_index([("document_id", 1), ("version_number", -1)])
        await db.document_versions.create_index("changed_by")
        print("✅ document_versions 索引创建完成")
        
        # document_collaborators 集合索引
        await db.document_collaborators.create_index("document_id")
        await db.document_collaborators.create_index("user_id")
        await db.document_collaborators.create_index([("document_id", 1), ("user_id", 1)], unique=True)
        print("✅ document_collaborators 索引创建完成")
        
        # document_comments 集合索引
        await db.document_comments.create_index("document_id")
        await db.document_comments.create_index("user_id")
        await db.document_comments.create_index([("created_at", -1)])
        print("✅ document_comments 索引创建完成")
        
        # document_sessions 集合索引
        await db.document_sessions.create_index("document_id")
        await db.document_sessions.create_index("user_id")
        await db.document_sessions.create_index("session_id", unique=True)
        print("✅ document_sessions 索引创建完成")
        
        # 创建示例数据
        print("\n📝 创建示例数据...")
        await create_sample_data(db)
        
        print("\n🎉 MongoDB 初始化完成!")
        print(f"📊 数据库: {DATABASE_NAME}")
        print(f"📁 集合: {', '.join(collections)}")
        print("🔍 索引: 已创建必要的索引")
        print("📝 示例数据: 已创建")
        
        client.close()
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False
    
    return True

async def create_sample_data(db):
    """创建示例数据"""
    try:
        # 创建示例文档
        sample_document = {
            "title": "NexCode 协作文档平台介绍",
            "content": """# NexCode 协作文档平台

## 项目简介
NexCode 是一个现代化的协作文档平台，支持实时协作编辑、版本控制和AI助手功能。

## 主要功能
- 📝 富文本编辑器
- 👥 实时协作编辑
- 📚 版本控制和历史记录
- 🔐 细粒度权限管理
- 🤖 AI写作助手
- 🔍 全文搜索

## 技术栈
- 后端: FastAPI + MongoDB
- 前端: React + TypeScript
- 实时通信: WebSocket
- AI集成: OpenAI API

欢迎使用！""",
            "owner_id": "admin_user",
            "collaborators": [
                {
                    "user_id": "demo_user",
                    "permission": "editor",
                    "added_at": datetime.utcnow()
                }
            ],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "version": 1,
            "status": "active",
            "tags": ["介绍", "功能", "技术"]
        }
        
        # 插入示例文档
        result = await db.documents.insert_one(sample_document)
        print(f"✅ 创建示例文档: {sample_document['title']}")
        
        # 创建文档版本
        version_doc = {
            "document_id": result.inserted_id,
            "version_number": 1,
            "content": sample_document["content"],
            "title": sample_document["title"],
            "changed_by": "admin_user",
            "change_description": "初始版本",
            "created_at": datetime.utcnow()
        }
        
        await db.document_versions.insert_one(version_doc)
        print("✅ 创建文档版本记录")
        
        # 创建示例评论
        comment_doc = {
            "document_id": result.inserted_id,
            "user_id": "demo_user",
            "content": "这是一个很棒的项目介绍文档！",
            "created_at": datetime.utcnow()
        }
        
        await db.document_comments.insert_one(comment_doc)
        print("✅ 创建示例评论")
        
    except Exception as e:
        print(f"❌ 创建示例数据失败: {e}")

def check_mongodb_connection():
    """检查MongoDB连接"""
    try:
        client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        client.close()
        return True
    except Exception as e:
        print(f"❌ MongoDB 连接失败: {e}")
        return False

async def main():
    """主函数"""
    print("🗄️ NexCode MongoDB 初始化工具")
    print("=" * 50)
    
    # 检查MongoDB连接
    if not check_mongodb_connection():
        print("\n💡 请确保 MongoDB 服务正在运行:")
        print("sudo systemctl start mongod")
        print("sudo systemctl status mongod")
        return
    
    # 初始化数据库
    success = await init_mongodb()
    
    if success:
        print("\n🚀 下一步:")
        print("1. 运行管理脚本: python scripts/mongo_manager.py")
        print("2. 开始开发协作文档功能")
        print("3. 在FastAPI中集成MongoDB")

if __name__ == "__main__":
    asyncio.run(main()) 