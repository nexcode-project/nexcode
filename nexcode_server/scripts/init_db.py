#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建初始管理员用户和基础数据
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.models.database import User
from app.services.auth_service import auth_service
from sqlalchemy import select

async def create_admin_user():
    """创建初始管理员用户"""
    async with AsyncSessionLocal() as db:
        # 检查是否已存在管理员用户
        stmt = select(User).where(User.username == "admin")
        result = await db.execute(stmt)
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            # 为现有管理员用户添加/更新密码
            existing_admin.password_hash = auth_service.get_password_hash("admin")
            await db.commit()
            print("为管理员用户设置密码成功")
            print("管理员登录信息: username=admin, password=admin")
            return existing_admin
        
        # 创建管理员用户
        password_hash = auth_service.get_password_hash("admin")
        admin_user = User(
            username="admin",
            email="admin@nexcode.local",
            full_name="System Administrator",
            password_hash=password_hash,
            is_superuser=True,
            is_active=True
        )
        
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
        
        print(f"管理员用户创建成功: {admin_user.username} (ID: {admin_user.id})")
        print("管理员登录信息: username=admin, password=admin123")
        return admin_user

async def create_demo_user():
    """创建演示用户"""
    async with AsyncSessionLocal() as db:
        # 检查是否已存在演示用户
        stmt = select(User).where(User.username == "demo")
        result = await db.execute(stmt)
        existing_demo = result.scalar_one_or_none()
        
        if existing_demo:
            # 为现有演示用户添加密码
            if not existing_demo.password_hash:
                existing_demo.password_hash = auth_service.get_password_hash("demo123")
                await db.commit()
                print("为演示用户添加密码成功")
                print("演示用户登录信息: username=demo, password=demo123")
            else:
                print("演示用户已存在")
            return existing_demo
        
        # 创建演示用户
        password_hash = auth_service.get_password_hash("demo123")
        demo_user = User(
            username="demo",
            email="demo@nexcode.local",
            full_name="Demo User",
            password_hash=password_hash,
            is_superuser=False,
            is_active=True
        )
        
        db.add(demo_user)
        await db.commit()
        await db.refresh(demo_user)
        
        print(f"演示用户创建成功: {demo_user.username} (ID: {demo_user.id})")
        print("演示用户登录信息: username=demo, password=demo123")
        return demo_user

async def create_demo_api_key(user: User):
    """为用户创建演示API密钥"""
    async with AsyncSessionLocal() as db:
        api_key, token = await auth_service.create_api_key(
            db=db,
            user_id=user.id,
            key_name="Demo API Key",
            scopes=["read", "write"],
            rate_limit=1000
        )
        
        print(f"为用户 {user.username} 创建API密钥成功")
        print(f"API Key: {token}")
        print("请保存此API密钥，它只会显示一次！")
        return api_key

async def main():
    """主函数"""
    print("开始初始化数据库...")
    
    try:
        # 创建管理员用户
        admin_user = await create_admin_user()
        
        # 创建演示用户
        demo_user = await create_demo_user()
        
        # 为演示用户创建API密钥
        await create_demo_api_key(demo_user)
        
        print("\n数据库初始化完成！")
        print("\n用户信息:")
        print(f"管理员: admin / admin@nexcode.local (超级用户)")
        print(f"演示用户: demo / demo@nexcode.local")
        print("\n您可以通过以下方式测试系统:")
        print("1. 使用CAS登录 (需要配置CAS服务器)")
        print("2. 使用API密钥调用接口")
        print("3. 通过管理员账户管理用户")
        
    except Exception as e:
        print(f"初始化失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 