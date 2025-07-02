from fastapi import APIRouter
from app.models.schemas import CodeReviewRequest, CodeReviewResponse
from app.core.llm_client import get_llm_solution
import json

router = APIRouter()

@router.post("/code-review", response_model=CodeReviewResponse)
async def review_code(request: CodeReviewRequest):
    """
    代码审查
    """
    try:
        # 准备LLM请求数据
        llm_data = {
            "diff": request.diff,
            "check_type": request.check_type
        }
        
        # 调用LLM，传递CLI的API配置
        response_text = get_llm_solution(
            task_type="code_review",
            data=llm_data,
            api_key=request.api_key,
            api_base_url=request.api_base_url,
            model_name=request.model_name
        )
        
        # 尝试解析LLM返回的JSON，如果失败则使用默认格式
        try:
            result = json.loads(response_text)
            return CodeReviewResponse(
                analysis=result.get("analysis", response_text),
                issues=result.get("issues", []),
                suggestions=result.get("suggestions", []),
                severity=result.get("severity", "info")
            )
        except json.JSONDecodeError:
            return CodeReviewResponse(
                analysis=response_text,
                issues=[],
                suggestions=[],
                severity="info"
            )
    except Exception as e:
        return CodeReviewResponse(
            analysis=f"Error during code review: {str(e)}",
            issues=[],
            suggestions=[],
            severity="error"
        ) 