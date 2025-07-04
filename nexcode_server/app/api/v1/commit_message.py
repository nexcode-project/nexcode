from fastapi import APIRouter, Depends
from time import time
from typing import Optional
from app.models.schemas import CommitMessageRequest, CommitMessageResponse
from app.core.llm_client import get_llm_solution
from app.core.dependencies import OptionalUser, DatabaseSession
from app.services.commit_service import commit_service
from app.models.user_schemas import CommitInfoCreate

router = APIRouter()

# 配置diff长度限制
MAX_DIFF_LENGTH = 32648

def truncate_diff(diff: str) -> str:
    """
    截取diff内容到指定长度，确保不破坏diff结构
    """
    if not diff or len(diff) <= MAX_DIFF_LENGTH:
        return diff
    
    # 截取到最大长度
    truncated = diff[:MAX_DIFF_LENGTH]
    
    # 尝试在行边界截取，避免破坏diff结构
    last_newline = truncated.rfind('\n')
    if last_newline > MAX_DIFF_LENGTH * 0.8:  # 如果最后一个换行符在80%位置之后
        truncated = truncated[:last_newline]
    
    # 添加截取提示
    truncated += "\n\n[... diff truncated to fit size limit ...]"
    
    return truncated

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
        # 截取diff长度
        original_diff = request.diff
        truncated_diff = truncate_diff(original_diff) if original_diff else None
        
        # 调试输出：显示接收到的数据
        print(f"\n=== COMMIT MESSAGE DEBUG ===")
        print(f"Style: {request.style}")
        print(f"API Key: {request.api_key[:10] + '...' if request.api_key else 'None'}")
        print(f"Model Name: {request.model_name}")
        print(f"Original diff length: {len(original_diff) if original_diff else 0}")
        print(f"Truncated diff length: {len(truncated_diff) if truncated_diff else 0}")
        print(f"Diff preview (first 500 chars):")
        print(truncated_diff[:500] if truncated_diff else "No diff")
        print(f"Context: {request.context}")
        print("===========================\n")
        
        # 准备LLM请求数据，使用截取后的diff
        llm_data = {
            "diff": truncated_diff,
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
        
        print(f"Generated message: {message}")
        print("=== END DEBUG ===\n")
        
        generation_time = int((time() - start_time) * 1000)  # 转换为毫秒
        
        # 如果用户已认证，记录到数据库
        if current_user and db:
            try:
                # 解析diff信息（简化版）
                files_changed = []
                lines_added = 0
                lines_deleted = 0
                
                if truncated_diff:
                    # 简单解析diff（可以后续优化）
                    for line in truncated_diff.split('\n'):
                        if line.startswith('+++') or line.startswith('---'):
                            if not line.endswith('/dev/null'):
                                file_path = line[4:].strip()
                                if file_path and file_path not in files_changed:
                                    files_changed.append(file_path)
                        elif line.startswith('+') and not line.startswith('+++'):
                            lines_added += 1
                        elif line.startswith('-') and not line.startswith('---'):
                            lines_deleted += 1
                
                # 创建commit信息记录 - 存储原始diff长度信息
                commit_data = CommitInfoCreate(
                    repository_url=request.context.get('repository_url') if request.context else None,
                    repository_name=request.context.get('repository_name') if request.context else None,
                    branch_name=request.context.get('branch_name') if request.context else None,
                    ai_generated_message=message,
                    final_commit_message=message,  # 初始情况下，final和ai生成的相同
                    diff_content=truncated_diff,  # 存储截取后的diff
                    files_changed=files_changed,
                    lines_added=lines_added,
                    lines_deleted=lines_deleted,
                    ai_model_used=request.model_name,
                    ai_parameters={
                        "api_key": request.api_key[:10] + "..." if request.api_key else None,
                        "api_base_url": request.api_base_url,
                        "style": request.style,
                        "original_diff_length": len(original_diff) if original_diff else 0,
                        "truncated_diff_length": len(truncated_diff) if truncated_diff else 0,
                        "was_truncated": len(original_diff) > MAX_DIFF_LENGTH if original_diff else False
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