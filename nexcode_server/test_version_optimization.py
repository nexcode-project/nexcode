#!/usr/bin/env python3
"""
测试版本快照优化功能
验证只有内容变化时才创建版本快照
"""

import asyncio
import hashlib
from app.services.document_storage_service import document_storage_service

async def test_version_optimization():
    """测试版本快照优化"""
    print("🧪 开始测试版本快照优化...")
    
    # 模拟文档ID和用户ID
    document_id = 5
    user_id = 2
    
    # 测试1: 创建第一个版本快照
    print("\n📝 测试1: 创建初始版本快照")
    result1 = await document_storage_service.create_version_snapshot(
        document_id, user_id, "测试版本1"
    )
    print(f"结果: {result1}")
    
    # 测试2: 立即再次创建版本快照（内容未变化）
    print("\n📝 测试2: 创建重复版本快照（内容未变化）")
    result2 = await document_storage_service.create_version_snapshot(
        document_id, user_id, "测试版本2"
    )
    print(f"结果: {result2}")
    
    # 测试3: 使用不同内容创建版本快照
    print("\n📝 测试3: 使用不同内容创建版本快照")
    new_content = "这是新的内容，应该会创建新版本"
    result3 = await document_storage_service.create_version_snapshot_with_content(
        document_id, user_id, "测试版本3", new_content
    )
    print(f"结果: {result3}")
    
    # 测试4: 使用相同内容再次创建版本快照
    print("\n📝 测试4: 使用相同内容再次创建版本快照")
    result4 = await document_storage_service.create_version_snapshot_with_content(
        document_id, user_id, "测试版本4", new_content
    )
    print(f"结果: {result4}")
    
    print("\n✅ 测试完成！")

if __name__ == "__main__":
    asyncio.run(test_version_optimization()) 