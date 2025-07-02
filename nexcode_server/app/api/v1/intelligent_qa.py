from fastapi import APIRouter
from app.models.schemas import IntelligentQARequest, IntelligentQAResponse
from app.core.llm_client import get_llm_solution
import json

router = APIRouter()

@router.post("/intelligent-qa", response_model=IntelligentQAResponse)
async def intelligent_qa(request: IntelligentQARequest):
    """
    智能问答（专门为ask命令设计）
    """
    try:
        # 准备LLM请求数据
        llm_data = {
            "question": request.question,
            "category": request.category,
            "context": request.context or {}
        }
        
        # 调用LLM，传递CLI的API配置
        response_text = get_llm_solution(
            task_type="intelligent_qa",
            data=llm_data,
            api_key=request.api_key,
            api_base_url=request.api_base_url,
            model_name=request.model_name
        )
        
        # 尝试解析LLM返回的JSON，如果失败则使用默认格式
        try:
            result = json.loads(response_text)
            return IntelligentQAResponse(
                answer=result.get("answer", response_text),
                related_topics=result.get("related_topics", []),
                suggested_actions=result.get("suggested_actions", [])
            )
        except json.JSONDecodeError:
            return IntelligentQAResponse(
                answer=response_text,
                related_topics=[],
                suggested_actions=[]
            )
    except Exception as e:
        return IntelligentQAResponse(
            answer=f"Error processing question: {str(e)}",
            related_topics=[],
            suggested_actions=[]
        ) 