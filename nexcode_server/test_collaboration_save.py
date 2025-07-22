#!/usr/bin/env python3
"""
测试协作编辑中的智能保存策略
模拟多个用户同时编辑文档的场景
"""

import asyncio
import sys
import os
import time

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.document_storage_service import DocumentStorageService
from app.services.collaboration_service import CollaborationManager
from app.core.database import get_db
from app.models.document_models import Document
from app.models.database import User
from sqlalchemy import select
from app.models.document_models import DocumentVersion, DocumentOperation


async def simulate_collaboration_editing():
    """模拟协作编辑场景"""
    print("🧪 开始模拟协作编辑场景...")
    
    # 创建服务实例
    storage_service = DocumentStorageService()
    collaboration_manager = CollaborationManager()
    
    # 创建测试用户和文档
    async for db in get_db():
        # 查找测试用户
        stmt = select(User).where(User.username == "demo")
        result = await db.execute(stmt)
        user1 = result.scalar_one_or_none()
        
        if not user1:
            print("❌ 测试用户不存在，请先运行用户创建脚本")
            return
        
        # 创建测试文档
        test_document = Document(
            title="协作编辑测试文档",
            content="这是一个协作编辑测试文档。",
            owner_id=user1.id,
            version=1
        )
        db.add(test_document)
        await db.commit()
        await db.refresh(test_document)
        
        document_id = test_document.id
        user1_id = user1.id
        user2_id = 999  # 模拟第二个用户
        
        print(f"✅ 创建测试文档: ID={document_id}")
        break
    
    try:
        print("\n👥 模拟两个用户开始协作编辑...")
        
        # 初始化文档锁
        collaboration_manager.document_locks[document_id] = asyncio.Lock()
        
        # 用户1开始编辑
        print("👤 用户1开始编辑...")
        content1 = "这是一个协作编辑测试文档。用户1正在编辑这个文档。"
        await collaboration_manager.handle_content_update(document_id, user1_id, content1)
        await asyncio.sleep(0.5)
        
        # 用户2开始编辑
        print("👤 用户2开始编辑...")
        content2 = "这是一个协作编辑测试文档。用户1正在编辑这个文档。用户2也加入了编辑！"
        await collaboration_manager.handle_content_update(document_id, user2_id, content2)
        await asyncio.sleep(0.5)
        
        # 用户1继续编辑
        print("👤 用户1继续编辑...")
        content3 = "这是一个协作编辑测试文档。用户1正在编辑这个文档。用户2也加入了编辑！现在用户1添加了更多内容。"
        await collaboration_manager.handle_content_update(document_id, user1_id, content3)
        await asyncio.sleep(0.5)
        
        # 用户2完成一个句子
        print("👤 用户2完成一个句子...")
        content4 = "这是一个协作编辑测试文档。用户1正在编辑这个文档。用户2也加入了编辑！现在用户1添加了更多内容。用户2完成了这个句子！"
        await collaboration_manager.handle_content_update(document_id, user2_id, content4)
        await asyncio.sleep(0.5)
        
        # 等待一段时间让后台处理完成
        print("⏰ 等待后台处理完成...")
        await asyncio.sleep(2)
        
        # 验证保存结果
        print("\n🔍 验证协作编辑保存结果...")
        versions = await storage_service.get_document_versions(document_id)
        print(f"📊 版本数量: {len(versions)}")
        
        for i, version in enumerate(versions):
            print(f"  版本 {version.version_number}: {version.change_description}")
            print(f"    内容长度: {len(version.content)}")
            print(f"    修改者: {version.changed_by}")
            print(f"    修改时间: {version.created_at}")
        
        # 获取文档统计
        stats = await storage_service.get_document_statistics(document_id)
        print(f"\n📈 文档统计:")
        print(f"  当前版本: {stats.get('current_version', 'N/A')}")
        print(f"  版本数量: {stats.get('version_count', 'N/A')}")
        print(f"  内容长度: {stats.get('content_length', 'N/A')}")
        print(f"  最后编辑者: {stats.get('last_editor_id', 'N/A')}")
        
        print("\n✅ 协作编辑智能保存测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试文档
        async for db in get_db():
            try:
                # 先删除版本记录
                stmt = select(DocumentVersion).where(DocumentVersion.document_id == document_id)
                result = await db.execute(stmt)
                versions = result.scalars().all()
                for version in versions:
                    await db.delete(version)
                
                # 再删除操作记录
                stmt = select(DocumentOperation).where(DocumentOperation.document_id == document_id)
                result = await db.execute(stmt)
                operations = result.scalars().all()
                for operation in operations:
                    await db.delete(operation)
                
                # 最后删除文档
                stmt = select(Document).where(Document.id == document_id)
                result = await db.execute(stmt)
                document = result.scalar_one_or_none()
                
                if document:
                    await db.delete(document)
                
                await db.commit()
                print(f"🧹 清理测试文档: {document_id}")
            except Exception as e:
                print(f"⚠️ 清理文档时出错: {e}")
                await db.rollback()
            break
        
        # 关闭存储服务
        await storage_service.shutdown()


if __name__ == "__main__":
    asyncio.run(simulate_collaboration_editing()) 