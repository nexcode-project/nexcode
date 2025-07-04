from fastapi import APIRouter, Depends
from time import time
from typing import Optional
from app.models.schemas import CommitMessageRequest, CommitMessageResponse
from app.core.llm_client import get_llm_solution
from app.core.dependencies import OptionalUser, DatabaseSession
from app.services.commit_service import commit_service
from app.models.user_schemas import CommitInfoCreate

router = APIRouter()

@router.post("/commit-message", response_model=CommitMessageResponse)
async def generate_commit_message(
    request: CommitMessageRequest, 
    current_user: OptionalUser,
    db: DatabaseSession
):
    """
    生成提交消息，并记录到数据库
    """
    start_time = time()
    
    try:
        # 准备LLM请求数据
        llm_data = {
            "diff": request.diff,
            "style": request.style,
            "context": request.context or {}
        }
        
        # 调用LLM，传递CLI的API配置
        message = get_llm_solution(
            task_type="commit_message",
            data=llm_data,
            api_key=request.api_key,
            api_base_url=request.api_base_url,
            model_name=request.model_name
        )
        
        generation_time = int((time() - start_time) * 1000)  # 转换为毫秒
        
        # 如果用户已认证，记录到数据库
        if current_user and db:
            try:
                # 解析diff信息（简化版）
                files_changed = []
                lines_added = 0
                lines_deleted = 0
                
                if request.diff:
                    # 简单解析diff（可以后续优化）
                    for line in request.diff.split('\n'):
                        if line.startswith('+++') or line.startswith('---'):
                            if not line.endswith('/dev/null'):
                                files_changed.append(line[4:])
                        elif line.startswith('+') and not line.startswith('+++'):
                            lines_added += 1
                        elif line.startswith('-') and not line.startswith('---'):
                            lines_deleted += 1
                
                # 创建commit信息记录
                commit_data = CommitInfoCreate(
                    repository_url=request.context.get('repository_url') if request.context else None,
                    repository_name=request.context.get('repository_name') if request.context else None,
                    branch_name=request.context.get('branch_name') if request.context else None,
                    ai_generated_message=message,
                    final_commit_message=message,  # 初始情况下，final和ai生成的相同
                    diff_content=request.diff,
                    files_changed=files_changed,
                    lines_added=lines_added,
                    lines_deleted=lines_deleted,
                    ai_model_used=request.model_name,
                    ai_parameters={
                        "api_key": request.api_key[:10] + "..." if request.api_key else None,
                        "api_base_url": request.api_base_url,
                        "style": request.style
                    },
                    generation_time_ms=generation_time,
                    commit_style=request.style or "conventional"
                )
                
                await commit_service.create_commit_info(
                    db=db,
                    user_id=current_user.id,
                    commit_data=commit_data
                )
            except Exception as db_error:
                # 记录数据库错误，但不影响主要功能
                print(f"Database error: {db_error}")
        
        return CommitMessageResponse(message=message)
    except Exception as e:
        return CommitMessageResponse(message=f"Error generating commit message: {str(e)}") 