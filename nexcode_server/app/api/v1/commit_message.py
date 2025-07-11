from fastapi import APIRouter, Depends
from time import time
from typing import Optional
from app.models.schemas import CommitMessageRequest, CommitMessageResponse
from app.core.llm_client import get_llm_solution
from app.core.dependencies import OptionalUser, DatabaseSession
from app.services.commit_service import commit_service
from app.models.user_schemas import CommitInfoCreate

router = APIRouter()

# 配置diff长度限制 - 增加到更大的值以保持更多上下文
MAX_DIFF_LENGTH = 65536  # 64KB，足够包含大部分代码变更

def clean_commit_message(message: str) -> str:
    """
    清理和优化AI生成的提交消息
    """
    if not message:
        return "chore: update code"
    
    # 移除可能的格式标记
    message = message.replace('```', '').replace('`', '').strip()
    
    # 只取第一行
    first_line = message.split('\n')[0].strip()
    
    # 移除引号和多余空格
    first_line = first_line.strip('"\'`').strip()
    
    # 确保不超过72字符
    if len(first_line) > 72:
        first_line = first_line[:69] + "..."
    
    # 验证conventional commits格式
    valid_prefixes = ['feat:', 'fix:', 'docs:', 'style:', 'refactor:', 'test:', 'chore:', 'build:', 'ci:', 'perf:']
    
    if not any(first_line.startswith(prefix) for prefix in valid_prefixes):
        # 智能判断类型并添加前缀
        lower_msg = first_line.lower()
        if any(word in lower_msg for word in ['fix', 'bug', 'error', 'issue']):
            first_line = f"fix: {first_line}"
        elif any(word in lower_msg for word in ['add', 'new', 'create', 'implement']):
            first_line = f"feat: {first_line}"
        elif any(word in lower_msg for word in ['update', 'modify', 'change', 'improve']):
            first_line = f"refactor: {first_line}"
        elif any(word in lower_msg for word in ['doc', 'readme', 'comment']):
            first_line = f"docs: {first_line}"
        elif any(word in lower_msg for word in ['test', 'spec']):
            first_line = f"test: {first_line}"
        elif any(word in lower_msg for word in ['config', 'setting', 'setup']):
            first_line = f"chore: {first_line}"
        else:
            first_line = f"chore: {first_line}"
    
    # 确保描述部分不重复type
    for prefix in valid_prefixes:
        if first_line.startswith(prefix):
            description = first_line[len(prefix):].strip()
            # 移除描述中重复的type关键词
            description = description.replace(prefix.replace(':', ''), '').strip()
            if description.startswith(':'):
                description = description[1:].strip()
            first_line = prefix + ' ' + description
            break
    
    return first_line

def truncate_diff(diff: str) -> str:
    """
    智能截取diff内容，优先保持重要的代码变更信息
    """
    if not diff or len(diff) <= MAX_DIFF_LENGTH:
        return diff
    
    lines = diff.split('\n')
    important_lines = []
    current_length = 0
    
    # 优先保留重要的diff行
    for line in lines:
        line_with_newline = line + '\n'
        
        # 重要行：文件头、hunk头、实际的代码变更
        is_important = (
            line.startswith('diff --git') or 
            line.startswith('index ') or
            line.startswith('+++') or line.startswith('---') or
            line.startswith('@@') or
            line.startswith('+') or line.startswith('-') or
            line.strip() == ''  # 保留空行以维持结构
        )
        
        if is_important or current_length + len(line_with_newline) <= MAX_DIFF_LENGTH:
            important_lines.append(line)
            current_length += len(line_with_newline)
        else:
            break
    
    # 如果截断了，添加提示
    if len(important_lines) < len(lines):
        important_lines.append('')
        important_lines.append('[... diff truncated - showing most relevant changes ...]')
    
    return '\n'.join(important_lines)

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
        
        # 清理和优化生成的消息
        cleaned_message = clean_commit_message(message)
        print(f"Cleaned message: {cleaned_message}")
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
                    final_commit_message=cleaned_message,  # 使用清理后的消息
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
        
        return CommitMessageResponse(message=cleaned_message)
    except Exception as e:
        return CommitMessageResponse(message=f"Error generating commit message: {str(e)}") 