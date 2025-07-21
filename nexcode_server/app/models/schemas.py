from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any


# 基础API配置模型 - CLI传递给服务端使用
class APIConfigMixin(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    api_key: Optional[str] = None  # CLI传递的API密钥，服务端复用
    api_base_url: Optional[str] = None  # CLI传递的API基础URL
    model_name: Optional[str] = None  # CLI传递的模型名称


# Git错误分析
class GitErrorRequest(APIConfigMixin):
    command: List[str]
    error_message: str


class GitErrorResponse(BaseModel):
    solution: str


# 代码审查
class CodeReviewRequest(APIConfigMixin):
    diff: str
    check_type: Optional[str] = "general"  # general, security, performance, style


class CodeReviewResponse(BaseModel):
    analysis: str
    issues: List[Dict[str, Any]] = []
    suggestions: List[str] = []
    severity: str = "info"  # info, warning, error


# 提交消息生成
class CommitMessageRequest(APIConfigMixin):
    diff: str
    style: Optional[str] = "conventional"  # 提交消息风格
    context: Optional[Dict[str, Any]] = {}  # 额外上下文


class CommitMessageResponse(BaseModel):
    message: str


# 提交相关问答
class CommitQARequest(APIConfigMixin):
    question: str
    context: Optional[Dict[str, Any]] = {}  # Git仓库上下文


class CommitQAResponse(BaseModel):
    answer: str


# 代码质量检查（专门为check命令）
class CodeQualityRequest(APIConfigMixin):
    diff: str
    files: Optional[List[str]] = []
    check_types: List[str] = ["bugs", "security", "performance", "style"]


class CodeQualityResponse(BaseModel):
    overall_score: float
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    summary: str


# 推送策略分析
class PushStrategyRequest(APIConfigMixin):
    diff: str
    target_branch: str
    repository_type: Optional[str] = "github"
    current_branch: str


class PushStrategyResponse(BaseModel):
    commit_message: str
    push_command: str
    pre_push_checks: List[str]
    warnings: List[str] = []


# 仓库分析
class RepositoryAnalysisRequest(APIConfigMixin):
    repository_path: Optional[str] = None
    analysis_type: str = "overview"  # overview, structure, dependencies


class RepositoryAnalysisResponse(BaseModel):
    analysis: str
    structure: Dict[str, Any] = {}
    recommendations: List[str] = []


# 智能问答（增强版）
class IntelligentQARequest(APIConfigMixin):
    question: str
    category: Optional[str] = "general"  # git, code, workflow, best_practices
    context: Optional[Dict[str, Any]] = {}


class IntelligentQAResponse(BaseModel):
    answer: str
    related_topics: List[str] = []
    suggested_actions: List[str] = []


# 服务健康检查
class HealthCheckResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, str]
    timestamp: str
