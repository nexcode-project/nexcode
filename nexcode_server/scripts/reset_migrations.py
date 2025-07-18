#!/usr/bin/env python3
"""
重置数据库迁移
"""

import subprocess
import sys
import shutil
import asyncio
from pathlib import Path


def reset_migrations():
    """重置迁移历史"""
    project_root = Path(__file__).parent.parent
    versions_dir = project_root / "alembic" / "versions"

    print("重置数据库迁移...")
    print("-" * 50)

    try:
        # 1. 删除现有迁移文件
        if versions_dir.exists():
            print("删除现有迁移文件...")
            for file in versions_dir.glob("*.py"):
                if file.name != "__init__.py":
                    file.unlink()
                    print(f"  删除: {file.name}")

        # 2. 清理数据库中的alembic_version表
        print("清理数据库版本信息...")
        clean_result = subprocess.run(
            [sys.executable, "scripts/clean_alembic_version.py"], cwd=project_root
        )

        if clean_result.returncode != 0:
            print("⚠️  数据库清理失败，继续尝试...")

        # 3. 创建初始迁移
        print("创建初始迁移...")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alembic",
                "revision",
                "--autogenerate",
                "-m",
                "initial_migration",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ 初始迁移创建成功")
            print(result.stdout)
        else:
            print("❌ 初始迁移创建失败")
            print(result.stderr)
            return False

        # 4. 应用迁移
        print("应用迁移...")
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ 迁移应用成功")
            print(result.stdout)
        else:
            print("❌ 迁移应用失败")
            print(result.stderr)
            return False

        return True

    except Exception as e:
        print(f"重置失败: {e}")
        return False


if __name__ == "__main__":
    if reset_migrations():
        print("-" * 50)
        print("✅ 迁移重置完成！")
    else:
        print("❌ 迁移重置失败")
        sys.exit(1)
