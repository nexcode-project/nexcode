from fastapi import APIRouter, Depends
from app.models.schemas import GitErrorRequest, GitErrorResponse
from app.core.llm_client import get_llm_solution
from app.core.auth import get_auth_dependency

router = APIRouter()

@router.post("/git-error/", response_model=GitErrorResponse, tags=["Git Error"])
async def analyze_git_error(req: GitErrorRequest, _: bool = Depends(get_auth_dependency())):
    """
    分析Git错误并提供解决方案
    """
    # 准备传递给 LLM 的数据
    context = {
        "command": req.command,
        "error_message": req.error_message
    }
    
    # 调用 LLM 获取解决方案
    solution = get_llm_solution("git_error", context)
    
    return GitErrorResponse(solution=solution) 