from fastapi import APIRouter
from app.models.schemas import PushStrategyRequest, PushStrategyResponse
from app.core.llm_client import get_llm_solution
import json
import re

router = APIRouter()

@router.post("/push-strategy", response_model=PushStrategyResponse)
async def analyze_push_strategy(request: PushStrategyRequest):
    """
    推送策略分析（专门为push命令设计）
    """
    try:
        # 准备LLM请求数据
        llm_data = {
            "diff": request.diff,
            "target_branch": request.target_branch,
            "repository_type": request.repository_type,
            "current_branch": request.current_branch
        }
        
        # 调用LLM，传递CLI的API配置
        response_text = get_llm_solution(
            task_type="push_strategy",
            data=llm_data,
            api_key=request.api_key,
            api_base_url=request.api_base_url,
            model_name=request.model_name
        )
        
        # 清理并解析LLM返回的内容
        commit_message = extract_clean_commit_message(response_text)
        
        # 尝试解析LLM返回的JSON，如果失败则使用默认格式
        try:
            # 清理response_text中的markdown标记
            cleaned_response = response_text.replace('```json', '').replace('```', '').strip()
            result = json.loads(cleaned_response)
            
            return PushStrategyResponse(
                commit_message=extract_clean_commit_message(result.get("commit_message", commit_message)),
                push_command=result.get("push_command", f"git push origin {request.current_branch}"),
                pre_push_checks=result.get("pre_push_checks", ["确认代码质量", "检查测试覆盖率"]),
                warnings=result.get("warnings", [])
            )
        except json.JSONDecodeError:
            return PushStrategyResponse(
                commit_message=commit_message,
                push_command=f"git push origin {request.current_branch}",
                pre_push_checks=["确认代码质量", "检查测试覆盖率"],
                warnings=[]
            )
    except Exception as e:
        return PushStrategyResponse(
            commit_message="chore: update code",
            push_command="",
            pre_push_checks=[],
            warnings=[f"推送策略分析失败: {str(e)}"]
        )


def extract_clean_commit_message(text: str) -> str:
    """从LLM响应中提取干净的提交消息"""
    if not text:
        return "chore: update code"
    
    # 移除JSON标记
    text = text.replace('```json', '').replace('```', '').strip()
    
    # 如果是JSON，尝试提取commit_message字段
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and 'commit_message' in parsed:
            text = parsed['commit_message']
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    
    # 取第一行
    first_line = text.strip().split('\n')[0].strip()
    
    # 移除引号和格式标记
    first_line = first_line.strip('"\'`')
    
    # 如果包含JSON结构，提取引号中的内容
    if '{' in first_line or '}' in first_line:
        match = re.search(r'["\']([^"\']+)["\']', first_line)
        if match:
            first_line = match.group(1)
        else:
            first_line = "chore: update code"
    
    # 长度限制
    if len(first_line) > 72:
        first_line = first_line[:69] + "..."
    
    # 确保有conventional commits前缀
    if not any(first_line.startswith(prefix) for prefix in ['feat:', 'fix:', 'docs:', 'style:', 'refactor:', 'test:', 'chore:']):
        if 'fix' in first_line.lower() or 'bug' in first_line.lower():
            first_line = f"fix: {first_line}"
        elif 'add' in first_line.lower() or 'new' in first_line.lower():
            first_line = f"feat: {first_line}"
        elif 'update' in first_line.lower() or 'modify' in first_line.lower():
            first_line = f"refactor: {first_line}"
        else:
            first_line = f"chore: {first_line}"
    
    return first_line 