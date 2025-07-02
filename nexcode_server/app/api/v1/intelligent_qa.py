from fastapi import APIRouter, Depends
from app.models.schemas import IntelligentQARequest, IntelligentQAResponse
from app.core.llm_client import get_llm_solution
from app.core.auth import get_auth_dependency

router = APIRouter()

@router.post("/intelligent-qa/", response_model=IntelligentQAResponse, tags=["Intelligent QA"])
async def intelligent_qa(req: IntelligentQARequest, _: bool = Depends(get_auth_dependency())):
    """
    智能问答服务
    
    专门为nexcode ask命令提供增强的问答功能，包括相关主题推荐和建议操作
    """
    # 准备传递给 LLM 的数据
    context = {
        "question": req.question,
        "category": req.category,
        "context": req.context or {}
    }
    
    # 调用 LLM 获取回答
    answer = get_llm_solution("intelligent_qa", context)
    
    # 根据问题类别提供相关主题和建议操作
    related_topics = []
    suggested_actions = []
    
    if req.category == "git":
        related_topics = ["branching", "merging", "rebasing", "remote repositories"]
        suggested_actions = ["Check git status", "Review git log", "Update documentation"]
    elif req.category == "code":
        related_topics = ["code review", "testing", "debugging", "optimization"]
        suggested_actions = ["Run code analysis", "Add unit tests", "Check code style"]
    elif req.category == "workflow":
        related_topics = ["CI/CD", "deployment", "collaboration", "project management"]
        suggested_actions = ["Setup automation", "Review workflow", "Update guidelines"]
    else:  # general
        related_topics = ["best practices", "troubleshooting", "documentation"]
        suggested_actions = ["Read documentation", "Check examples", "Ask for help"]
    
    return IntelligentQAResponse(
        answer=answer,
        related_topics=related_topics,
        suggested_actions=suggested_actions
    ) 