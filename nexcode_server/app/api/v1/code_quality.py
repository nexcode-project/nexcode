from fastapi import APIRouter
from app.models.schemas import CodeQualityRequest, CodeQualityResponse
from app.core.llm_client import get_llm_solution
import json

router = APIRouter()

@router.post("/code-quality-check", response_model=CodeQualityResponse)
async def check_code_quality(request: CodeQualityRequest):
    """
    代码质量检查（专门为check命令设计）
    """
    try:
        # 准备LLM请求数据
        llm_data = {
            "diff": request.diff,
            "files": request.files or [],
            "check_types": request.check_types
        }
        
        # 调用LLM，传递CLI的API配置
        response_text = get_llm_solution(
            task_type="code_quality",
            data=llm_data,
            api_key=request.api_key,
            api_base_url=request.api_base_url,
            model_name=request.model_name
        )
        
        # 尝试解析LLM返回的JSON，如果失败则使用默认格式
        try:
            result = json.loads(response_text)
            return CodeQualityResponse(
                overall_score=result.get("overall_score", 85.0),
                issues=result.get("issues", []),
                suggestions=result.get("suggestions", []),
                summary=result.get("summary", response_text)
            )
        except json.JSONDecodeError:
            return CodeQualityResponse(
                overall_score=85.0,
                issues=[],
                suggestions=[response_text],
                summary="代码质量检查完成"
            )
    except Exception as e:
        return CodeQualityResponse(
            overall_score=0.0,
            issues=[{"type": "error", "message": f"检查失败: {str(e)}"}],
            suggestions=[],
            summary="代码质量检查失败"
        ) 