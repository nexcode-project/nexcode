#!/usr/bin/env python3
"""
修复文档权限脚本
检查文档12的权限设置并给admin用户添加权限
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.database import User
from app.models.document_models import Document, DocumentCollaborator
from app.models.document_models import PermissionLevel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def check_document_permissions():
    """检查文档权限"""
    print("🔍 检查文档权限...")
    
    async for db in get_db():
        try:
            # 检查文档12是否存在
            stmt = select(Document).where(Document.id == 12)
            result = await db.execute(stmt)
            document = result.scalar_one_or_none()
            
            if not document:
                print("❌ 文档12不存在，创建新文档...")
                # 创建文档12
                demo_user = await db.execute(select(User).where(User.username == "demo"))
                demo_user = demo_user.scalar_one_or_none()
                
                if not demo_user:
                    print("❌ demo用户不存在")
                    return
                
                new_document = Document(
                    id=12,
                    title="测试协作文档",
                    content="这是一个用于测试协作编辑的文档",
                    owner_id=demo_user.id,
                    category="test",
                    status="active"
                )
                db.add(new_document)
                await db.commit()
                print("✅ 创建文档12成功")
                
                # 重新获取文档
                stmt = select(Document).where(Document.id == 12)
                result = await db.execute(stmt)
                document = result.scalar_one_or_none()
            
            print(f"📄 文档12信息:")
            print(f"  - 标题: {document.title}")
            print(f"  - 所有者ID: {document.owner_id}")
            print(f"  - 状态: {document.status}")
            
            # 检查所有者
            owner_stmt = select(User).where(User.id == document.owner_id)
            owner_result = await db.execute(owner_stmt)
            owner = owner_result.scalar_one_or_none()
            print(f"  - 所有者: {owner.username if owner else 'Unknown'}")
            
            # 检查协作者
            collaborator_stmt = select(DocumentCollaborator).where(DocumentCollaborator.document_id == 12)
            collaborator_result = await db.execute(collaborator_stmt)
            collaborators = collaborator_result.scalars().all()
            
            print(f"  - 协作者数量: {len(collaborators)}")
            for collab in collaborators:
                user_stmt = select(User).where(User.id == collab.user_id)
                user_result = await db.execute(user_stmt)
                user = user_result.scalar_one_or_none()
                print(f"    * {user.username if user else 'Unknown'} - {collab.permission}")
            
            # 检查admin用户
            admin_stmt = select(User).where(User.username == "admin")
            admin_result = await db.execute(admin_stmt)
            admin = admin_result.scalar_one_or_none()
            
            # 获取demo用户（文档所有者）
            demo_user = owner
            
            if admin:
                print(f"👤 admin用户信息:")
                print(f"  - ID: {admin.id}")
                print(f"  - 用户名: {admin.username}")
                print(f"  - 邮箱: {admin.email}")
                
                # 检查admin是否有权限
                has_permission = False
                if document.owner_id == admin.id:
                    has_permission = True
                    print("  - 权限: 所有者")
                else:
                    for collab in collaborators:
                        if collab.user_id == admin.id:
                            has_permission = True
                            print(f"  - 权限: {collab.permission}")
                            break
                
                if not has_permission:
                    print("  - 权限: 无权限")
                    print("🔄 正在给admin用户添加编辑权限...")
                    
                    # 添加admin为协作者
                    new_collaborator = DocumentCollaborator(
                        document_id=12,
                        user_id=admin.id,
                        permission=PermissionLevel.EDITOR,
                        added_by=demo_user.id  # 使用demo用户作为添加者
                    )
                    db.add(new_collaborator)
                    await db.commit()
                    print("✅ admin用户权限添加成功")
                else:
                    print("✅ admin用户已有权限")
            else:
                print("❌ admin用户不存在")
            
        except Exception as e:
            print(f"❌ 检查权限失败: {e}")
            await db.rollback()
        finally:
            break

async def main():
    """主函数"""
    print("🚀 开始修复文档权限")
    print("=" * 50)
    
    await check_document_permissions()
    
    print("🎉 权限修复完成")

if __name__ == "__main__":
    asyncio.run(main()) 