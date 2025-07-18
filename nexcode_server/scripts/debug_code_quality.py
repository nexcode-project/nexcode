#!/usr/bin/env python3
"""
调试code_quality.toml文件加载
"""

import toml
from pathlib import Path

def debug_code_quality_toml():
    """调试code_quality.toml文件加载"""
    prompt_path = Path(__file__).parent.parent / "prompts" / "code_quality.toml"
    
    print(f"📁 文件路径: {prompt_path}")
    print(f"📁 文件存在: {prompt_path.exists()}")
    print()
    
    if prompt_path.exists():
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print("📄 文件内容:")
                print("=" * 50)
                print(content)
                print("=" * 50)
                print()
            
            # 尝试解析TOML
            config = toml.load(prompt_path)
            print("🔍 解析结果:")
            print("=" * 50)
            print(config)
            print("=" * 50)
            print()
            
            # 检查字段
            if 'code_quality' in config:
                quality_config = config['code_quality']
                print("📋 code_quality字段:")
                print(f"  - system: {'存在' if 'system' in quality_config else '不存在'}")
                print(f"  - content: {'存在' if 'content' in quality_config else '不存在'}")
                print(f"  - 所有字段: {list(quality_config.keys())}")
                
                if 'system' in quality_config:
                    print(f"  - system长度: {len(quality_config['system'])}")
                if 'content' in quality_config:
                    print(f"  - content长度: {len(quality_config['content'])}")
            else:
                print("❌ 没有找到code_quality字段")
                print(f"  可用字段: {list(config.keys())}")
                
        except Exception as e:
            print(f"❌ TOML解析失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_code_quality_toml() 