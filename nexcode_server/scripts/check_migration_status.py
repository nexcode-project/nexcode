#!/usr/bin/env python3
"""
检查数据库迁移状态
"""

import subprocess
import sys
from pathlib import Path


def check_migration_status():
    """检查迁移状态"""
    project_root = Path(__file__).parent.parent

    print("检查数据库迁移状态...")
    print("-" * 50)

    try:
        # 检查当前版本
        print("1. 检查当前数据库版本:")
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "current"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ 当前版本:")
            print(result.stdout if result.stdout.strip() else "  (无版本信息)")
        else:
            print("❌ 获取当前版本失败:")
            print(result.stderr)

        print("-" * 30)

        # 检查迁移历史
        print("2. 检查迁移历史:")
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "history"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ 迁移历史:")
            print(result.stdout if result.stdout.strip() else "  (无历史记录)")
        else:
            print("❌ 获取迁移历史失败:")
            print(result.stderr)

        print("-" * 30)

        # 检查迁移文件
        print("3. 检查迁移文件:")
        versions_dir = project_root / "alembic" / "versions"
        if versions_dir.exists():
            migration_files = list(versions_dir.glob("*.py"))
            migration_files = [f for f in migration_files if f.name != "__init__.py"]

            if migration_files:
                print(f"✅ 发现 {len(migration_files)} 个迁移文件:")
                for file in sorted(migration_files):
                    print(f"  - {file.name}")
            else:
                print("⚠️  未发现迁移文件")
        else:
            print("❌ versions目录不存在")

        print("-" * 30)

        # 检查数据库连接
        print("4. 检查数据库连接:")
        try:
            # 尝试连接数据库
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import sys; sys.path.append('.'); from app.core.database import engine; print('数据库连接正常')",
                ],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                print("✅ 数据库连接正常")
            else:
                print("❌ 数据库连接失败:")
                print(result.stderr)
        except subprocess.TimeoutExpired:
            print("❌ 数据库连接超时")
        except Exception as e:
            print(f"❌ 检查数据库连接时出错: {e}")

    except Exception as e:
        print(f"检查失败: {e}")


if __name__ == "__main__":
    check_migration_status()
