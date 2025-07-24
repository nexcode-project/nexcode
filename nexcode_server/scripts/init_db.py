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

from app.core.database import AsyncSessionLocal, init_db
from app.models.database import User, SystemSettings, Document
from app.services.auth_service import auth_service
from sqlalchemy import select


async def create_admin_user():
    """创建管理员用户"""
    try:
        async with AsyncSessionLocal() as db:
            # 检查是否已存在管理员用户
            stmt = select(User).where(User.username == "admin")
            result = await db.execute(stmt)
            existing_admin = result.scalar_one_or_none()

            if existing_admin:
                print("✅ 管理员用户已存在")
                return existing_admin  # 返回现有的管理员用户

            # 创建管理员用户 - 移除 full_name 参数
            admin_user = User(
                username="admin",
                email="admin@nexcode.com",
                password_hash=auth_service.get_password_hash("admin123"),
                is_active=True
            )

            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)

            print("✅ 管理员用户创建成功")
            print(f"   用户名: admin")
            print(f"   密码: admin123")
            print(f"   邮箱: admin@nexcode.com")

            return admin_user

    except Exception as e:
        await db.rollback()
        print(f"❌ 创建管理员用户失败: {e}")
        raise


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
                print("✅ 演示用户密码设置成功")
            else:
                print("✅ 演示用户已存在")
            print("   用户名: demo")
            print("   密码: demo123")
            return existing_demo

        # 创建演示用户
        password_hash = auth_service.get_password_hash("demo123")
        demo_user = User(
            username="demo",
            email="demo@nexcode.local",
            full_name="演示用户",
            password_hash=password_hash,
            is_superuser=False,
            is_active=True,
        )

        db.add(demo_user)
        await db.commit()
        await db.refresh(demo_user)

        print(f"✅ 演示用户创建成功")
        print(f"   ID: {demo_user.id}")
        print(f"   用户名: {demo_user.username}")
        print(f"   邮箱: {demo_user.email}")
        print("   密码: demo123")
        return demo_user


async def create_demo_documents(admin_user: User, demo_user: User):
    """创建演示文档"""
    async with AsyncSessionLocal() as db:
        # 检查是否已存在演示文档
        stmt = select(Document).where(Document.title.like("演示文档%"))
        result = await db.execute(stmt)
        existing_docs = result.scalars().all()

        if existing_docs:
            print(f"✅ 演示文档已存在 ({len(existing_docs)}个)")
            return existing_docs

        # 创建演示文档
        demo_documents = [
            {
                "title": "演示文档 - 项目介绍",
                "content": """# NexCode 协作文档平台

## 项目简介
NexCode 是一个现代化的协作文档平台，支持实时协作编辑、版本控制和AI助手功能。

## 主要功能
- 📝 富文本编辑器
- 👥 实时协作编辑
- 📚 版本控制和历史记录
- 🔐 细粒度权限管理
- 🤖 AI写作助手
- 🔍 全文搜索

## 技术栈
- 后端: FastAPI + PostgreSQL
- 前端: React + TypeScript
- 实时通信: WebSocket
- AI集成: OpenAI API

欢迎使用！""",
                "category": "介绍",
                "tags": ["演示", "介绍", "功能"],
                "owner_id": admin_user.id,
            },
            {
                "title": "演示文档 - 使用指南",
                "content": """# 使用指南

## 创建文档
1. 点击"新建文档"按钮
2. 输入文档标题
3. 选择分类和标签
4. 开始编写内容

## 协作编辑
1. 点击"分享"按钮
2. 输入协作者邮箱
3. 选择权限级别：
   - 查看者：只能查看文档
   - 编辑者：可以编辑文档
   - 所有者：拥有完全控制权

## 版本管理
- 系统自动保存版本
- 可以查看历史版本
- 支持版本回滚

## AI助手
- 使用 `/ai` 命令调用AI助手
- 支持内容生成、改写、总结等功能""",
                "category": "指南",
                "tags": ["指南", "教程", "帮助"],
                "owner_id": demo_user.id,
            },
            {
                "title": "演示文档 - 会议记录模板",
                "content": """# 会议记录

**会议主题：**
**时间：**
**地点：**
**参会人员：**

## 会议议程
1.
2.
3.

## 讨论内容

### 议题一
**讨论要点：**
-
-

**决议：**
-

### 议题二
**讨论要点：**
-
-

**决议：**
-

## 行动项
| 任务 | 负责人 | 截止时间 | 状态 |
|------|--------|----------|------|
|      |        |          |      |

## 下次会议
**时间：**
**议题：** """,
                "category": "模板",
                "tags": ["模板", "会议", "记录"],
                "owner_id": admin_user.id,
            },
        ]

        created_docs = []
        for doc_data in demo_documents:
            document = Document(
                title=doc_data["title"],
                content=doc_data["content"],
                category=doc_data["category"],
                tags=doc_data["tags"],
                owner_id=doc_data["owner_id"],
                last_editor_id=doc_data["owner_id"],
                version=1  # 新文档版本从 1 开始
            )

            db.add(document)
            created_docs.append(document)

        await db.commit()

        print(f"✅ 演示文档创建成功 ({len(created_docs)}个)")
        for doc in created_docs:
            print(f"   - {doc.title}")

        return created_docs


async def create_system_settings():
    """创建系统设置"""
    async with AsyncSessionLocal() as db:
        # 检查是否已存在系统设置
        stmt = select(SystemSettings)
        result = await db.execute(stmt)
        existing_settings = result.scalar_one_or_none()

        if existing_settings:
            print("✅ 系统设置已存在")
            return existing_settings

        # 创建默认系统设置
        settings = SystemSettings(
            site_name="NexCode 协作文档平台",
            site_description="现代化的协作文档平台，支持实时协作编辑、版本控制和AI助手功能",
            admin_email="admin@nexcode.local",
            max_file_size=10485760,  # 10MB
            session_timeout=1800,  # 30分钟
            enable_registration=True,
            enable_email_verification=False,
        )

        db.add(settings)
        await db.commit()
        await db.refresh(settings)

        print("✅ 系统设置创建成功")
        print(f"   站点名称: {settings.site_name}")
        print(f"   管理员邮箱: {settings.admin_email}")

        return settings


async def create_demo_api_key(user: User):
    """为用户创建演示API密钥"""
    try:
        async with AsyncSessionLocal() as db:
            api_key, token = await auth_service.create_api_key(
                db=db,
                user_id=user.id,
                key_name="演示API密钥",
                scopes=["read", "write"],
                rate_limit=1000,
            )

            print(f"✅ API密钥创建成功")
            print(f"   用户: {user.username}")
            print(f"   密钥名称: 演示API密钥")
            print(f"   Token: {token}")
            print("   ⚠️  请保存此API密钥，它只会显示一次！")
            return api_key
    except Exception as e:
        print(f"⚠️  API密钥创建失败: {e}")
        return None


async def main():
    """主函数"""
    print("=" * 60)
    print("🚀 开始初始化数据库...")
    print("=" * 60)

    try:
        # 初始化数据库表结构
        print("1. 初始化数据库表结构...")
        await init_db()
        print("✅ 数据库表结构初始化完成")
        print()

        # 创建管理员用户
        print("2. 创建管理员用户...")
        admin_user = await create_admin_user()
        print()

        # 创建演示用户
        print("3. 创建演示用户...")
        demo_user = await create_demo_user()
        print()

        # 创建系统设置
        print("4. 创建系统设置...")
        await create_system_settings()
        print()

        # 创建演示文档
        print("5. 创建演示文档...")
        await create_demo_documents(admin_user, demo_user)
        print()

        # 为演示用户创建API密钥
        print("6. 创建API密钥...")
        await create_demo_api_key(demo_user)
        print()

        print("=" * 60)
        print("🎉 数据库初始化完成！")
        print("=" * 60)
        print()
        print("📋 登录信息:")
        print("   管理员账户:")
        print("     用户名: admin")
        print("     密码: admin")
        print("     邮箱: admin@nexcode.local")
        print()
        print("   演示账户:")
        print("     用户名: demo")
        print("     密码: demo123")
        print("     邮箱: demo@nexcode.local")
        print()
        print("🔧 下一步:")
        print("   1. 启动后端服务: uvicorn app.main:app --reload")
        print("   2. 访问API文档: http://localhost:8000/docs")
        print("   3. 使用上述账户登录测试")
        print()

    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
