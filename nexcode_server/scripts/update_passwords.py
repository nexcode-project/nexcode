#!/usr/bin/env python3
"""
修改用户密码脚本
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.database import User
from app.services.auth_service import auth_service
from sqlalchemy import select

async def update_user_password(username: str, new_password: str):
    """修改指定用户的密码"""
    print(f"🔄 正在修改用户 '{username}' 的密码...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 查找用户
            result = await db.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ 用户 '{username}' 不存在")
                return False
            
            # 更新密码
            user.password_hash = auth_service.get_password_hash(new_password)
            user.is_superuser = True
            await db.commit()
            
            print(f"✅ 用户 '{username}' 密码修改成功")
            print(f"   新密码: {new_password}")
            return True
            
        except Exception as e:
            print(f"❌ 修改密码失败: {e}")
            await db.rollback()
            return False

async def update_default_passwords():
    """更新默认用户的密码"""
    print("🔄 开始更新默认用户密码...")
    
    # 默认用户配置
    default_users = [
        ("demo", "demo123"),
        ("admin", "admin123"),
    ]
    
    success_count = 0
    total_count = len(default_users)
    
    for username, password in default_users:
        if await update_user_password(username, password):
            success_count += 1
    
    print(f"\n📊 更新结果: {success_count}/{total_count} 个用户密码更新成功")
    
    if success_count == total_count:
        print("\n🎉 所有默认用户密码更新完成!")
        print("=" * 50)
        print("📝 可用账号:")
        print("  - 演示账号: demo / demo123")
        print("  - 管理员账号: admin / admin123")
        print("  - 测试账号: test / test123")
        print("=" * 50)
    else:
        print(f"⚠️  有 {total_count - success_count} 个用户密码更新失败")

async def check_users():
    """检查现有用户"""
    print("🔍 检查现有用户...")
    
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(User))
            users = result.scalars().all()
            
            if not users:
                print("❌ 数据库中没有用户")
                return False
            
            print(f"✅ 找到 {len(users)} 个用户:")
            for user in users:
                print(f"  - {user.username} ({user.email}) - {'管理员' if user.is_superuser else '普通用户'}")
            
            return True
            
        except Exception as e:
            print(f"❌ 检查用户失败: {e}")
            return False

async def create_missing_users():
    """创建缺失的默认用户"""
    print("🔄 创建缺失的默认用户...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 检查并创建demo用户
            result = await db.execute(select(User).where(User.username == "demo"))
            demo_user = result.scalar_one_or_none()
            
            if not demo_user:
                demo_user = User(
                    username="demo",
                    email="demo@example.com",
                    password_hash=auth_service.get_password_hash("demo123"),
                    is_active=True,
                    is_superuser=False
                )
                db.add(demo_user)
                print("✅ 创建演示账号: demo / demo123")
            
            # 检查并创建admin用户
            result = await db.execute(select(User).where(User.username == "admin"))
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    password_hash=auth_service.get_password_hash("admin123"),
                    is_active=True,
                    is_superuser=True
                )
                db.add(admin_user)
                print("✅ 创建管理员账号: admin / admin123")
            
            # 检查并创建test用户
            result = await db.execute(select(User).where(User.username == "test"))
            test_user = result.scalar_one_or_none()
            
            if not test_user:
                test_user = User(
                    username="test",
                    email="test@example.com",
                    password_hash=auth_service.get_password_hash("test123"),
                    is_active=True,
                    is_superuser=False
                )
                db.add(test_user)
                print("✅ 创建测试账号: test / test123")
            
            await db.commit()
            print("✅ 所有默认用户创建完成")
            
        except Exception as e:
            print(f"❌ 创建用户失败: {e}")
            await db.rollback()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="修改用户密码")
    parser.add_argument("--check", action="store_true", help="检查现有用户")
    parser.add_argument("--update", action="store_true", help="更新默认用户密码")
    parser.add_argument("--create", action="store_true", help="创建缺失的默认用户")
    parser.add_argument("--user", help="指定用户名")
    parser.add_argument("--password", help="指定新密码")
    
    args = parser.parse_args()
    
    async def main():
        if args.check:
            await check_users()
        elif args.update:
            await update_default_passwords()
        elif args.create:
            await create_missing_users()
        elif args.user and args.password:
            await update_user_password(args.user, args.password)
        else:
            # 默认先检查，然后更新密码
            if await check_users():
                print("\n是否要更新默认用户密码? (Y/n): ", end="")
                response = input().strip().lower()
                if response not in ['n', 'no', '否']:
                    await update_default_passwords()
                else:
                    print("取消密码更新操作")
            else:
                print("\n数据库中没有用户，是否要创建默认用户? (Y/n): ", end="")
                response = input().strip().lower()
                if response not in ['n', 'no', '否']:
                    await create_missing_users()
                    await update_default_passwords()
                else:
                    print("取消创建用户操作")
    
    asyncio.run(main()) 