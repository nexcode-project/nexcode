#!/usr/bin/env python3
"""
直接测试协作管理器
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.collaboration_service import collaboration_manager

async def test_collaboration_manager():
    """直接测试协作管理器"""
    
    print("🧪 直接测试协作管理器")
    print("=" * 50)
    
    # 测试用户信息缓存
    print("1️⃣ 测试用户信息缓存...")
    collaboration_manager.update_user_cache(1, {
        "id": 1,
        "username": "user1",
        "email": "user1@test.com"
    })
    collaboration_manager.update_user_cache(2, {
        "id": 2,
        "username": "user2",
        "email": "user2@test.com"
    })
    
    print(f"✅ 用户缓存: {collaboration_manager.user_cache}")
    
    # 测试在线用户列表
    print("\n2️⃣ 测试在线用户列表...")
    
    # 模拟连接
    collaboration_manager.active_connections[12] = {1: None, 2: None}
    
    print(f"✅ 活跃连接: {collaboration_manager.active_connections}")
    
    # 测试在线用户列表生成
    online_users = []
    for uid in collaboration_manager.active_connections[12].keys():
        user_info = collaboration_manager.user_cache.get(uid, {"id": uid, "username": f"User{uid}"})
        online_users.append(user_info)
    
    print(f"✅ 在线用户列表: {online_users}")
    
    print("\n🎉 协作管理器测试完成!")

if __name__ == "__main__":
    asyncio.run(test_collaboration_manager()) 