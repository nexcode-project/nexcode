from fastapi import APIRouter
from app.models.schemas import RepositoryAnalysisRequest, RepositoryAnalysisResponse
from app.core.llm_client import get_llm_solution
import json

router = APIRouter()

@router.post("/repository-analysis", response_model=RepositoryAnalysisResponse)
async def analyze_repository(request: RepositoryAnalysisRequest):
    """
    仓库分析
    """
    try:
        # 准备LLM请求数据
        llm_data = {
            "repository_path": request.repository_path,
            "analysis_type": request.analysis_type
        }
        
        # 调用LLM，传递CLI的API配置
        response_text = get_llm_solution(
            task_type="repository_analysis",
            data=llm_data,
            api_key=request.api_key,
            api_base_url=request.api_base_url,
            model_name=request.model_name
        )
        
        # 尝试解析LLM返回的JSON，如果失败则使用默认格式
        try:
            result = json.loads(response_text)
            return RepositoryAnalysisResponse(
                analysis=result.get("analysis", response_text),
                structure=result.get("structure", {}),
                recommendations=result.get("recommendations", [])
            )
        except json.JSONDecodeError:
            return RepositoryAnalysisResponse(
                analysis=response_text,
                structure={},
                recommendations=[]
            )
    except Exception as e:
        return RepositoryAnalysisResponse(
            analysis=f"Error analyzing repository: {str(e)}",
            structure={},
            recommendations=[]
        ) 