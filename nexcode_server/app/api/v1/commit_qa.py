from fastapi import APIRouter
from app.models.schemas import CommitQARequest, CommitQAResponse
from app.core.llm_client import get_llm_solution

router = APIRouter()

@router.post("/commit-qa", response_model=CommitQAResponse)
async def commit_qa(request: CommitQARequest):
    """
    提交相关问答
    """
    try:
        # 准备LLM请求数据
        llm_data = {
            "question": request.question,
            "context": request.context or {}
        }
        
        # 调用LLM，传递CLI的API配置
        answer = get_llm_solution(
            task_type="commit_qa",
            data=llm_data,
            api_key=request.api_key,
            api_base_url=request.api_base_url,
            model_name=request.model_name
        )
        
        return CommitQAResponse(answer=answer)
    except Exception as e:
        return CommitQAResponse(answer=f"Error processing question: {str(e)}") 