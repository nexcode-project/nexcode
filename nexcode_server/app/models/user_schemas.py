from pydantic import BaseModel, EmailStr, Field, field_validator, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import re
from enum import Enum

# 用户相关模型
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    username: str = Field(..., min_length=3, max_length=50)
    email: str  # Changed from EmailStr to str to allow .local domains
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        # Basic email pattern that allows .local and other development domains
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$|^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.local$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v
    
    class Config:
        from_attributes = True

class UserCASLogin(BaseModel):
    cas_ticket: str
    service_url: str

class UserProfile(UserResponse):
    cas_user_id: Optional[str] = None
    cas_attributes: Optional[Dict[str, Any]] = None

# Commit信息相关模型
class CommitInfoBase(BaseModel):
    repository_url: Optional[str] = None
    repository_name: Optional[str] = None
    branch_name: Optional[str] = None
    commit_hash: Optional[str] = None
    
    user_selected_message: Optional[str] = None
    ai_generated_message: Optional[str] = None
    final_commit_message: str
    
    diff_content: Optional[str] = None
    files_changed: Optional[List[str]] = None
    lines_added: Optional[int] = 0
    lines_deleted: Optional[int] = 0
    
    ai_model_used: Optional[str] = None
    ai_parameters: Optional[Dict[str, Any]] = None
    generation_time_ms: Optional[int] = None
    
    commit_style: str = "conventional"
    tags: Optional[List[str]] = None
    status: Optional[str] = "draft"

class CommitInfoCreate(CommitInfoBase):
    pass

class CommitInfoUpdate(BaseModel):
    user_selected_message: Optional[str] = None
    final_commit_message: Optional[str] = None
    commit_hash: Optional[str] = None
    status: Optional[str] = None
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    user_feedback: Optional[str] = None
    committed_at: Optional[datetime] = None

class CommitInfoResponse(CommitInfoBase):
    id: int
    user_id: int
    status: str
    user_rating: Optional[int] = None
    user_feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    committed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class CommitInfoWithUser(CommitInfoResponse):
    user: UserResponse

# API Key相关模型
class TokenScope(str, Enum):
    """API Token权限范围枚举 - 参考GitHub模式"""
    # 用户权限
    USER_READ = "user:read"           # 读取用户信息
    USER_WRITE = "user:write"         # 修改用户信息
    
    # 仓库权限  
    REPO_READ = "repo:read"           # 读取仓库信息
    REPO_WRITE = "repo:write"         # 修改仓库内容
    
    # API权限
    API_READ = "api:read"             # 调用读取API
    API_WRITE = "api:write"           # 调用写入API
    
    # 管理权限
    ADMIN = "admin"                   # 管理员权限
    
    @classmethod
    def get_default_scopes(cls) -> List[str]:
        """获取默认权限范围"""
        return [cls.USER_READ, cls.REPO_READ, cls.API_READ, cls.API_WRITE]
    
    @classmethod  
    def get_all_scopes(cls) -> List[str]:
        """获取所有权限范围"""
        return [scope.value for scope in cls]


class APIKeyCreate(BaseModel):
    key_name: str = Field(..., min_length=1, max_length=100, description="API密钥名称")
    scopes: Optional[List[str]] = Field(default_factory=TokenScope.get_default_scopes, description="权限范围")
    rate_limit: Optional[int] = Field(1000, ge=1, le=10000, description="每小时速率限制")
    expires_at: Optional[datetime] = Field(None, description="过期时间（可选）")
    
    @validator('scopes')
    def validate_scopes(cls, v):
        if v:
            valid_scopes = TokenScope.get_all_scopes()
            invalid = [scope for scope in v if scope not in valid_scopes]
            if invalid:
                raise ValueError(f"无效的权限范围: {invalid}")
        return v

class APIKeyResponse(BaseModel):
    id: int
    key_name: str
    key_prefix: str
    scopes: Optional[List[str]] = None
    rate_limit: int
    usage_count: int
    last_used: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class APIKeyWithToken(APIKeyResponse):
    """只在创建时返回完整的token"""
    token: str

# 认证相关模型
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None

# 用户会话模型
class UserSessionResponse(BaseModel):
    id: int
    session_token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

# 统计和分析模型
class UserCommitStats(BaseModel):
    total_commits: int
    commits_this_month: int
    avg_rating: Optional[float] = None
    most_used_style: str
    total_lines_added: int
    total_lines_deleted: int

# 系统设置模型
class SystemSettingsBase(BaseModel):
    site_name: str = Field(..., min_length=1, max_length=100)
    site_description: Optional[str] = None
    admin_email: Optional[EmailStr] = None
    max_file_size: int = Field(10485760, ge=1024, le=104857600)  # 1KB to 100MB
    session_timeout: int = Field(1800, ge=300, le=86400)  # 5min to 24h
    enable_registration: bool = True
    enable_email_verification: bool = False
    smtp_host: Optional[str] = None
    smtp_port: int = Field(587, ge=1, le=65535)
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True

class SystemSettingsCreate(SystemSettingsBase):
    pass

class SystemSettingsUpdate(BaseModel):
    site_name: Optional[str] = Field(None, min_length=1, max_length=100)
    site_description: Optional[str] = None
    admin_email: Optional[EmailStr] = None
    max_file_size: Optional[int] = Field(None, ge=1024, le=104857600)
    session_timeout: Optional[int] = Field(None, ge=300, le=86400)
    enable_registration: Optional[bool] = None
    enable_email_verification: Optional[bool] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = Field(None, ge=1, le=65535)
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: Optional[bool] = None

class SystemSettingsResponse(SystemSettingsBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CommitTrends(BaseModel):
    date: str
    commit_count: int
    avg_generation_time: Optional[float] = None
    
class CommitAnalytics(BaseModel):
    user_stats: UserCommitStats
    recent_trends: List[CommitTrends]
    top_repositories: List[Dict[str, Any]] 