#!/usr/bin/env python3
"""
比较commit_message.toml和push_strategy.toml的解析差异
"""

import toml
from pathlib import Path

def compare_toml_files():
    """比较两个TOML文件的解析结果"""
    prompts_dir = Path(__file__).parent.parent / "prompts"
    
    # 测试commit_message.toml
    commit_path = prompts_dir / "commit_message.toml"
    push_path = prompts_dir / "push_strategy.toml"
    
    print("🔍 比较TOML文件解析")
    print("=" * 60)
    
    # 测试commit_message.toml
    print("📄 commit_message.toml:")
    print("-" * 30)
    if commit_path.exists():
        try:
            config = toml.load(commit_path)
            if 'commit_message' in config:
                cm_config = config['commit_message']
                print(f"  - system: {'存在' if 'system' in cm_config else '不存在'}")
                print(f"  - content: {'存在' if 'content' in cm_config else '不存在'}")
                print(f"  - 所有字段: {list(cm_config.keys())}")
                if 'system' in cm_config:
                    print(f"  - system长度: {len(cm_config['system'])}")
                if 'content' in cm_config:
                    print(f"  - content长度: {len(cm_config['content'])}")
            else:
                print("  ❌ 没有找到commit_message字段")
        except Exception as e:
            print(f"  ❌ 解析失败: {e}")
    else:
        print("  ❌ 文件不存在")
    
    print()
    
    # 测试push_strategy.toml
    print("📄 push_strategy.toml:")
    print("-" * 30)
    if push_path.exists():
        try:
            config = toml.load(push_path)
            if 'push_strategy' in config:
                ps_config = config['push_strategy']
                print(f"  - system: {'存在' if 'system' in ps_config else '不存在'}")
                print(f"  - content: {'存在' if 'content' in ps_config else '不存在'}")
                print(f"  - 所有字段: {list(ps_config.keys())}")
                if 'system' in ps_config:
                    print(f"  - system长度: {len(ps_config['system'])}")
                if 'content' in ps_config:
                    print(f"  - content长度: {len(ps_config['content'])}")
            else:
                print("  ❌ 没有找到push_strategy字段")
        except Exception as e:
            print(f"  ❌ 解析失败: {e}")
    else:
        print("  ❌ 文件不存在")
    
    print()
    
    # 检查文件内容格式
    print("📋 文件格式分析:")
    print("-" * 30)
    
    if commit_path.exists():
        with open(commit_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print("commit_message.toml 格式:")
            print(f"  - 使用三引号: {'是' if '"""' in content else '否'}")
            print(f"  - 使用单引号: {'是' if "'''" in content else '否'}")
            print(f"  - 使用双引号: {'是' if '""' in content and '"""' not in content else '否'}")
    
    if push_path.exists():
        with open(push_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print("push_strategy.toml 格式:")
            print(f"  - 使用三引号: {'是' if '"""' in content else '否'}")
            print(f"  - 使用单引号: {'是' if "'''" in content else '否'}")
            print(f"  - 使用双引号: {'是' if '""' in content and '"""' not in content else '否'}")

if __name__ == "__main__":
    compare_toml_files() 