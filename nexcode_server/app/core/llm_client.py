import openai
from typing import Dict, Any, Optional, Union, List
from .config import settings
from .prompt_loader import get_rendered_prompts
from .token_counter import count_tokens, count_messages_tokens, estimate_total_tokens

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
                model_name: Optional[str] = None,
                use_json_format: bool = False) -> str:
    """
    调用 LLM API
    
    Args:
        system_content: 系统提示词
        user_content: 用户提示词
        api_key: CLI传递的API密钥
        api_base_url: CLI传递的API基础URL
        model_name: CLI传递的模型名称
        use_json_format: 是否使用JSON格式输出
    
    Returns:
        str: LLM 响应内容
    """
    try:
        client = get_openai_client(api_key, api_base_url)
        
        # 优先使用CLI传递的模型名称，没有则使用服务端配置
        model = model_name or settings.OPENAI_MODEL
        
        params = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            "max_tokens": settings.MAX_TOKENS,
            "temperature": settings.TEMPERATURE,
        }
        
        # 根据参数决定是否使用JSON格式
        if use_json_format:
            params["response_format"] = {"type": "json_object"}
        
        response = client.chat.completions.create(**params)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error calling LLM API: {str(e)}"

def call_llm_api_with_params(system_content: str, user_content: str,
                            api_key: Optional[str] = None,
                            api_base_url: Optional[str] = None,
                            model_name: Optional[str] = None,
                            temperature: Optional[float] = None,
                            max_tokens: Optional[int] = None,
                            top_p: Optional[float] = None,
                            presence_penalty: Optional[float] = None,
                            frequency_penalty: Optional[float] = None,
                            stop: Optional[Union[str, List[str]]] = None) -> str:
    """
    调用 LLM API（支持完整的OpenAI参数）
    
    Args:
        system_content: 系统提示词
        user_content: 用户提示词
        api_key: CLI传递的API密钥
        api_base_url: CLI传递的API基础URL
        model_name: CLI传递的模型名称
        temperature: 采样温度
        max_tokens: 最大token数
        top_p: 核采样参数
        presence_penalty: 存在惩罚
        frequency_penalty: 频率惩罚
        stop: 停止序列
    
    Returns:
        str: LLM 响应内容
    """
    try:
        from typing import Union, List
        
        client = get_openai_client(api_key, api_base_url)
        
        # 优先使用传入的参数，没有则使用服务端配置
        model = model_name or settings.OPENAI_MODEL
        temp = temperature if temperature is not None else settings.TEMPERATURE
        max_tok = max_tokens if max_tokens is not None else settings.MAX_TOKENS
        
        # 构建参数字典
        params = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            "temperature": temp,
            "max_tokens": max_tok,
        }
        
        # 添加可选参数
        if top_p is not None:
            params["top_p"] = top_p
        if presence_penalty is not None:
            params["presence_penalty"] = presence_penalty
        if frequency_penalty is not None:
            params["frequency_penalty"] = frequency_penalty
        if stop is not None:
            params["stop"] = stop
            
        response = client.chat.completions.create(**params)
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
        print(f"\n=== LLM DEBUG ({task_type}) ===")
        print(f"Data keys: {list(data.keys())}")
        
        system_content, user_content = get_rendered_prompts(task_type, data)
        
        print(f"System prompt length: {len(system_content)}")
        print(f"User prompt length: {len(user_content)}")
        print(f"User prompt preview (first 300 chars):")
        print(user_content[:300])
        
        # Token统计
        try:
            final_model = model_name or settings.OPENAI_MODEL
            system_tokens = count_tokens(system_content, final_model)
            user_tokens = count_tokens(user_content, final_model)
            total_input_tokens = system_tokens + user_tokens
            
            print(f"Token统计:")
            print(f"  System tokens: {system_tokens}")
            print(f"  User tokens: {user_tokens}")
            print(f"  Total input tokens: {total_input_tokens}")
            print(f"  Model: {final_model}")
        except Exception as e:
            print(f"Token统计错误: {e}")
        
        print("===========================\n")
        
        # 根据任务类型决定是否使用JSON格式和调整温度
        use_json = task_type not in ["commit_message"]
        
        # 为不同任务类型使用不同的温度设置
        if task_type == "commit_message":
            # 提交消息需要更高的确定性
            temperature = 0.1
        else:
            # 其他任务使用默认温度
            temperature = None
        
        if temperature is not None:
            result = call_llm_api_with_params(
                system_content=system_content,
                user_content=user_content,
                api_key=api_key,
                api_base_url=api_base_url,
                model_name=model_name,
                temperature=temperature
            )
        else:
            result = call_llm_api(system_content, user_content, api_key, api_base_url, model_name, use_json)
        
        print(f"LLM response: {result}")
        print("=== END LLM DEBUG ===\n")
        
        return result
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        print(f"LLM Error: {error_msg}")
        return error_msg 