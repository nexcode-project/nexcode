#!/usr/bin/env python3
"""
SQL查询工具
用于直接执行SQL命令查看数据库结构和数据
"""

import asyncio
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from sqlalchemy import text

console = Console()

# 预定义的SQL查询
PREDEFINED_QUERIES = {
    "1": {
        "name": "查看所有表",
        "sql": "SELECT table_name, table_type FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
    },
    "2": {
        "name": "查看表结构",
        "sql": "SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name = '{table_name}' AND table_schema = 'public' ORDER BY ordinal_position;"
    },
    "3": {
        "name": "查看表约束",
        "sql": """
        SELECT 
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
        LEFT JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
        WHERE tc.table_name = '{table_name}' AND tc.table_schema = 'public';
        """
    },
    "4": {
        "name": "查看表索引",
        "sql": "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = '{table_name}' AND schemaname = 'public';"
    },
    "5": {
        "name": "查看用户表数据",
        "sql": "SELECT id, username, email, full_name, is_active, is_superuser, created_at FROM users LIMIT 10;"
    },
    "6": {
        "name": "查看提交历史",
        "sql": "SELECT id, user_id, repository_name, branch_name, final_commit_message, status, created_at FROM commit_info ORDER BY created_at DESC LIMIT 10;"
    },
    "7": {
        "name": "查看表记录数",
        "sql": "SELECT 'users' as table_name, COUNT(*) as count FROM users UNION ALL SELECT 'commit_info', COUNT(*) FROM commit_info UNION ALL SELECT 'user_sessions', COUNT(*) FROM user_sessions UNION ALL SELECT 'api_keys', COUNT(*) FROM api_keys UNION ALL SELECT 'system_settings', COUNT(*) FROM system_settings;"
    },
    "8": {
        "name": "查看外键关系",
        "sql": """
        SELECT 
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public';
        """
    }
}

async def execute_sql(sql: str, params: dict = None):
    """执行SQL查询"""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(text(sql), params or {})
            
            # 如果是SELECT查询，显示结果
            if sql.strip().upper().startswith('SELECT'):
                rows = result.fetchall()
                if rows:
                    # 获取列名
                    columns = result.keys()
                    
                    # 创建表格
                    table = Table(title="查询结果")
                    for col in columns:
                        table.add_column(str(col), style="cyan", no_wrap=True)
                    
                    # 添加数据行
                    for row in rows:
                        table.add_row(*[str(cell) if cell is not None else "NULL" for cell in row])
                    
                    console.print(table)
                    console.print(f"📊 共返回 {len(rows)} 行数据")
                else:
                    console.print("📝 查询结果为空", style="yellow")
            
            # 如果是其他类型的查询
            else:
                await db.commit()
                console.print("✅ 查询执行成功", style="green")
                
        except Exception as e:
            console.print(f"❌ SQL执行错误: {e}", style="red")

async def show_table_structure(table_name: str):
    """显示表结构"""
    sql = f"""
    SELECT 
        column_name as "字段名",
        data_type as "数据类型",
        CASE 
            WHEN character_maximum_length IS NOT NULL 
            THEN data_type || '(' || character_maximum_length || ')'
            WHEN numeric_precision IS NOT NULL AND numeric_scale IS NOT NULL
            THEN data_type || '(' || numeric_precision || ',' || numeric_scale || ')'
            WHEN numeric_precision IS NOT NULL
            THEN data_type || '(' || numeric_precision || ')'
            ELSE data_type
        END as "完整类型",
        is_nullable as "可空",
        column_default as "默认值",
        ordinal_position as "位置"
    FROM information_schema.columns 
    WHERE table_name = '{table_name}' AND table_schema = 'public'
    ORDER BY ordinal_position;
    """
    
    await execute_sql(sql)

async def show_table_data(table_name: str, limit: int = 10):
    """显示表数据"""
    sql = f"SELECT * FROM {table_name} LIMIT {limit};"
    await execute_sql(sql)

async def show_table_info(table_name: str):
    """显示表的完整信息"""
    console.print(f"\n📋 表 '{table_name}' 的完整信息:", style="bold blue")
    
    # 1. 表结构
    console.print("\n🏗️ 表结构:")
    await show_table_structure(table_name)
    
    # 2. 表约束
    console.print("\n🔗 表约束:")
    constraint_sql = f"""
    SELECT 
        tc.constraint_name as "约束名",
        tc.constraint_type as "约束类型",
        kcu.column_name as "字段名",
        ccu.table_name as "引用表",
        ccu.column_name as "引用字段"
    FROM information_schema.table_constraints tc
    LEFT JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
    LEFT JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
    WHERE tc.table_name = '{table_name}' AND tc.table_schema = 'public';
    """
    await execute_sql(constraint_sql)
    
    # 3. 表索引
    console.print("\n📇 表索引:")
    index_sql = f"SELECT indexname as '索引名', indexdef as '索引定义' FROM pg_indexes WHERE tablename = '{table_name}' AND schemaname = 'public';"
    await execute_sql(index_sql)
    
    # 4. 表数据（前5行）
    console.print("\n📊 表数据（前5行）:")
    await show_table_data(table_name, 5)

async def main():
    """主函数"""
    console.print("🔍 NexCode SQL查询工具", style="bold blue")
    console.print("=" * 50)
    
    while True:
        console.print("\n请选择操作：")
        console.print("1. 查看所有表")
        console.print("2. 查看表结构")
        console.print("3. 查看表约束")
        console.print("4. 查看表索引")
        console.print("5. 查看用户数据")
        console.print("6. 查看提交历史")
        console.print("7. 查看表记录数")
        console.print("8. 查看外键关系")
        console.print("9. 查看完整表信息")
        console.print("10. 自定义SQL查询")
        console.print("0. 退出")
        
        choice = input("\n请输入选择 (0-10): ").strip()
        
        try:
            if choice == "0":
                console.print("👋 再见！")
                break
            elif choice in PREDEFINED_QUERIES:
                query_info = PREDEFINED_QUERIES[choice]
                
                if "{table_name}" in query_info["sql"]:
                    table_name = input(f"请输入表名: ").strip()
                    if not table_name:
                        console.print("❌ 请输入表名", style="red")
                        continue
                    sql = query_info["sql"].format(table_name=table_name)
                else:
                    sql = query_info["sql"]
                
                console.print(f"\n🔍 执行查询: {query_info['name']}")
                console.print(Syntax(sql, "sql", theme="monokai"))
                await execute_sql(sql)
                
            elif choice == "9":
                table_name = input("请输入表名: ").strip()
                if table_name:
                    await show_table_info(table_name)
                else:
                    console.print("❌ 请输入表名", style="red")
                    
            elif choice == "10":
                console.print("\n💡 输入您的SQL查询（输入 'exit' 退出）:")
                while True:
                    sql = input("SQL> ").strip()
                    if sql.lower() == 'exit':
                        break
                    if sql:
                        await execute_sql(sql)
                        
            else:
                console.print("❌ 无效选择，请重新输入", style="red")
                
        except Exception as e:
            console.print(f"❌ 错误: {e}", style="red")

if __name__ == "__main__":
    asyncio.run(main()) 