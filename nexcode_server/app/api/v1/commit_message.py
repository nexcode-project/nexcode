from fastapi import APIRouter, Depends
from app.models.schemas import CommitMessageRequest, CommitMessageResponse
from app.core.llm_client import get_llm_solution
from app.core.auth import get_auth_dependency

router = APIRouter()

@router.post("/commit-message/", response_model=CommitMessageResponse, tags=["Commit Message"])
async def generate_commit_message(req: CommitMessageRequest, _: bool = Depends(get_auth_dependency())):
    """
    生成提交消息
    """
    # 准备传递给 LLM 的数据
    context = {
        "diff": req.diff,
        "style": req.style,
        "context": req.context
    }
    
    # 调用 LLM 获取提交消息
    message = get_llm_solution("commit_message", context)
    
    return CommitMessageResponse(message=message) 