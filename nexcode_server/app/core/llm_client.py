import openai
from typing import Dict, Any
from .config import settings
from .prompt_loader import get_rendered_prompts

def get_openai_client():
    """
    获取OpenAI客户端（使用服务端配置）
    
    Returns:
        OpenAI客户端实例
    """
    client = openai.OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_API_BASE
    )
    return client

def call_llm_api(system_content: str, user_content: str) -> str:
    """
    调用 LLM API（使用服务端配置）
    
    Args:
        system_content: 系统提示词
        user_content: 用户提示词
    
    Returns:
        str: LLM 响应内容
    """
    if not settings.OPENAI_API_KEY:
        return "Error: Server OpenAI API key not configured. Please configure server settings."
    
    client = get_openai_client()
    
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            max_tokens=settings.MAX_TOKENS,
            temperature=settings.TEMPERATURE,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error calling LLM API: {str(e)}"

def get_llm_solution(task_type: str, data: Dict[str, Any]) -> str:
    """
    统一的 LLM 调用接口（使用服务端配置）
    
    Args:
        task_type: 任务类型（git_error, code_review, commit_qa等）
        data: 请求数据
    
    Returns:
        str: LLM 响应结果
    """
    try:
        system_content, user_content = get_rendered_prompts(task_type, data)
        return call_llm_api(system_content, user_content)
    except Exception as e:
        return f"Error processing request: {str(e)}" 