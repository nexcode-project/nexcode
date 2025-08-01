#!/usr/bin/env python3
"""
测试版本预览功能
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.database import Document, DocumentVersion
from app.services.document_storage_service import DocumentStorageService
from sqlalchemy import select

async def test_version_preview():
    """测试版本预览功能"""
    print("🔍 测试版本预览功能...")
    
    document_id = 10
    target_version = 6
    
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
            print(f"   版本描述: {target_version_obj.change_description}")
            
            # 2. 测试版本预览功能
            document_storage_service = DocumentStorageService()
            
            print(f"🔄 正在获取版本 {target_version} 的内容...")
            content = await document_storage_service.get_version_content(document_id, target_version)
            
            if content is not None:
                print(f"✅ 版本预览成功!")
                print(f"   内容长度: {len(content)} 字符")
                print(f"   内容预览: {content[:200]}...")
                
                # 验证内容是否匹配
                if content == target_version_obj.content:
                    print("✅ 预览内容与版本内容匹配")
                else:
                    print("❌ 预览内容与版本内容不匹配")
                    
            else:
                print(f"❌ 版本预览失败")
                
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_version_preview()) 