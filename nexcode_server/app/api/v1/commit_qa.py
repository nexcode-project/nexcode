from fastapi import APIRouter, Depends
from app.models.schemas import CommitQARequest, CommitQAResponse
from app.core.llm_client import get_llm_solution
from app.core.auth import get_auth_dependency

router = APIRouter()

@router.post("/commit-qa/", response_model=CommitQAResponse, tags=["Commit QA"])
async def handle_commit_qa(req: CommitQARequest, _: bool = Depends(get_auth_dependency())):
    """
    处理 Commit 相关问答请求
    
    接收用户问题，返回 AI 生成的回答
    """
    # 准备传递给 LLM 的数据
    context = {
        "question": req.question
    }
    
    # 调用 LLM 获取回答，传递客户端的 API 密钥
    answer = get_llm_solution("commit_qa", context, req.api_key)
    return CommitQAResponse(answer=answer) 