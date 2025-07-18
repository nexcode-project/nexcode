#!/usr/bin/env python3
"""
数据库表结构查看脚本
用于快速查看数据库表的结构信息
"""

import asyncio
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import create_async_engine

console = Console()

async def get_database_url():
    """获取数据库URL"""
    from app.core.database import DATABASE_URL
    return DATABASE_URL

async def view_all_tables():
    """查看所有表的基本信息"""
    async with AsyncSessionLocal() as db:
        # 获取所有表名
        stmt = text("""
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        result = await db.execute(stmt)
        tables = result.fetchall()
        
        table = Table(title="数据库表列表")
        table.add_column("表名", style="cyan", no_wrap=True)
        table.add_column("类型", style="green")
        table.add_column("描述", style="yellow")
        
        table_descriptions = {
            "users": "用户信息表",
            "commit_info": "提交信息表",
            "user_sessions": "用户会话表",
            "api_keys": "API密钥表",
            "system_settings": "系统设置表",
            "alembic_version": "数据库迁移版本表"
        }
        
        for table_info in tables:
            table_name = table_info[0]
            table_type = table_info[1]
            description = table_descriptions.get(table_name, "系统表")
            
            table.add_row(table_name, table_type, description)
        
        console.print(table)

async def view_table_structure(table_name: str):
    """查看指定表的详细结构"""
    async with AsyncSessionLocal() as db:
        # 获取表结构信息
        stmt = text("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns 
            WHERE table_name = :table_name AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        result = await db.execute(stmt, {"table_name": table_name})
        columns = result.fetchall()
        
        if not columns:
            console.print(f"❌ 表 '{table_name}' 不存在", style="red")
            return
        
        # 创建表结构表格
        table = Table(title=f"表结构: {table_name}")
        table.add_column("字段名", style="cyan", no_wrap=True)
        table.add_column("数据类型", style="green")
        table.add_column("可空", style="yellow")
        table.add_column("默认值", style="blue")
        table.add_column("长度/精度", style="magenta")
        table.add_column("描述", style="white")
        
        # 字段描述映射
        field_descriptions = {
            "users": {
                "id": "主键ID",
                "username": "用户名",
                "email": "邮箱地址",
                "full_name": "全名",
                "password_hash": "密码哈希",
                "cas_user_id": "CAS用户ID",
                "cas_attributes": "CAS属性",
                "is_active": "是否激活",
                "is_superuser": "是否超级用户",
                "created_at": "创建时间",
                "updated_at": "更新时间",
                "last_login": "最后登录时间"
            },
            "commit_info": {
                "id": "主键ID",
                "user_id": "用户ID",
                "repository_url": "仓库URL",
                "repository_name": "仓库名称",
                "branch_name": "分支名称",
                "commit_hash": "提交哈希",
                "user_selected_message": "用户选择的提交消息",
                "ai_generated_message": "AI生成的提交消息",
                "final_commit_message": "最终提交消息",
                "diff_content": "差异内容",
                "files_changed": "变更文件",
                "lines_added": "新增行数",
                "lines_deleted": "删除行数",
                "ai_model_used": "使用的AI模型",
                "ai_parameters": "AI参数",
                "generation_time_ms": "生成时间(毫秒)",
                "user_rating": "用户评分",
                "user_feedback": "用户反馈",
                "commit_style": "提交风格",
                "status": "状态",
                "tags": "标签",
                "created_at": "创建时间",
                "updated_at": "更新时间",
                "committed_at": "提交时间"
            },
            "user_sessions": {
                "id": "主键ID",
                "user_id": "用户ID",
                "session_token": "会话令牌",
                "cas_ticket": "CAS票据",
                "ip_address": "IP地址",
                "user_agent": "用户代理",
                "created_at": "创建时间",
                "expires_at": "过期时间",
                "last_activity": "最后活动时间",
                "is_active": "是否活跃"
            },
            "api_keys": {
                "id": "主键ID",
                "user_id": "用户ID",
                "key_name": "密钥名称",
                "key_hash": "密钥哈希",
                "key_prefix": "密钥前缀",
                "scopes": "权限范围",
                "rate_limit": "速率限制",
                "usage_count": "使用次数",
                "last_used": "最后使用时间",
                "is_active": "是否激活",
                "created_at": "创建时间",
                "expires_at": "过期时间"
            },
            "system_settings": {
                "id": "主键ID",
                "site_name": "站点名称",
                "site_description": "站点描述",
                "admin_email": "管理员邮箱",
                "max_file_size": "最大文件大小",
                "session_timeout": "会话超时时间",
                "enable_registration": "启用注册",
                "enable_email_verification": "启用邮件验证",
                "smtp_host": "SMTP主机",
                "smtp_port": "SMTP端口",
                "smtp_username": "SMTP用户名",
                "smtp_password": "SMTP密码",
                "smtp_use_tls": "使用TLS",
                "created_at": "创建时间",
                "updated_at": "更新时间"
            }
        }
        
        descriptions = field_descriptions.get(table_name, {})
        
        for column in columns:
            column_name = column[0]
            data_type = column[1]
            is_nullable = "YES" if column[2] == "YES" else "NO"
            default_value = str(column[3]) if column[3] else "NULL"
            max_length = column[4] or column[5] or column[6] or ""
            description = descriptions.get(column_name, "")
            
            # 格式化数据类型显示
            if column[4]:  # 字符串类型
                data_type_display = f"{data_type}({column[4]})"
            elif column[5]:  # 数值类型
                if column[6]:
                    data_type_display = f"{data_type}({column[5]},{column[6]})"
                else:
                    data_type_display = f"{data_type}({column[5]})"
            else:
                data_type_display = data_type
            
            table.add_row(
                column_name,
                data_type_display,
                is_nullable,
                default_value,
                str(max_length),
                description
            )
        
        console.print(table)

async def view_table_constraints(table_name: str):
    """查看表的约束信息"""
    async with AsyncSessionLocal() as db:
        # 获取主键信息
        pk_stmt = text("""
            SELECT column_name
            FROM information_schema.key_column_usage
            WHERE table_name = :table_name 
            AND constraint_name LIKE '%_pkey'
            AND table_schema = 'public'
        """)
        pk_result = await db.execute(pk_stmt, {"table_name": table_name})
        primary_keys = [row[0] for row in pk_result.fetchall()]
        
        # 获取外键信息
        fk_stmt = text("""
            SELECT 
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                tc.constraint_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_name = :table_name
            AND tc.table_schema = 'public'
        """)
        fk_result = await db.execute(fk_stmt, {"table_name": table_name})
        foreign_keys = fk_result.fetchall()
        
        # 获取唯一约束
        unique_stmt = text("""
            SELECT column_name, constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = :table_name 
            AND constraint_name LIKE '%_key'
            AND constraint_name NOT LIKE '%_pkey'
            AND table_schema = 'public'
        """)
        unique_result = await db.execute(unique_stmt, {"table_name": table_name})
        unique_constraints = unique_result.fetchall()
        
        # 显示约束信息
        if primary_keys or foreign_keys or unique_constraints:
            table = Table(title=f"表约束: {table_name}")
            table.add_column("约束类型", style="cyan")
            table.add_column("字段", style="green")
            table.add_column("详细信息", style="yellow")
            
            # 主键
            if primary_keys:
                table.add_row("主键", ", ".join(primary_keys), "")
            
            # 外键
            for fk in foreign_keys:
                table.add_row(
                    "外键",
                    fk[0],
                    f"引用 {fk[1]}.{fk[2]}"
                )
            
            # 唯一约束
            for unique in unique_constraints:
                table.add_row("唯一约束", unique[0], unique[1])
            
            console.print(table)
        else:
            console.print(f"📝 表 '{table_name}' 没有特殊约束", style="yellow")

async def view_table_indexes(table_name: str):
    """查看表的索引信息"""
    async with AsyncSessionLocal() as db:
        stmt = text("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = :table_name
            AND schemaname = 'public'
            ORDER BY indexname
        """)
        result = await db.execute(stmt, {"table_name": table_name})
        indexes = result.fetchall()
        
        if indexes:
            table = Table(title=f"表索引: {table_name}")
            table.add_column("索引名", style="cyan")
            table.add_column("索引定义", style="green")
            
            for index in indexes:
                table.add_row(index[0], index[1])
            
            console.print(table)
        else:
            console.print(f"📝 表 '{table_name}' 没有自定义索引", style="yellow")

async def view_table_relationships():
    """查看表之间的关系"""
    async with AsyncSessionLocal() as db:
        stmt = text("""
            SELECT 
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_schema = 'public'
            ORDER BY tc.table_name, kcu.column_name
        """)
        result = await db.execute(stmt)
        relationships = result.fetchall()
        
        if relationships:
            table = Table(title="表关系图")
            table.add_column("表名", style="cyan")
            table.add_column("外键字段", style="green")
            table.add_column("引用表", style="yellow")
            table.add_column("引用字段", style="blue")
            
            for rel in relationships:
                table.add_row(rel[0], rel[1], rel[2], rel[3])
            
            console.print(table)
        else:
            console.print("📝 没有找到表关系", style="yellow")

async def view_database_info():
    """查看数据库基本信息"""
    async with AsyncSessionLocal() as db:
        # 获取数据库名称
        db_stmt = text("SELECT current_database()")
        db_result = await db.execute(db_stmt)
        db_name = db_result.scalar()
        
        # 获取表数量
        table_stmt = text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_result = await db.execute(table_stmt)
        table_count = table_result.scalar()
        
        # 获取数据库大小
        size_stmt = text("""
            SELECT pg_size_pretty(pg_database_size(current_database()))
        """)
        size_result = await db.execute(size_stmt)
        db_size = size_result.scalar()
        
        info_panel = Panel(
            f"数据库名称: {db_name}\n"
            f"表数量: {table_count}\n"
            f"数据库大小: {db_size}",
            title="数据库信息",
            border_style="blue"
        )
        console.print(info_panel)

async def main():
    """主函数"""
    console.print("🏗️ NexCode 数据库结构查看工具", style="bold blue")
    console.print("=" * 50)
    
    while True:
        console.print("\n请选择要查看的内容：")
        console.print("1. 查看所有表")
        console.print("2. 查看表结构")
        console.print("3. 查看表约束")
        console.print("4. 查看表索引")
        console.print("5. 查看表关系")
        console.print("6. 查看数据库信息")
        console.print("7. 查看完整表信息")
        console.print("0. 退出")
        
        choice = input("\n请输入选择 (0-7): ").strip()
        
        try:
            if choice == "0":
                console.print("👋 再见！")
                break
            elif choice == "1":
                await view_all_tables()
            elif choice == "2":
                table_name = input("请输入表名: ").strip()
                if table_name:
                    await view_table_structure(table_name)
                else:
                    console.print("❌ 请输入表名", style="red")
            elif choice == "3":
                table_name = input("请输入表名: ").strip()
                if table_name:
                    await view_table_constraints(table_name)
                else:
                    console.print("❌ 请输入表名", style="red")
            elif choice == "4":
                table_name = input("请输入表名: ").strip()
                if table_name:
                    await view_table_indexes(table_name)
                else:
                    console.print("❌ 请输入表名", style="red")
            elif choice == "5":
                await view_table_relationships()
            elif choice == "6":
                await view_database_info()
            elif choice == "7":
                table_name = input("请输入表名: ").strip()
                if table_name:
                    console.print(f"\n📋 表 '{table_name}' 的完整信息:")
                    await view_table_structure(table_name)
                    console.print()
                    await view_table_constraints(table_name)
                    console.print()
                    await view_table_indexes(table_name)
                else:
                    console.print("❌ 请输入表名", style="red")
            else:
                console.print("❌ 无效选择，请重新输入", style="red")
        except Exception as e:
            console.print(f"❌ 错误: {e}", style="red")

if __name__ == "__main__":
    asyncio.run(main()) 