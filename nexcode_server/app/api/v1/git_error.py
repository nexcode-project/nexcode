from fastapi import APIRouter
from app.models.schemas import GitErrorRequest, GitErrorResponse
from app.core.llm_client import get_llm_solution

router = APIRouter()

@router.post("/git-error-analysis", response_model=GitErrorResponse)
async def analyze_git_error(request: GitErrorRequest):
    """
    分析Git错误并提供解决方案
    """
    try:
        # 准备LLM请求数据
        llm_data = {
            "command": " ".join(request.command),
            "error_message": request.error_message
        }
        
        # 调用LLM，传递CLI的API配置
        solution = get_llm_solution(
            task_type="git_error",
            data=llm_data,
            api_key=request.api_key,
            api_base_url=request.api_base_url,
            model_name=request.model_name
        )
        
        return GitErrorResponse(solution=solution)
    except Exception as e:
        return GitErrorResponse(solution=f"Error analyzing git error: {str(e)}") 