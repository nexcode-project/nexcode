from fastapi import APIRouter, Depends
from app.models.schemas import CodeReviewRequest, CodeReviewResponse
from app.core.llm_client import get_llm_solution
from app.core.auth import get_auth_dependency

router = APIRouter()

@router.post("/code-review/", response_model=CodeReviewResponse, tags=["Code Review"])
async def review_code(req: CodeReviewRequest, _: bool = Depends(get_auth_dependency())):
    """
    代码审查
    """
    # 准备传递给 LLM 的数据
    context = {
        "diff": req.diff,
        "check_type": req.check_type
    }
    
    # 调用 LLM 获取分析结果
    analysis = get_llm_solution("code_review", context)
    
    return CodeReviewResponse(analysis=analysis) 