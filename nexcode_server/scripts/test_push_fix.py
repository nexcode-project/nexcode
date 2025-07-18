#!/usr/bin/env python3
"""
测试push功能修复效果的脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_extract_clean_commit_message():
    """测试提交消息提取函数"""
    print("🧪 测试提交消息提取函数")
    print("=" * 50)
    
    # 模拟extract_clean_commit_message函数
    def extract_clean_commit_message(text: str) -> str:
        """从LLM响应中提取干净的提交消息"""
        if not text:
            return "chore: update code"
        
        # 移除JSON标记和多余空白
        text = text.replace('```json', '').replace('```', '').strip()
        
        # 如果是JSON，尝试提取commit_message字段
        try:
            import json
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                # 按优先级尝试不同的字段名
                for field in ['commit_message', 'message', 'commit', 'title']:
                    if field in parsed and parsed[field]:
                        text = str(parsed[field])
                        break
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        
        # 取第一行并清理
        lines = text.strip().split('\n')
        first_line = lines[0].strip()
        
        # 移除引号格式标记
        first_line = first_line.strip('"\'`')
        
        # 如果包含JSON结构，尝试提取引号中的内容
        if '{' in first_line or '}' in first_line:
            import re
            # 尝试多种模式匹配
            patterns = [
                r'["\']([^"\']+)["\']',  # 引号包围的内容
                r'commit_message["\s]*:["\s]*["\']([^"\']+)["\']',  # JSON字段
                r'message["\s]*:["\s]*["\']([^"\']+)["\']'  # message字段
            ]
            
            for pattern in patterns:
                match = re.search(pattern, first_line)
                if match:
                    first_line = match.group(1)
                    break
            else:
                # 如果没有找到匹配，使用默认消息
                first_line = "chore: update code"
        
        # 长度限制（Git提交消息最佳实践）
        if len(first_line) > 72:
            first_line = first_line[:69] + "..."
        
        # 确保有conventional commits前缀
        conventional_prefixes = ['feat:', 'fix:', 'docs:', 'style:', 'refactor:', 'test:', 'chore:', 'perf:', 'ci:', 'build:']
        
        if not any(first_line.startswith(prefix) for prefix in conventional_prefixes):
            # 基于内容智能判断类型
            lower_line = first_line.lower()
            if any(word in lower_line for word in ['fix', 'bug', 'error', 'issue', 'problem']):
                first_line = f"fix: {first_line}"
            elif any(word in lower_line for word in ['add', 'new', 'create', 'implement', 'feature']):
                first_line = f"feat: {first_line}"
            elif any(word in lower_line for word in ['update', 'modify', 'change', 'improve', 'enhance']):
                first_line = f"refactor: {first_line}"
            elif any(word in lower_line for word in ['doc', 'readme', 'comment']):
                first_line = f"docs: {first_line}"
            elif any(word in lower_line for word in ['test', 'spec']):
                first_line = f"test: {first_line}"
            elif any(word in lower_line for word in ['style', 'format', 'lint']):
                first_line = f"style: {first_line}"
            else:
                first_line = f"chore: {first_line}"
        
        return first_line
    
    test_cases = [
        # 正常JSON格式
        {
            "input": '{"commit_message": "feat: add user authentication"}',
            "expected": "feat: add user authentication"
        },
        # 带markdown的JSON
        {
            "input": '```json\n{"commit_message": "fix: resolve login bug"}\n```',
            "expected": "fix: resolve login bug"
        },
        # 纯文本
        {
            "input": "add new feature for user management",
            "expected": "feat: add new feature for user management"
        },
        # 已有conventional commits格式
        {
            "input": "docs: update README",
            "expected": "docs: update README"
        },
        # 复杂JSON结构
        {
            "input": '{"commit_message": "refactor: improve code structure", "push_command": "git push origin main"}',
            "expected": "refactor: improve code structure"
        },
        # 用户编辑的消息
        {
            "input": "修复了登录页面的样式问题",
            "expected": "fix: 修复了登录页面的样式问题"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        result = extract_clean_commit_message(case["input"])
        status = "✅" if result == case["expected"] else "❌"
        print(f"{i}. {status} 输入: {case['input']}")
        print(f"   输出: {result}")
        print(f"   期望: {case['expected']}")
        print()

def test_user_commit_message_cleaning():
    """测试用户提交消息清理函数"""
    print("🧪 测试用户提交消息清理函数")
    print("=" * 50)
    
    def clean_user_commit_message(message):
        """清理用户输入的提交消息，使其符合Git提交规范，但保留用户编辑"""
        if not message:
            return "feat: update code"
        
        # 移除可能的JSON标记
        message = message.replace('```json', '').replace('```', '').strip()
        
        # 尝试解析JSON（如果LLM返回了JSON格式）
        import json
        try:
            parsed = json.loads(message)
            if isinstance(parsed, dict) and 'commit_message' in parsed:
                message = parsed['commit_message']
            elif isinstance(parsed, dict) and 'message' in parsed:
                message = parsed['message']
        except:
            pass  # 不是JSON，继续处理纯文本
        
        # 只取第一行作为提交消息
        lines = message.strip().split('\n')
        first_line = lines[0].strip()
        
        # 移除引号和其他格式标记
        first_line = first_line.strip('"\'`')
        
        # 如果包含JSON结构标记，提取实际消息
        if '{' in first_line or '}' in first_line:
            # 尝试提取引号中的内容
            import re
            patterns = [
                r'["\']([^"\']+)["\']',  # 引号包围的内容
                r'commit_message["\s]*:["\s]*["\']([^"\']+)["\']',  # JSON字段
                r'message["\s]*:["\s]*["\']([^"\']+)["\']'  # message字段
            ]
            
            for pattern in patterns:
                match = re.search(pattern, first_line)
                if match:
                    first_line = match.group(1)
                    break
            else:
                # 如果没有找到，使用默认消息
                first_line = "chore: update code"
        
        # 如果第一行太长，截断到合理长度
        if len(first_line) > 72:
            first_line = first_line[:69] + "..."
        
        # 检查是否已经有conventional commits格式
        conventional_prefixes = ['feat:', 'fix:', 'docs:', 'style:', 'refactor:', 'test:', 'chore:', 'perf:', 'ci:', 'build:']
        
        # 如果用户已经输入了conventional commits格式，直接返回
        if any(first_line.startswith(prefix) for prefix in conventional_prefixes):
            return first_line
        
        # 如果用户没有使用conventional commits格式，但内容看起来是有效的提交消息，直接返回
        # 这样可以保留用户的编辑意图
        if len(first_line) > 3 and not first_line.startswith('{') and not first_line.startswith('['):
            return first_line
        
        # 只有在内容明显不是提交消息时才添加前缀
        lower_line = first_line.lower()
        if any(word in lower_line for word in ['fix', 'bug', 'error', 'issue', 'problem']):
            first_line = f"fix: {first_line}"
        elif any(word in lower_line for word in ['add', 'new', 'create', 'implement', 'feature']):
            first_line = f"feat: {first_line}"
        elif any(word in lower_line for word in ['update', 'modify', 'change', 'improve', 'enhance']):
            first_line = f"refactor: {first_line}"
        elif any(word in lower_line for word in ['doc', 'readme', 'comment']):
            first_line = f"docs: {first_line}"
        elif any(word in lower_line for word in ['test', 'spec']):
            first_line = f"test: {first_line}"
        elif any(word in lower_line for word in ['style', 'format', 'lint']):
            first_line = f"style: {first_line}"
        else:
            first_line = f"chore: {first_line}"
        
        return first_line
    
    test_cases = [
        # 用户输入conventional commits格式
        {
            "input": "feat: add new authentication system",
            "expected": "feat: add new authentication system"
        },
        # 用户输入普通文本
        {
            "input": "修复了登录bug",
            "expected": "修复了登录bug"  # 保留用户编辑
        },
        # 用户输入带前缀的文本
        {
            "input": "docs: 更新了API文档",
            "expected": "docs: 更新了API文档"
        },
        # 用户输入JSON格式
        {
            "input": '{"commit_message": "fix: resolve issue"}',
            "expected": "fix: resolve issue"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        result = clean_user_commit_message(case["input"])
        status = "✅" if result == case["expected"] else "❌"
        print(f"{i}. {status} 输入: {case['input']}")
        print(f"   输出: {result}")
        print(f"   期望: {case['expected']}")
        print()

def main():
    """主测试函数"""
    print("🚀 开始测试push功能修复效果")
    print("=" * 60)
    
    # 测试提交消息提取
    test_extract_clean_commit_message()
    
    # 测试用户提交消息清理
    test_user_commit_message_cleaning()
    
    print("✅ 测试完成")
    print()
    print("📝 修复总结:")
    print("1. 改进了提交消息提取的准确性")
    print("2. 更好地保留用户编辑的提交消息")
    print("3. 改进了push策略分析的错误处理")
    print("4. 优化了用户交互体验")

if __name__ == "__main__":
    main() 