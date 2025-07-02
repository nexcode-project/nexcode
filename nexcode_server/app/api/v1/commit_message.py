from fastapi import APIRouter
from app.models.schemas import CommitMessageRequest, CommitMessageResponse
from app.core.llm_client import get_llm_solution

router = APIRouter()

@router.post("/commit-message", response_model=CommitMessageResponse)
async def generate_commit_message(request: CommitMessageRequest):
    """
    生成提交消息
    """
    try:
        # 准备LLM请求数据
        llm_data = {
            "diff": request.diff,
            "style": request.style,
            "context": request.context or {}
        }
        
        # 调用LLM，传递CLI的API配置
        message = get_llm_solution(
            task_type="commit_message",
            data=llm_data,
            api_key=request.api_key,
            api_base_url=request.api_base_url,
            model_name=request.model_name
        )
        
        return CommitMessageResponse(message=message)
    except Exception as e:
        return CommitMessageResponse(message=f"Error generating commit message: {str(e)}") 