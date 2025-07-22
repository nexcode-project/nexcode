#!/usr/bin/env python3
"""
测试智能保存策略
验证基于时间间隔、内容变化和句子完成的保存触发
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.document_storage_service import DocumentStorageService
from app.core.database import get_db
from app.models.document_models import Document
from app.models.database import User
from sqlalchemy import select
from datetime import datetime


async def test_smart_save_strategy():
    """测试智能保存策略"""
    print("🧪 开始测试智能保存策略...")
    
    # 创建文档存储服务实例
    storage_service = DocumentStorageService()
    
    # 创建测试用户和文档
    async for db in get_db():
        # 查找或创建测试用户
        stmt = select(User).where(User.username == "demo")
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ 测试用户不存在，请先运行用户创建脚本")
            return
        
        # 创建测试文档
        test_document = Document(
            title="智能保存测试文档",
            content="这是初始内容。",
            owner_id=user.id,
            version=1
        )
        db.add(test_document)
        await db.commit()
        await db.refresh(test_document)
        
        document_id = test_document.id
        user_id = user.id
        
        print(f"✅ 创建测试文档: ID={document_id}")
        break
    
    try:
        # 测试1: 初始保存
        print("\n📝 测试1: 初始保存")
        await storage_service.save_content(document_id, user_id, "这是初始内容。")
        await asyncio.sleep(1)  # 等待后台处理
        
        # 测试2: 小变化（不应触发保存）
        print("\n📝 测试2: 小变化（不应触发保存）")
        await storage_service.save_content(document_id, user_id, "这是初始内容。稍微修改")
        await asyncio.sleep(1)
        
        # 测试3: 大变化（应触发保存）
        print("\n📝 测试3: 大变化（应触发保存）")
        await storage_service.save_content(document_id, user_id, "这是初始内容。稍微修改。现在添加更多内容来测试大变化触发保存机制。")
        await asyncio.sleep(1)
        
        # 测试4: 句子完成（应触发保存）
        print("\n📝 测试4: 句子完成（应触发保存）")
        await storage_service.save_content(document_id, user_id, "这是初始内容。稍微修改。现在添加更多内容来测试大变化触发保存机制。这是一个完整的句子！")
        await asyncio.sleep(1)
        
        # 测试5: 时间间隔触发
        print("\n📝 测试5: 时间间隔触发（等待10秒）")
        await storage_service.save_content(document_id, user_id, "这是初始内容。稍微修改。现在添加更多内容来测试大变化触发保存机制。这是一个完整的句子！等待时间间隔触发。")
        print("⏰ 等待10秒...")
        await asyncio.sleep(10)
        
        # 再次保存相同内容（应该触发时间间隔保存）
        await storage_service.save_content(document_id, user_id, "这是初始内容。稍微修改。现在添加更多内容来测试大变化触发保存机制。这是一个完整的句子！等待时间间隔触发。")
        await asyncio.sleep(1)
        
        # 测试6: 中文句子完成
        print("\n📝 测试6: 中文句子完成（应触发保存）")
        await storage_service.save_content(document_id, user_id, "这是初始内容。稍微修改。现在添加更多内容来测试大变化触发保存机制。这是一个完整的句子！等待时间间隔触发。现在测试中文句子。")
        await asyncio.sleep(1)
        
        await storage_service.save_content(document_id, user_id, "这是初始内容。稍微修改。现在添加更多内容来测试大变化触发保存机制。这是一个完整的句子！等待时间间隔触发。现在测试中文句子。这是中文句子！")
        await asyncio.sleep(1)
        
        # 验证保存结果
        print("\n🔍 验证保存结果...")
        versions = await storage_service.get_document_versions(document_id)
        print(f"📊 版本数量: {len(versions)}")
        
        for i, version in enumerate(versions):
            print(f"  版本 {version.version_number}: {version.change_description}")
            print(f"    内容长度: {len(version.content)}")
            print(f"    修改时间: {version.created_at}")
        
        # 获取文档统计
        stats = await storage_service.get_document_statistics(document_id)
        print(f"\n📈 文档统计:")
        print(f"  当前版本: {stats.get('current_version', 'N/A')}")
        print(f"  版本数量: {stats.get('version_count', 'N/A')}")
        print(f"  内容长度: {stats.get('content_length', 'N/A')}")
        
        print("\n✅ 智能保存策略测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试文档（先删除相关记录）
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
    asyncio.run(test_smart_save_strategy()) 