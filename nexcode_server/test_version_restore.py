#!/usr/bin/env python3
"""
测试版本恢复功能
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.database import Document, DocumentVersion
from app.services.sharedb_service import get_sharedb_service
from sqlalchemy import select

async def test_version_restore():
    """测试版本恢复功能"""
    print("🔍 测试版本恢复功能...")
    
    document_id = 10
    target_version = 6  # 修改为版本6
    
    try:
        # 1. 检查文档和版本是否存在
        async for db in get_db():
            # 检查文档
            doc_stmt = select(Document).where(Document.id == document_id)
            doc_result = await db.execute(doc_stmt)
            document = doc_result.scalar_one_or_none()
            
            if not document:
                print(f"❌ 文档 {document_id} 不存在")
                return
            
            print(f"✅ 文档 {document_id} 存在: {document.title}")
            print(f"   当前版本: {document.version}")
            print(f"   当前内容长度: {len(document.content or '')}")
            
            # 检查目标版本
            version_stmt = select(DocumentVersion).where(
                DocumentVersion.document_id == document_id,
                DocumentVersion.version_number == target_version
            )
            version_result = await db.execute(version_stmt)
            target_version_obj = version_result.scalar_one_or_none()
            
            if not target_version_obj:
                print(f"❌ 版本 {target_version} 不存在")
                return
            
            print(f"✅ 目标版本 {target_version} 存在")
            print(f"   版本内容长度: {len(target_version_obj.content or '')}")
            print(f"   版本标题: {target_version_obj.title}")
            
            # 2. 测试 ShareDB 版本恢复
            sharedb_service = get_sharedb_service()
            
            # 获取恢复前的 ShareDB 状态
            before_doc = await sharedb_service.get_document(str(document_id))
            print(f"📊 恢复前 ShareDB 状态:")
            print(f"   版本: {before_doc['version']}")
            print(f"   内容长度: {len(before_doc['content'])}")
            
            # 执行版本恢复
            print(f"🔄 正在恢复版本 {target_version}...")
            restore_result = await sharedb_service.restore_version(
                doc_id=str(document_id),
                target_version_number=target_version,
                user_id=2,  # 假设用户ID为2
                db_session=db
            )
            
            if restore_result["success"]:
                print(f"✅ 版本恢复成功!")
                print(f"   新版本: {restore_result['version']}")
                print(f"   恢复自版本: {restore_result['restored_from_version']}")
                print(f"   内容长度: {len(restore_result['content'])}")
                
                # 验证 ShareDB 状态
                after_doc = await sharedb_service.get_document(str(document_id))
                print(f"📊 恢复后 ShareDB 状态:")
                print(f"   版本: {after_doc['version']}")
                print(f"   内容长度: {len(after_doc['content'])}")
                
                # 检查内容是否匹配
                if after_doc['content'] == restore_result['content']:
                    print("✅ ShareDB 内容已正确更新")
                else:
                    print("❌ ShareDB 内容更新失败")
                    
            else:
                print(f"❌ 版本恢复失败: {restore_result['error']}")
                
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_version_restore()) 