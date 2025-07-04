from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    
    # CAS相关字段
    cas_user_id = Column(String(100), unique=True, index=True, nullable=True)
    cas_attributes = Column(JSON, nullable=True)  # 存储CAS返回的用户属性
    
    # 用户状态
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    commits = relationship("CommitInfo", back_populates="user")

class CommitInfo(Base):
    """Commit信息表"""
    __tablename__ = "commit_info"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Git相关信息
    repository_url = Column(String(500), nullable=True)
    repository_name = Column(String(200), nullable=True)
    branch_name = Column(String(100), nullable=True)
    commit_hash = Column(String(40), nullable=True)  # Git commit hash
    
    # Commit信息
    user_selected_message = Column(Text, nullable=True)  # 用户选择的commit信息
    ai_generated_message = Column(Text, nullable=True)   # AI生成的commit信息
    final_commit_message = Column(Text, nullable=False)  # 最终使用的commit信息
    
    # 代码变更信息
    diff_content = Column(Text, nullable=True)  # Git diff内容
    files_changed = Column(JSON, nullable=True)  # 变更文件列表
    lines_added = Column(Integer, default=0)
    lines_deleted = Column(Integer, default=0)
    
    # AI相关信息
    ai_model_used = Column(String(50), nullable=True)  # 使用的AI模型
    ai_parameters = Column(JSON, nullable=True)        # AI调用参数
    generation_time_ms = Column(Integer, nullable=True)  # AI生成耗时(毫秒)
    
    # 用户选择和反馈
    user_rating = Column(Integer, nullable=True)  # 用户对AI生成内容的评分 1-5
    user_feedback = Column(Text, nullable=True)   # 用户反馈
    commit_style = Column(String(50), default="conventional")  # commit风格
    
    # 状态和标签
    status = Column(String(20), default="draft")  # draft, committed, failed
    tags = Column(JSON, nullable=True)  # 自定义标签
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    committed_at = Column(DateTime(timezone=True), nullable=True)  # 实际提交时间
    
    # 关系
    user = relationship("User", back_populates="commits")

class UserSession(Base):
    """用户会话表"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    cas_ticket = Column(String(255), nullable=True)  # CAS ticket
    
    # 会话信息
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 状态
    is_active = Column(Boolean, default=True)

class APIKey(Base):
    """API密钥表"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # API Key信息
    key_name = Column(String(100), nullable=False)  # 密钥名称
    key_hash = Column(String(255), nullable=False)  # 密钥哈希
    key_prefix = Column(String(20), nullable=False)  # 密钥前缀（用于显示）
    
    # 权限和限制
    scopes = Column(JSON, nullable=True)  # 权限范围
    rate_limit = Column(Integer, default=1000)  # 速率限制（每小时）
    
    # 使用统计
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # 可选的过期时间 