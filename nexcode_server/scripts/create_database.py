#!/usr/bin/env python3
"""
数据库创建脚本
用于创建PostgreSQL数据库
"""

import asyncio
import sys
import os
from pathlib import Path
import asyncpg
from urllib.parse import urlparse

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import DATABASE_URL

async def create_database():
    """创建数据库"""
    
    # 解析数据库URL
    parsed_url = urlparse(DATABASE_URL.replace("+asyncpg", ""))
    
    # 提取连接信息
    host = parsed_url.hostname or 'localhost'
    port = parsed_url.port or 5433
    username = parsed_url.username or 'postgres'
    password = parsed_url.password or 'kangkang123'
    database_name = parsed_url.path.lstrip('/') or 'nexcode'
    
    print(f"连接信息:")
    print(f"  主机: {host}")
    print(f"  端口: {port}")
    print(f"  用户: {username}")
    print(f"  数据库: {database_name}")
    
    try:
        # 连接到默认的postgres数据库
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database='postgres'
        )
        
        print(f"成功连接到PostgreSQL服务器")
        
        # 检查数据库是否已存在
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            database_name
        )
        
        if result:
            print(f"数据库 '{database_name}' 已存在")
        else:
            # 创建数据库
            await conn.execute(f'CREATE DATABASE "{database_name}"')
            print(f"数据库 '{database_name}' 创建成功")
        
        await conn.close()
        return True
        
    except asyncpg.exceptions.InvalidAuthorizationSpecificationError:
        print(f"❌ 认证失败: 用户名或密码错误")
        print(f"请检查数据库连接配置:")
        print(f"  用户: {username}")
        print(f"  密码: {'*' * len(password) if password else '(未设置)'}")
        return False
        
    except asyncpg.exceptions.CannotConnectNowError:
        print(f"❌ 无法连接到数据库服务器")
        print(f"请确保PostgreSQL服务正在运行:")
        print(f"  主机: {host}")
        print(f"  端口: {port}")
        return False
        
    except Exception as e:
        print(f"❌ 创建数据库失败: {e}")
        return False

async def test_connection():
    """测试数据库连接"""
    
    parsed_url = urlparse(DATABASE_URL.replace("+asyncpg", ""))
    host = parsed_url.hostname or 'localhost'
    port = parsed_url.port or 5433
    username = parsed_url.username or 'postgres'
    password = parsed_url.password or 'kangkang123'
    database_name = parsed_url.path.lstrip('/') or 'nexcode'
    
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database_name
        )
        
        # 测试查询
        result = await conn.fetchval("SELECT version()")
        print(f"✅ 数据库连接测试成功")
        print(f"PostgreSQL版本: {result}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return False

async def main():
    """主函数"""
    print("开始创建数据库...")
    print(f"数据库URL: {DATABASE_URL}")
    print("-" * 50)
    
    # 创建数据库
    if await create_database():
        print("-" * 50)
        print("测试数据库连接...")
        
        # 测试连接
        if await test_connection():
            print("-" * 50)
            print("✅ 数据库创建完成！")
            print("\n下一步:")
            print("1. 运行数据库迁移: alembic upgrade head")
            print("2. 初始化数据: python scripts/init_db.py")
        else:
            print("❌ 数据库连接测试失败")
            sys.exit(1)
    else:
        print("❌ 数据库创建失败")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())