import toml
from pathlib import Path
from typing import Dict, Any

# 获取 prompts 目录路径
PROMPT_DIR = Path(__file__).parent.parent.parent / "prompts"

def load_prompt(prompt_name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    加载指定的 prompt 配置文件，支持自动选择优化版本
    
    Args:
        prompt_name: prompt 文件名（不含扩展名）
        context: 上下文信息，用于判断是否使用中文优化版本
    
    Returns:
        Dict: prompt 配置内容
    
    Raises:
        FileNotFoundError: 如果 prompt 文件不存在
    """
    # 检查是否有中文内容，如果有则尝试使用中文优化版本
    use_zh_optimized = False
    if context and prompt_name == "commit_message":
        # 检查diff或其他内容是否包含中文
        diff_content = context.get('diff', '')
        if diff_content and any('\u4e00' <= char <= '\u9fff' for char in diff_content):
            use_zh_optimized = True
    
    # 尝试使用中文优化版本
    if use_zh_optimized:
        zh_prompt_path = PROMPT_DIR / f"{prompt_name}_zh.toml"
        if zh_prompt_path.exists():
            return toml.load(zh_prompt_path)
    
    # 使用默认版本
    prompt_path = PROMPT_DIR / f"{prompt_name}.toml"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file {prompt_path} not found.")
    return toml.load(prompt_path)

def render_prompt(template: str, context: Dict[str, Any]) -> str:
    """
    渲染 prompt 模板，替换模板变量
    
    Args:
        template: 模板字符串
        context: 模板变量上下文
    
    Returns:
        str: 渲染后的字符串
    """
    import re
    
    # 简单的模板变量替换，支持有空格和无空格的格式
    rendered = template
    for key, value in context.items():
        # 支持 {{ key }} 和 {{key}} 两种格式
        pattern1 = f"{{{{\\s*{key}\\s*}}}}"
        rendered = re.sub(pattern1, str(value), rendered)
    return rendered

def get_rendered_prompts(task_type: str, context: Dict[str, Any]) -> tuple[str, str]:
    """
    获取渲染后的系统和用户 prompt
    
    Args:
        task_type: 任务类型
        context: 模板变量上下文
    
    Returns:
        tuple: (system_prompt, user_prompt)
    """
    prompt_config = load_prompt(task_type, context)
    print(f"Prompt config: {prompt_config}")
    system_content = prompt_config.get(task_type, {}).get("system", "")
    user_template = prompt_config.get(task_type, {}).get("content", "")
    
    user_content = render_prompt(user_template, context)
    
    return system_content, user_content 