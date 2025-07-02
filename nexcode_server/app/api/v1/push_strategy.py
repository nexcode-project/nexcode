from fastapi import APIRouter, Depends
from app.models.schemas import PushStrategyRequest, PushStrategyResponse
from app.core.llm_client import get_llm_solution
from app.core.auth import get_auth_dependency

router = APIRouter()

@router.post("/push-strategy/", response_model=PushStrategyResponse, tags=["Push Strategy"])
async def analyze_push_strategy(req: PushStrategyRequest, _: bool = Depends(get_auth_dependency())):
    """
    推送策略分析
    
    专门为nexcode push命令提供服务，生成提交消息和推送策略
    """
    # 准备传递给 LLM 的数据
    context = {
        "diff": req.diff,
        "target_branch": req.target_branch,
        "repository_type": req.repository_type,
        "current_branch": req.current_branch
    }
    
    # 获取提交消息
    commit_context = {
        "diff": req.diff,
        "style": "conventional"  # 可以从请求中获取
    }
    commit_message = get_llm_solution("commit_message", commit_context)
    
    # 获取推送策略建议
    strategy_analysis = get_llm_solution("push_strategy", context)
    
    # 根据仓库类型生成推送命令
    if req.repository_type == "gerrit":
        push_command = f"git push origin HEAD:refs/for/{req.target_branch}"
    elif req.repository_type == "gitlab":
        push_command = f"git push origin {req.current_branch} -o merge_request.create"
    else:  # github或默认
        push_command = f"git push origin {req.current_branch}"
    
    return PushStrategyResponse(
        commit_message=commit_message,
        push_command=push_command,
        pre_push_checks=[
            "Run tests before push",
            "Check code quality",
            "Verify commit message format"
        ],
        warnings=[]
    ) 