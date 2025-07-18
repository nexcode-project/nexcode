#!/usr/bin/env python3
"""
清理Alembic版本表
"""

import asyncio
import sys
from pathlib import Path
import asyncpg
from urllib.parse import urlparse

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import DATABASE_URL

async def clean_alembic_version():
    """清理alembic_version表"""
    
    # 解析数据库URL
    parsed_url = urlparse(DATABASE_URL.replace("+asyncpg", ""))
    
    # 提取连接信息
    host = parsed_url.hostname or 'localhost'
    port = parsed_url.port or 5432
    username = parsed_url.username or 'postgres'
    password = parsed_url.password or 'kangkang123'
    database_name = parsed_url.path.lstrip('/') or 'nexcode'
    
    print(f"连接到数据库: {database_name}")
    
    try:
        # 连接到数据库
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database_name
        )
        
        print("成功连接到数据库")
        
        # 检查alembic_version表是否存在
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'alembic_version'
            );
        """)
        
        if table_exists:
            print("发现alembic_version表，正在清理...")
            
            # 查看当前版本
            current_version = await conn.fetchval("SELECT version_num FROM alembic_version")
            print(f"当前版本: {current_version}")
            
            # 删除alembic_version表
            await conn.execute("DROP TABLE IF EXISTS alembic_version")
            print("✅ alembic_version表已删除")
        else:
            print("alembic_version表不存在，无需清理")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        return False

async def main():
    """主函数"""
    print("开始清理Alembic版本信息...")
    print("-" * 50)
    
    if await clean_alembic_version():
        print("-" * 50)
        print("✅ 清理完成！")
        print("\n下一步:")
        print("1. 运行: python scripts/create_migration.py")
        print("2. 或者手动执行:")
        print("   alembic revision --autogenerate -m 'initial_migration'")
        print("   alembic upgrade head")
    else:
        print("❌ 清理失败")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())