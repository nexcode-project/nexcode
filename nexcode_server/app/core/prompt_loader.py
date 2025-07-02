import toml
from pathlib import Path
from typing import Dict, Any

# 获取 prompts 目录路径
PROMPT_DIR = Path(__file__).parent.parent.parent / "prompts"

def load_prompt(prompt_name: str) -> Dict[str, Any]:
    """
    加载指定的 prompt 配置文件
    
    Args:
        prompt_name: prompt 文件名（不含扩展名）
    
    Returns:
        Dict: prompt 配置内容
    
    Raises:
        FileNotFoundError: 如果 prompt 文件不存在
    """
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
    # 简单的模板变量替换，可以后续扩展为 Jinja2
    rendered = template
    for key, value in context.items():
        placeholder = f"{{{{ {key} }}}}"
        rendered = rendered.replace(placeholder, str(value))
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
    prompt_config = load_prompt(task_type)
    
    system_content = prompt_config.get("system", {}).get("content", "")
    user_template = prompt_config.get("user", {}).get("template", "")
    
    user_content = render_prompt(user_template, context)
    
    return system_content, user_content 