"""
API端点定义模块
统一管理所有后端服务的API接口路径
"""

# API版本前缀
API_VERSION = "/v1"

# API端点路径常量字典
ENDPOINTS = {
    # Git错误分析
    'git_error': f"{API_VERSION}/git-error-analysis",
    
    # 代码审查（基础）
    'code_review': f"{API_VERSION}/code-review",
    
    # 代码质量检查（专门为check命令）
    'code_quality': f"{API_VERSION}/code-quality-check",
    
    # 提交消息生成
    'commit_message': f"{API_VERSION}/commit-message",
    
    # 提交相关问答（基础）
    'commit_qa': f"{API_VERSION}/commit-qa",
    
    # 智能问答（增强版，专门为ask命令）
    'intelligent_qa': f"{API_VERSION}/intelligent-qa",
    
    # 推送策略（专门为push命令）
    'push_strategy': f"{API_VERSION}/push-strategy",
    
    # 仓库分析
    'repository_analysis': f"{API_VERSION}/repository-analysis",
    
    # 健康检查
    'health': "/health",
    
    # 文档
    'docs': "/docs",
    'redoc': "/redoc"
}

# 向后兼容的APIEndpoints类
class APIEndpoints:
    """API端点路径常量（向后兼容）"""
    
    # Git错误分析
    GIT_ERROR = ENDPOINTS['git_error']
    
    # 代码审查（基础）
    CODE_REVIEW = ENDPOINTS['code_review']
    
    # 代码质量检查（专门为check命令）
    CODE_QUALITY = ENDPOINTS['code_quality']
    
    # 提交消息生成
    COMMIT_MESSAGE = ENDPOINTS['commit_message']
    
    # 提交相关问答（基础）
    COMMIT_QA = ENDPOINTS['commit_qa']
    
    # 智能问答（增强版，专门为ask命令）
    INTELLIGENT_QA = ENDPOINTS['intelligent_qa']
    
    # 推送策略（专门为push命令）
    PUSH_STRATEGY = ENDPOINTS['push_strategy']
    
    # 仓库分析
    REPOSITORY_ANALYSIS = ENDPOINTS['repository_analysis']
    
    # 健康检查
    HEALTH = ENDPOINTS['health']
    
    # 文档
    DOCS = ENDPOINTS['docs']
    REDOC = ENDPOINTS['redoc']

    @classmethod
    def get_all_endpoints(cls):
        """获取所有端点列表"""
        return list(ENDPOINTS.values())

    @classmethod
    def get_service_endpoints(cls):
        """获取业务服务端点（不包括文档和健康检查）"""
        return [
            ENDPOINTS['git_error'],
            ENDPOINTS['code_review'], 
            ENDPOINTS['code_quality'],
            ENDPOINTS['commit_message'],
            ENDPOINTS['commit_qa'],
            ENDPOINTS['intelligent_qa'],
            ENDPOINTS['push_strategy'],
            ENDPOINTS['repository_analysis']
        ] 