from fastapi import APIRouter, Depends
from app.models.schemas import RepositoryAnalysisRequest, RepositoryAnalysisResponse
from app.core.llm_client import get_llm_solution
from app.core.auth import get_auth_dependency

router = APIRouter()

@router.post("/repository-analysis/", response_model=RepositoryAnalysisResponse, tags=["Repository Analysis"])
async def analyze_repository(req: RepositoryAnalysisRequest, _: bool = Depends(get_auth_dependency())):
    """
    仓库分析服务
    
    分析Git仓库的结构、依赖关系和提供优化建议
    """
    # 准备传递给 LLM 的数据
    context = {
        "repository_path": req.repository_path,
        "analysis_type": req.analysis_type
    }
    
    # 调用 LLM 获取分析结果
    analysis = get_llm_solution("repository_analysis", context)
    
    # 模拟仓库结构分析结果
    structure = {
        "total_files": 0,
        "languages": {},
        "directories": [],
        "main_branches": ["main", "develop"],
        "recent_activity": "Active development"
    }
    
    # 根据分析类型提供不同的建议
    recommendations = []
    if req.analysis_type == "overview":
        recommendations = [
            "Consider adding more documentation",
            "Review commit message consistency",
            "Setup continuous integration"
        ]
    elif req.analysis_type == "structure":
        recommendations = [
            "Organize code into logical modules",
            "Add proper README files",
            "Consider using conventional directory structure"
        ]
    elif req.analysis_type == "dependencies":
        recommendations = [
            "Update outdated dependencies",
            "Remove unused dependencies",
            "Add dependency security scanning"
        ]
    
    return RepositoryAnalysisResponse(
        analysis=analysis,
        structure=structure,
        recommendations=recommendations
    ) 