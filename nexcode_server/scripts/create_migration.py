#!/usr/bin/env python3
"""
创建数据库迁移脚本
"""

import subprocess
import sys
from pathlib import Path


def check_migration_status():
    """检查迁移状态"""
    project_root = Path(__file__).parent.parent

    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "current"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def create_migration():
    """创建新的数据库迁移"""

    # 切换到项目根目录
    project_root = Path(__file__).parent.parent

    # 先检查迁移状态
    print("检查迁移状态...")
    success, stdout, stderr = check_migration_status()

    if not success:
        print("⚠️  迁移状态检查失败，可能需要重置迁移")
        print("错误信息:", stderr)

        # 询问是否重置
        response = input("是否重置迁移历史? (y/N): ").lower().strip()
        if response == "y":
            print("正在重置迁移...")
            reset_result = subprocess.run(
                [sys.executable, "scripts/reset_migrations.py"], cwd=project_root
            )

            if reset_result.returncode != 0:
                print("❌ 迁移重置失败")
                return False

            print("✅ 迁移重置成功，继续创建迁移...")
        else:
            print("❌ 取消操作")
            return False

    try:
        # 创建迁移
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alembic",
                "revision",
                "--autogenerate",
                "-m",
                "add_document_models",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ 数据库迁移创建成功")
            print(result.stdout)
        else:
            print("❌ 创建迁移失败")
            print("错误信息:", result.stderr)

            # 如果是版本冲突，提供解决方案
            if "Can't locate revision" in result.stderr:
                print("\n💡 解决方案:")
                print("1. 运行: python scripts/reset_migrations.py")
                print("2. 或者手动删除 alembic/versions/ 下的迁移文件")
                print("3. 然后重新运行此脚本")

            return False

    except Exception as e:
        print(f"❌ 创建迁移时出错: {e}")
        return False

    return True


def apply_migration():
    """应用数据库迁移"""

    project_root = Path(__file__).parent.parent

    try:
        # 应用迁移
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ 数据库迁移应用成功")
            print(result.stdout)
        else:
            print("❌ 应用迁移失败")
            print("错误信息:", result.stderr)
            return False

    except Exception as e:
        print(f"❌ 应用迁移时出错: {e}")
        return False

    return True


def main():
    """主函数"""
    print("开始创建和应用数据库迁移...")

    # 创建迁移
    if create_migration():
        print("-" * 50)
        print("应用数据库迁移...")

        # 应用迁移
        if apply_migration():
            print("-" * 50)
            print("✅ 数据库迁移完成！")
            print("\n下一步:")
            print("运行初始化脚本: python scripts/init_db.py")
        else:
            print("❌ 数据库迁移应用失败")
            sys.exit(1)
    else:
        print("❌ 数据库迁移创建失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
