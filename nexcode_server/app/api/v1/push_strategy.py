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
            
            # 验证JSON结构
            if not isinstance(result, dict):
                raise ValueError("LLM返回的不是有效的JSON对象")
            
            # 提取并验证各个字段
            extracted_commit_message = result.get("commit_message", commit_message)
            if extracted_commit_message and isinstance(extracted_commit_message, str):
                commit_message = extract_clean_commit_message(extracted_commit_message)
            
            push_command = result.get("push_command", f"git push origin {request.current_branch}")
            if not push_command or not isinstance(push_command, str):
                push_command = f"git push origin {request.current_branch}"
            
            pre_push_checks = result.get("pre_push_checks", [])
            if not isinstance(pre_push_checks, list):
                pre_push_checks = ["确认代码质量", "检查测试覆盖率"]
            
            warnings = result.get("warnings", [])
            if not isinstance(warnings, list):
                warnings = []
            
            return PushStrategyResponse(
                commit_message=commit_message,
                push_command=push_command,
                pre_push_checks=pre_push_checks,
                warnings=warnings
            )
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            # 如果JSON解析失败，使用提取的提交消息和默认值
            return PushStrategyResponse(
                commit_message=commit_message,
                push_command=f"git push origin {request.current_branch}",
                pre_push_checks=["确认代码质量", "检查测试覆盖率"],
                warnings=[f"LLM响应解析失败，使用默认值: {str(e)}"]
            )
    except Exception as e:
        # 记录详细错误信息
        print(f"Push strategy analysis error: {str(e)}")
        return PushStrategyResponse(
            commit_message="chore: update code",
            push_command=f"git push origin {request.current_branch}",
            pre_push_checks=[],
            warnings=[f"推送策略分析失败: {str(e)}"]
        )


def extract_clean_commit_message(text: str) -> str:
    """从LLM响应中提取干净的提交消息"""
    if not text:
        return "chore: update code"
    
    # 移除JSON标记和多余空白
    text = text.replace('```json', '').replace('```', '').strip()
    
    # 如果是JSON，尝试提取commit_message字段
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            # 按优先级尝试不同的字段名
            for field in ['commit_message', 'message', 'commit', 'title']:
                if field in parsed and parsed[field]:
                    text = str(parsed[field])
                    break
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    
    # 取第一行并清理
    lines = text.strip().split('\n')
    first_line = lines[0].strip()
    
    # 移除引号和格式标记
    first_line = first_line.strip('"\'`')
    
    # 如果包含JSON结构，尝试提取引号中的内容
    if '{' in first_line or '}' in first_line:
        import re
        # 尝试多种模式匹配
        patterns = [
            r'["\']([^"\']+)["\']',  # 引号包围的内容
            r'commit_message["\s]*:["\s]*["\']([^"\']+)["\']',  # JSON字段
            r'message["\s]*:["\s]*["\']([^"\']+)["\']'  # message字段
        ]
        
        for pattern in patterns:
            match = re.search(pattern, first_line)
            if match:
                first_line = match.group(1)
                break
        else:
            # 如果没有找到匹配，使用默认消息
            first_line = "chore: update code"
    
    # 长度限制（Git提交消息最佳实践）
    if len(first_line) > 72:
        first_line = first_line[:69] + "..."
    
    # 确保有conventional commits前缀
    conventional_prefixes = ['feat:', 'fix:', 'docs:', 'style:', 'refactor:', 'test:', 'chore:', 'perf:', 'ci:', 'build:']
    
    if not any(first_line.startswith(prefix) for prefix in conventional_prefixes):
        # 基于内容智能判断类型
        lower_line = first_line.lower()
        if any(word in lower_line for word in ['fix', 'bug', 'error', 'issue', 'problem']):
            first_line = f"fix: {first_line}"
        elif any(word in lower_line for word in ['add', 'new', 'create', 'implement', 'feature']):
            first_line = f"feat: {first_line}"
        elif any(word in lower_line for word in ['update', 'modify', 'change', 'improve', 'enhance']):
            first_line = f"refactor: {first_line}"
        elif any(word in lower_line for word in ['doc', 'readme', 'comment']):
            first_line = f"docs: {first_line}"
        elif any(word in lower_line for word in ['test', 'spec']):
            first_line = f"test: {first_line}"
        elif any(word in lower_line for word in ['style', 'format', 'lint']):
            first_line = f"style: {first_line}"
        else:
            first_line = f"chore: {first_line}"
    
    return first_line 