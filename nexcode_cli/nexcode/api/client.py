"""
API客户端模块
统一管理所有后端API请求
"""

from typing import Dict, Any, Optional, List

import requests

from ..config import get_merged_config
from .endpoints import ENDPOINTS


class NexCodeAPIClient:
    """统一的API客户端"""

    def __init__(self):
        self.config = get_merged_config()
        self.base_url = self.config.get("api_server", {}).get(
            "url", "http://localhost:8000"
        )
        self.token = self.config.get("api_server", {}).get("token")

        # API配置 - 将传递给服务端使用
        # 优先使用api配置，如果没有则尝试兼容旧的配置结构
        api_config = self.config.get("api", {})
        openai_config = self.config.get("openai", {})  # 兼容旧配置

        self.api_config = {
            "api_key": api_config.get("key") or openai_config.get("api_key"),
            "api_base_url": api_config.get("base_url")
            or openai_config.get("api_base_url"),
            "model_name": self.config.get("model", {}).get("name")
            or openai_config.get("model"),
        }

        self.headers = {
            "Content-Type": "application/json",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def _add_api_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """向请求数据中添加API配置"""
        return {**data, **self.api_config}

    def _make_request(
        self, method: str, endpoint: str, data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """统一的API请求方法"""
        url = f"{self.base_url.rstrip('/')}{endpoint}"

        # 添加API配置到请求数据
        if data:
            data = self._add_api_config(data)

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(
                    url, headers=self.headers, json=data, timeout=30
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return self._make_request("GET", ENDPOINTS["health"])

    def check_code_quality(
        self, diff: str, files: List[str] = None, check_types: List[str] = None
    ) -> Dict[str, Any]:
        """代码质量检查"""
        data = {
            "diff": diff,
            "files": files or [],
            "check_types": check_types or ["bugs", "security", "performance", "style"],
        }
        return self._make_request("POST", ENDPOINTS["code_quality"], data)

    def code_quality_check(self, diff: str) -> Dict[str, Any]:
        """代码质量检查 - 兼容旧接口"""
        return self.check_code_quality(diff)

    def ask_question(
        self, question: str, category: str = "general", context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """智能问答"""
        data = {"question": question, "category": category, "context": context or {}}
        return self._make_request("POST", ENDPOINTS["intelligent_qa"], data)

    def analyze_git_error(
        self, command: List[str], error_message: str
    ) -> Dict[str, Any]:
        """Git错误分析"""
        data = {"command": command, "error_message": error_message}
        return self._make_request("POST", ENDPOINTS["git_error"], data)

    def git_error_analysis(self, command: List[str], error_message: str) -> str:
        """Git错误分析 - 兼容旧接口，直接返回分析结果"""
        result = self.analyze_git_error(command, error_message)
        if "error" in result:
            return f"Error analyzing git error: {result['error']}"
        return result.get("analysis", "Unable to analyze git error")

    def generate_commit_message(
        self, diff: str, style: str = "conventional", context: Dict[str, Any] = None
    ) -> str:
        """生成提交消息"""
        # 清理diff内容，避免Unicode问题
        try:
            # 确保diff是有效的UTF-8字符串
            cleaned_diff = diff.encode("utf-8", errors="replace").decode("utf-8")
            # 移除或替换可能导致JSON问题的特殊字符
            import re

            # 移除控制字符
            cleaned_diff = re.sub(
                r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", cleaned_diff
            )
            # 移除可能导致JSON解析问题的反斜杠序列
            cleaned_diff = re.sub(r"\\x[0-9a-fA-F]{2}", "", cleaned_diff)
            cleaned_diff = re.sub(r"\\u[0-9a-fA-F]{4}", "", cleaned_diff)
            # 转义反斜杠
            cleaned_diff = cleaned_diff.replace("\\", "\\\\")
        except Exception as e:
            print(f"Warning: Could not clean diff: {e}")
            cleaned_diff = diff

        data = {"diff": cleaned_diff, "style": style, "context": context or {}}
        result = self._make_request("POST", ENDPOINTS["commit_message"], data)

        # 处理错误响应
        if "error" in result:
            return f"Error generating commit message: {result['error']}"

        # 提取消息内容
        message = result.get("message", "feat: update code")
        if not message:
            return "feat: update code"

        return message

    def analyze_push_strategy(
        self,
        diff: str,
        target_branch: str,
        current_branch: str,
        repository_type: str = "github",
    ) -> Dict[str, Any]:
        """推送策略分析"""
        data = {
            "diff": diff,
            "target_branch": target_branch,
            "current_branch": current_branch,
            "repository_type": repository_type,
        }
        return self._make_request("POST", ENDPOINTS["push_strategy"], data)

    def review_code(self, diff: str, check_type: str = "general") -> Dict[str, Any]:
        """代码审查"""
        data = {"diff": diff, "check_type": check_type}
        return self._make_request("POST", ENDPOINTS["code_review"], data)

    def commit_qa(
        self, question: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """提交相关问答"""
        data = {"question": question, "context": context or {}}
        return self._make_request("POST", ENDPOINTS["commit_qa"], data)

    def analyze_repository(
        self, repository_path: str = None, analysis_type: str = "overview"
    ) -> Dict[str, Any]:
        """仓库分析"""
        data = {"repository_path": repository_path, "analysis_type": analysis_type}
        return self._make_request("POST", ENDPOINTS["repository_analysis"], data)

    def create_commit_info(self, commit_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建新的Commit信息记录"""
        return self._make_request("POST", ENDPOINTS["commits"], commit_data)

    def mark_commit_as_committed(
        self, commit_id: int, commit_hash: str
    ) -> Dict[str, Any]:
        """标记Commit为已提交状态"""
        endpoint = f"{ENDPOINTS['commits']}/{commit_id}/commit"
        data = {"commit_hash": commit_hash}
        return self._make_request("POST", endpoint, data)


# 全局API客户端实例
api_client = NexCodeAPIClient()
