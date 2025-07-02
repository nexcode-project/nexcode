from fastapi import APIRouter, Depends
from app.models.schemas import CommitQARequest, CommitQAResponse
from app.core.llm_client import get_llm_solution
from app.core.auth import get_auth_dependency

router = APIRouter()

@router.post("/commit-qa/", response_model=CommitQAResponse, tags=["Commit QA"])
async def commit_qa(req: CommitQARequest, _: bool = Depends(get_auth_dependency())):
    """
    提交相关问答
    """
    # 准备传递给 LLM 的数据
    context = {
        "question": req.question,
        "context": req.context
    }
    
    # 调用 LLM 获取答案
    answer = get_llm_solution("commit_qa", context)
    
    return CommitQAResponse(answer=answer) 