from fastapi import APIRouter, Depends
from app.models.schemas import CodeReviewRequest, CodeReviewResponse
from app.core.llm_client import get_llm_solution
from app.core.auth import get_auth_dependency

router = APIRouter()

@router.post("/code-review/", response_model=CodeReviewResponse, tags=["Code Review"])
async def handle_code_review(req: CodeReviewRequest, _: bool = Depends(get_auth_dependency())):
    """
    处理代码审查请求
    
    接收 Git diff 内容，返回 AI 生成的代码分析结果
    """
    # 准备传递给 LLM 的数据
    context = {
        "diff": req.diff
    }
    
    # 调用 LLM 获取分析结果，传递客户端的 API 密钥
    analysis = get_llm_solution("code_review", context, req.api_key)
    return CodeReviewResponse(analysis=analysis) 