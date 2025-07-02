from fastapi import APIRouter, Depends
from app.models.schemas import CodeQualityRequest, CodeQualityResponse
from app.core.llm_client import get_llm_solution
from app.core.auth import get_auth_dependency

router = APIRouter()

@router.post("/code-quality/", response_model=CodeQualityResponse, tags=["Code Quality"])
async def analyze_code_quality(req: CodeQualityRequest, _: bool = Depends(get_auth_dependency())):
    """
    代码质量分析
    
    专门为nexcode check命令提供服务，进行全面的代码质量检查
    """
    # 准备传递给 LLM 的数据
    context = {
        "diff": req.diff,
        "files": req.files or [],
        "check_types": req.check_types
    }
    
    # 调用 LLM 获取分析结果
    analysis = get_llm_solution("code_quality", context)
    
    # 解析分析结果（这里可以根据需要进行更复杂的解析）
    # 为了演示，我们返回基本的分析结果
    return CodeQualityResponse(
        overall_score=8.5,  # 可以从LLM结果中解析
        issues=[],  # 可以从LLM结果中提取
        suggestions=["Follow consistent coding style", "Add more comments"],
        summary=analysis
    ) 