from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
import time
import uuid
from app.models.openai_schemas import (
    ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChoice, Usage, Message, Role,
    CompletionRequest, CompletionResponse, CompletionChoice
)
from app.core.llm_client import call_llm_api_with_params
from app.core.config import settings
from app.core.token_counter import count_tokens, count_messages_tokens

router = APIRouter()

def _generate_id() -> str:
    """生成唯一的请求ID"""
    return f"chatcmpl-{uuid.uuid4().hex[:16]}"

def _create_usage(prompt: str, completion: str, model_name: str = "gpt-3.5-turbo") -> Usage:
    """创建usage统计（使用tiktoken精确计算）"""
    try:
        prompt_tokens = count_tokens(prompt, model_name)
        completion_tokens = count_tokens(completion, model_name)
        total_tokens = prompt_tokens + completion_tokens
        
        return Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )
    except Exception as e:
        # 回退到简单估算
        prompt_tokens = int(len(prompt.split()) * 1.3)
        completion_tokens = int(len(completion.split()) * 1.3)
        return Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )

async def verify_auth(authorization: Optional[str] = Header(None)):
    """验证认证"""
    if settings.REQUIRE_AUTH:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        
        token = authorization.replace("Bearer ", "")
        if token != settings.API_TOKEN:
            raise HTTPException(status_code=401, detail="Invalid API token")
    
    # 从Authorization header中提取API key（如果提供）
    api_key = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        # 如果token不是服务端的API_TOKEN，则当作OpenAI API key使用
        if token != settings.API_TOKEN:
            api_key = token
    
    return api_key

@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    api_key: Optional[str] = Depends(verify_auth)
):
    """OpenAI Chat Completions API兼容接口"""
    try:
        # 提取系统消息和用户消息
        system_messages = [msg.content for msg in request.messages if msg.role == Role.SYSTEM]
        user_messages = [msg.content for msg in request.messages if msg.role == Role.USER]
        
        system_content = "\n".join(system_messages) if system_messages else ""
        user_content = "\n".join(user_messages) if user_messages else ""
        
        # 调用扩展的LLM API
        completion_content = call_llm_api_with_params(
            system_content=system_content,
            user_content=user_content,
            api_key=api_key,
            model_name=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            presence_penalty=request.presence_penalty,
            frequency_penalty=request.frequency_penalty,
            stop=request.stop
        )
        
        # 创建响应
        choice = ChatCompletionChoice(
            index=0,
            message=Message(role=Role.ASSISTANT, content=completion_content),
            finish_reason="stop"
        )
        
        usage = _create_usage(
            prompt=system_content + "\n" + user_content,
            completion=completion_content,
            model_name=request.model
        )
        
        return ChatCompletionResponse(
            id=_generate_id(),
            created=int(time.time()),
            model=request.model,
            choices=[choice],
            usage=usage
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/completions", response_model=CompletionResponse)
async def completions(
    request: CompletionRequest,
    api_key: Optional[str] = Depends(verify_auth)
):
    """OpenAI Text Completions API兼容接口"""
    try:
        prompt = request.prompt if isinstance(request.prompt, str) else "\n".join(request.prompt)
        
        # 调用扩展的LLM API（作为简单的文本补全）
        completion_content = call_llm_api_with_params(
            system_content="你是一个专业的代码补全助手，请根据用户的问题，给出最准确的代码补全。",
            user_content=prompt,
            api_key=api_key,
            model_name=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            presence_penalty=request.presence_penalty,
            frequency_penalty=request.frequency_penalty,
            stop=request.stop
        )
        
        # 创建响应
        choice = CompletionChoice(
            text=completion_content,
            index=0,
            finish_reason="stop"
        )
        
        usage = _create_usage(
            prompt=prompt,
            completion=completion_content,
            model_name=request.model
        )
        
        return CompletionResponse(
            id=_generate_id(),
            created=int(time.time()),
            model=request.model,
            choices=[choice],
            usage=usage
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 