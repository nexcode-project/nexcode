#!/usr/bin/env python3
"""
MongoDB 管理脚本
用于连接、查询和管理协作文档平台的MongoDB数据
"""

import asyncio
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from datetime import datetime
import json

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo import MongoClient
except ImportError:
    print("❌ 请先安装 MongoDB 驱动:")
    print("pip install motor pymongo")
    sys.exit(1)

console = Console()

# MongoDB 配置
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/nexcode_docs")
DATABASE_NAME = "nexcode_docs"

class MongoDBManager:
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """连接MongoDB"""
        try:
            self.client = AsyncIOMotorClient(MONGODB_URL)
            self.db = self.client[DATABASE_NAME]
            
            # 测试连接
            await self.client.admin.command('ping')
            console.print("✅ MongoDB 连接成功", style="green")
            return True
        except Exception as e:
            console.print(f"❌ MongoDB 连接失败: {e}", style="red")
            return False
    
    async def close(self):
        """关闭连接"""
        if self.client:
            self.client.close()
    
    async def list_collections(self):
        """列出所有集合"""
        collections = await self.db.list_collection_names()
        
        table = Table(title="MongoDB 集合列表")
        table.add_column("集合名", style="cyan")
        table.add_column("文档数量", style="green")
        table.add_column("描述", style="yellow")
        
        collection_descriptions = {
            "documents": "协作文档",
            "document_versions": "文档版本历史",
            "document_collaborators": "文档协作者",
            "document_comments": "文档评论",
            "document_sessions": "文档编辑会话"
        }
        
        for collection_name in collections:
            count = await self.db[collection_name].count_documents({})
            description = collection_descriptions.get(collection_name, "系统集合")
            table.add_row(collection_name, str(count), description)
        
        console.print(table)
    
    async def view_documents(self, collection_name: str, limit: int = 10):
        """查看集合中的文档"""
        try:
            cursor = self.db[collection_name].find({}).limit(limit)
            documents = await cursor.to_list(length=limit)
            
            if not documents:
                console.print(f"📝 集合 '{collection_name}' 中没有文档", style="yellow")
                return
            
            console.print(f"\n📊 集合 '{collection_name}' 中的文档 (显示前 {len(documents)} 条):")
            
            for i, doc in enumerate(documents, 1):
                # 格式化文档显示
                doc_str = json.dumps(doc, indent=2, ensure_ascii=False, default=str)
                panel = Panel(
                    Syntax(doc_str, "json", theme="monokai"),
                    title=f"文档 {i}",
                    border_style="blue"
                )
                console.print(panel)
                
        except Exception as e:
            console.print(f"❌ 查询失败: {e}", style="red")
    
    async def create_sample_document(self):
        """创建示例文档"""
        sample_doc = {
            "title": "示例文档",
            "content": "# 这是一个示例文档\n\n这是文档的内容。",
            "owner_id": "sample_user_id",
            "collaborators": [
                {
                    "user_id": "collaborator_1",
                    "permission": "editor",
                    "added_at": datetime.utcnow()
                }
            ],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "version": 1,
            "status": "active"
        }
        
        try:
            result = await self.db.documents.insert_one(sample_doc)
            console.print(f"✅ 示例文档创建成功，ID: {result.inserted_id}", style="green")
        except Exception as e:
            console.print(f"❌ 创建示例文档失败: {e}", style="red")
    
    async def search_documents(self, query: str):
        """搜索文档"""
        try:
            # 文本搜索
            cursor = self.db.documents.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})])
            
            documents = await cursor.to_list(length=10)
            
            if not documents:
                console.print(f"📝 没有找到包含 '{query}' 的文档", style="yellow")
                return
            
            console.print(f"\n🔍 搜索结果 (关键词: '{query}'):")
            
            for i, doc in enumerate(documents, 1):
                score = doc.get("score", 0)
                title = doc.get("title", "无标题")
                content_preview = doc.get("content", "")[:100] + "..." if len(doc.get("content", "")) > 100 else doc.get("content", "")
                
                table = Table(title=f"结果 {i} (相关度: {score:.2f})")
                table.add_column("字段", style="cyan")
                table.add_column("值", style="green")
                
                table.add_row("标题", title)
                table.add_row("内容预览", content_preview)
                table.add_row("创建时间", str(doc.get("created_at", "N/A")))
                table.add_row("状态", doc.get("status", "N/A"))
                
                console.print(table)
                
        except Exception as e:
            console.print(f"❌ 搜索失败: {e}", style="red")
    
    async def get_database_stats(self):
        """获取数据库统计信息"""
        try:
            stats = await self.db.command("dbStats")
            
            table = Table(title="数据库统计信息")
            table.add_column("指标", style="cyan")
            table.add_column("值", style="green")
            
            table.add_row("数据库名称", stats.get("db", "N/A"))
            table.add_row("集合数量", str(stats.get("collections", 0)))
            table.add_row("文档总数", str(stats.get("objects", 0)))
            table.add_row("数据大小", f"{stats.get('dataSize', 0)} bytes")
            table.add_row("存储大小", f"{stats.get('storageSize', 0)} bytes")
            table.add_row("索引大小", f"{stats.get('indexSize', 0)} bytes")
            
            console.print(table)
            
        except Exception as e:
            console.print(f"❌ 获取统计信息失败: {e}", style="red")

async def main():
    """主函数"""
    console.print("🗄️ NexCode MongoDB 管理工具", style="bold blue")
    console.print("=" * 50)
    
    manager = MongoDBManager()
    
    # 连接数据库
    if not await manager.connect():
        return
    
    try:
        while True:
            console.print("\n请选择操作：")
            console.print("1. 查看所有集合")
            console.print("2. 查看集合文档")
            console.print("3. 创建示例文档")
            console.print("4. 搜索文档")
            console.print("5. 查看数据库统计")
            console.print("6. 查看集合结构")
            console.print("0. 退出")
            
            choice = input("\n请输入选择 (0-6): ").strip()
            
            try:
                if choice == "0":
                    console.print("👋 再见！")
                    break
                elif choice == "1":
                    await manager.list_collections()
                elif choice == "2":
                    collection_name = input("请输入集合名: ").strip()
                    if collection_name:
                        limit = input("请输入显示数量 (默认10): ").strip()
                        limit = int(limit) if limit.isdigit() else 10
                        await manager.view_documents(collection_name, limit)
                    else:
                        console.print("❌ 请输入集合名", style="red")
                elif choice == "3":
                    await manager.create_sample_document()
                elif choice == "4":
                    query = input("请输入搜索关键词: ").strip()
                    if query:
                        await manager.search_documents(query)
                    else:
                        console.print("❌ 请输入搜索关键词", style="red")
                elif choice == "5":
                    await manager.get_database_stats()
                elif choice == "6":
                    console.print("📋 MongoDB 集合结构说明:", style="bold")
                    console.print("""
📁 documents - 协作文档
  ├── _id: ObjectId (主键)
  ├── title: String (文档标题)
  ├── content: String (文档内容)
  ├── owner_id: String (所有者ID)
  ├── collaborators: Array (协作者列表)
  ├── created_at: Date (创建时间)
  ├── updated_at: Date (更新时间)
  ├── version: Number (版本号)
  └── status: String (状态)

📁 document_versions - 文档版本
  ├── _id: ObjectId (主键)
  ├── document_id: ObjectId (文档ID)
  ├── version_number: Number (版本号)
  ├── content: String (版本内容)
  ├── changed_by: String (修改者)
  └── created_at: Date (创建时间)

📁 document_collaborators - 协作者
  ├── _id: ObjectId (主键)
  ├── document_id: ObjectId (文档ID)
  ├── user_id: String (用户ID)
  ├── permission: String (权限)
  └── added_at: Date (添加时间)

📁 document_comments - 评论
  ├── _id: ObjectId (主键)
  ├── document_id: ObjectId (文档ID)
  ├── user_id: String (用户ID)
  ├── content: String (评论内容)
  └── created_at: Date (创建时间)

📁 document_sessions - 编辑会话
  ├── _id: ObjectId (主键)
  ├── document_id: ObjectId (文档ID)
  ├── user_id: String (用户ID)
  ├── session_id: String (会话ID)
  └── last_activity: Date (最后活动时间)
                    """)
                else:
                    console.print("❌ 无效选择，请重新输入", style="red")
                    
            except Exception as e:
                console.print(f"❌ 操作失败: {e}", style="red")
                
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(main()) 