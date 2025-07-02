from fastapi import APIRouter, Depends
from app.models.schemas import GitErrorRequest, GitErrorResponse
from app.core.llm_client import get_llm_solution
from app.core.auth import get_auth_dependency

router = APIRouter()

@router.post("/git-error/", response_model=GitErrorResponse, tags=["Git Error"])
async def handle_git_error(req: GitErrorRequest, _: bool = Depends(get_auth_dependency())):
    """
    处理 Git 错误分析请求
    
    接收 Git 命令和错误信息，返回 AI 生成的解决方案
    """
    # 准备传递给 LLM 的数据
    context = {
        "command": " ".join(req.command),
        "error_message": req.error_message
    }
    
    # 调用 LLM 获取解决方案，传递客户端的 API 密钥
    solution = get_llm_solution("git_error", context, req.api_key)
    return GitErrorResponse(solution=solution) 