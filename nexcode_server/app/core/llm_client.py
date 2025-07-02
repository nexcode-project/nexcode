import openai
from typing import Dict, Any, Optional
from .config import settings
from .prompt_loader import get_rendered_prompts

def get_openai_client(api_key: Optional[str] = None, api_base_url: Optional[str] = None):
    """
    获取OpenAI客户端
    
    Args:
        api_key: CLI传递的API密钥，如果为空则使用服务端配置
        api_base_url: CLI传递的API基础URL，如果为空则使用服务端配置
    
    Returns:
        OpenAI客户端实例
    """
    # 优先使用CLI传递的配置，没有则fallback到服务端配置
    final_api_key = api_key or settings.OPENAI_API_KEY
    final_base_url = api_base_url or settings.OPENAI_API_BASE
    
    if not final_api_key:
        raise ValueError("No API key available: neither from client request nor server configuration")
    
    client = openai.OpenAI(
        api_key=final_api_key,
        base_url=final_base_url
    )
    return client

def call_llm_api(system_content: str, user_content: str, 
                api_key: Optional[str] = None, 
                api_base_url: Optional[str] = None, 
                model_name: Optional[str] = None) -> str:
    """
    调用 LLM API
    
    Args:
        system_content: 系统提示词
        user_content: 用户提示词
        api_key: CLI传递的API密钥
        api_base_url: CLI传递的API基础URL
        model_name: CLI传递的模型名称
    
    Returns:
        str: LLM 响应内容
    """
    try:
        client = get_openai_client(api_key, api_base_url)
        
        # 优先使用CLI传递的模型名称，没有则使用服务端配置
        model = model_name or settings.OPENAI_MODEL
        
        response = client.chat.completions.create(
            model=model,
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

def get_llm_solution(task_type: str, data: Dict[str, Any], 
                    api_key: Optional[str] = None, 
                    api_base_url: Optional[str] = None, 
                    model_name: Optional[str] = None) -> str:
    """
    统一的 LLM 调用接口
    
    Args:
        task_type: 任务类型（git_error, code_review, commit_qa等）
        data: 请求数据
        api_key: CLI传递的API密钥
        api_base_url: CLI传递的API基础URL
        model_name: CLI传递的模型名称
    
    Returns:
        str: LLM 响应结果
    """
    try:
        system_content, user_content = get_rendered_prompts(task_type, data)
        return call_llm_api(system_content, user_content, api_key, api_base_url, model_name)
    except Exception as e:
        return f"Error processing request: {str(e)}" 