import openai
from typing import Dict, Any, Optional
from .config import settings
from .prompt_loader import get_rendered_prompts

def get_openai_client(api_key: str):
    """
    获取OpenAI客户端
    
    Args:
        api_key: 客户端提供的API密钥
    
    Returns:
        OpenAI客户端实例或None
    """
    if not api_key:
        return None
    
    client = openai.OpenAI(
        api_key=api_key,
        base_url=settings.OPENAI_API_BASE
    )
    return client

def call_llm_api(system_content: str, user_content: str, api_key: str) -> str:
    """
    调用 LLM API
    
    Args:
        system_content: 系统提示词
        user_content: 用户提示词
        api_key: 客户端提供的API密钥
    
    Returns:
        str: LLM 响应内容
    """
    if not api_key:
        return "Error: No API key provided by client. Please configure your OpenAI API key in the CLI."
    
    client = get_openai_client(api_key)
    if not client:
        return "Error: Failed to create OpenAI client with provided API key."
    
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

def get_llm_solution(task_type: str, data: Dict[str, Any], api_key: str) -> str:
    """
    统一的 LLM 调用接口
    
    Args:
        task_type: 任务类型（git_error, code_review, commit_qa）
        data: 请求数据
        api_key: 客户端提供的API密钥
    
    Returns:
        str: LLM 响应结果
    """
    try:
        system_content, user_content = get_rendered_prompts(task_type, data)
        return call_llm_api(system_content, user_content, api_key)
    except Exception as e:
        return f"Error processing request: {str(e)}" 