#!/usr/bin/env python3
"""
测试文档存储服务功能
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.database import User, Document
from app.services.document_storage_service import document_storage_service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def test_document_storage_service():
    """测试文档存储服务功能"""
    print("🧪 测试文档存储服务功能...")
    
    async for db in get_db():
        try:
            # 获取测试用户
            stmt = select(User).where(User.username == "demo")
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ 测试用户不存在，创建demo用户...")
                user = User(
                    username="demo",
                    email="demo@example.com",
                    full_name="Demo User"
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                print(f"✅ 创建用户: {user.username} (ID: {user.id})")
            
            # 创建测试文档
            print(f"\n📝 创建测试文档...")
            document = Document(
                title="测试文档存储服务",
                content="这是初始文档内容",
                owner_id=user.id,
                category="test",
                version=1
            )
            db.add(document)
            await db.commit()
            await db.refresh(document)
            print(f"✅ 创建文档: {document.title} (ID: {document.id})")
            
            # 测试异步内容保存
            print(f"\n💾 测试异步内容保存...")
            test_content = "这是通过存储服务更新的内容"
            await document_storage_service.save_content(document.id, user.id, test_content)
            
            # 等待后台保存完成
            await asyncio.sleep(1)
            
            # 验证内容是否保存
            stmt = select(Document).where(Document.id == document.id)
            result = await db.execute(stmt)
            updated_document = result.scalar_one_or_none()
            
            if updated_document and updated_document.content == test_content:
                print(f"✅ 异步内容保存成功: version={updated_document.version}, last_editor_id={updated_document.last_editor_id}")
            else:
                print(f"❌ 异步内容保存失败")
                print(f"   期望内容: {test_content}")
                print(f"   实际内容: {updated_document.content if updated_document else 'None'}")
            
            # 测试操作记录保存
            print(f"\n🔧 测试操作记录保存...")
            test_operation = {
                "id": "test_op_service_1",
                "type": "insert",
                "position": 5,
                "content": "插入的文本",
                "sequence": 1
            }
            await document_storage_service.save_content(document.id, user.id, "", test_operation)
            
            # 等待后台保存完成
            await asyncio.sleep(1)
            
            # 检查操作记录
            operations = await document_storage_service.get_document_operations(document.id)
            print(f"🔧 操作记录数量: {len(operations)}")
            for operation in operations:
                print(f"   - 操作 {operation.operation_id}: {operation.operation_type} at {operation.start_position}")
            
            # 测试版本管理
            print(f"\n📚 测试版本管理...")
            versions = await document_storage_service.get_document_versions(document.id)
            print(f"📚 版本记录数量: {len(versions)}")
            for version in versions:
                print(f"   - 版本 {version.version_number}: {version.change_description}")
            
            # 测试创建版本快照
            print(f"\n📸 测试创建版本快照...")
            await document_storage_service.create_version_snapshot(document.id, user.id, "手动创建的重要版本")
            
            # 等待后台保存完成
            await asyncio.sleep(1)
            
            # 检查版本快照
            versions = await document_storage_service.get_document_versions(document.id)
            print(f"📚 创建快照后版本数量: {len(versions)}")
            for version in versions:
                print(f"   - 版本 {version.version_number}: {version.change_description}")
            
            # 测试文档统计信息
            print(f"\n📊 测试文档统计信息...")
            stats = await document_storage_service.get_document_statistics(document.id)
            print(f"📊 文档统计信息:")
            for key, value in stats.items():
                print(f"   - {key}: {value}")
            
            # 测试多次内容更新
            print(f"\n🔄 测试多次内容更新...")
            for i in range(3):
                new_content = f"这是第{i+1}次通过存储服务更新的内容"
                await document_storage_service.save_content(document.id, user.id, new_content)
                print(f"   ✅ 第{i+1}次更新请求已发送")
            
            # 等待所有后台保存完成
            await asyncio.sleep(2)
            
            # 最终验证
            stmt = select(Document).where(Document.id == document.id)
            result = await db.execute(stmt)
            final_document = result.scalar_one_or_none()
            
            if final_document:
                print(f"\n📊 最终文档状态:")
                print(f"   - 标题: {final_document.title}")
                print(f"   - 版本: {final_document.version}")
                print(f"   - 最后编辑者: {final_document.last_editor_id}")
                print(f"   - 内容长度: {len(final_document.content)}")
            
            # 检查所有版本
            versions = await document_storage_service.get_document_versions(document.id)
            print(f"\n📚 所有版本记录:")
            for version in versions:
                print(f"   - 版本 {version.version_number}: {version.change_description} (长度: {len(version.content)})")
            
            print(f"\n✅ 文档存储服务功能测试完成！")
            break
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            break

if __name__ == "__main__":
    asyncio.run(test_document_storage_service()) 