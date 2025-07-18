#!/usr/bin/env python3
"""
测试push策略prompt的加载和渲染
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from app.core.prompt_loader import get_rendered_prompts

def test_push_strategy_prompt():
    """测试push策略prompt的加载和渲染"""
    print("🧪 测试push策略prompt加载和渲染")
    print("=" * 50)
    
    # 模拟push策略的上下文数据
    context = {
        "diff": """
diff --git a/src/components/Login.tsx b/src/components/Login.tsx
index abc123..def456 100644
--- a/src/components/Login.tsx
+++ b/src/components/Login.tsx
@@ -10,6 +10,7 @@ export const Login = () => {
   const [email, setEmail] = useState('');
   const [password, setPassword] = useState('');
+  const [rememberMe, setRememberMe] = useState(false);
 
   const handleSubmit = async (e: React.FormEvent) => {
     e.preventDefault();
@@ -20,6 +21,9 @@ export const Login = () => {
       <input
         type="email"
         value={email}
+        placeholder="Enter your email"
+        required
         onChange={(e) => setEmail(e.target.value)}
       />
       <input
@@ -27,6 +31,12 @@ export const Login = () => {
         value={password}
         onChange={(e) => setPassword(e.target.value)}
       />
+      <label>
+        <input
+          type="checkbox"
+          checked={rememberMe}
+          onChange={(e) => setRememberMe(e.target.checked)}
+        />
+        Remember me
+      </label>
       <button type="submit">Login</button>
     </form>
   );
""",
        "current_branch": "feature/login-enhancement",
        "target_branch": "main",
        "repository_type": "github"
    }
    
    try:
        # 获取渲染后的prompt
        system_prompt, user_prompt = get_rendered_prompts("push_strategy", context)
        
        print("✅ Prompt加载成功!")
        print()
        
        print("📋 系统Prompt长度:", len(system_prompt))
        print("📋 用户Prompt长度:", len(user_prompt))
        print()
        
        print("📋 系统Prompt:")
        print("-" * 30)
        print(system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt)
        print()
        
        print("📋 用户Prompt:")
        print("-" * 30)
        if user_prompt:
            print(user_prompt[:300] + "..." if len(user_prompt) > 300 else user_prompt)
        else:
            print("❌ 用户Prompt为空!")
        print()
        
        # 检查模板变量是否正确替换
        if "{{ diff }}" not in user_prompt and "{{ current_branch }}" not in user_prompt:
            print("✅ 模板变量替换成功!")
        else:
            print("❌ 模板变量替换失败!")
            print("未替换的变量:")
            if "{{ diff }}" in user_prompt:
                print("  - {{ diff }}")
            if "{{ current_branch }}" in user_prompt:
                print("  - {{ current_branch }}")
            if "{{ target_branch }}" in user_prompt:
                print("  - {{ target_branch }}")
            if "{{ repository_type }}" in user_prompt:
                print("  - {{ repository_type }}")
        
    except Exception as e:
        print(f"❌ Prompt加载失败: {e}")
        import traceback
        traceback.print_exc()

def test_other_prompts():
    """测试其他prompt的加载"""
    print("\n🧪 测试其他prompt加载")
    print("=" * 50)
    
    test_cases = [
        ("code_quality", {"diff": "test diff", "files": "test.js", "check_types": "bugs"}),
        ("git_error", {"command": "git push", "error_message": "Permission denied"}),
        ("commit_qa", {"question": "What is this commit about?"})
    ]
    
    for task_type, context in test_cases:
        try:
            system_prompt, user_prompt = get_rendered_prompts(task_type, context)
            print(f"✅ {task_type}: 加载成功")
        except Exception as e:
            print(f"❌ {task_type}: 加载失败 - {e}")

def main():
    """主测试函数"""
    print("🚀 开始测试prompt加载和渲染")
    print("=" * 60)
    
    # 测试push策略prompt
    test_push_strategy_prompt()
    
    # 测试其他prompt
    test_other_prompts()
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    main() 