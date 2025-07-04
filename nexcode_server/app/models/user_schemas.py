from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# 用户相关模型
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
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
class APIKeyCreate(BaseModel):
    key_name: str = Field(..., min_length=1, max_length=100)
    scopes: Optional[List[str]] = None
    rate_limit: Optional[int] = Field(1000, ge=1, le=10000)
    expires_at: Optional[datetime] = None

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
    
class CommitTrends(BaseModel):
    date: str
    commit_count: int
    avg_generation_time: Optional[float] = None
    
class CommitAnalytics(BaseModel):
    user_stats: UserCommitStats
    recent_trends: List[CommitTrends]
    top_repositories: List[Dict[str, Any]] 