from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Boolean,
    ForeignKey,
    JSON,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base
from datetime import datetime


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100))  # 匹配数据库字段
    password_hash = Column(String(255))  # 匹配数据库字段名
    cas_user_id = Column(String(100), unique=True, index=True)  # 匹配数据库字段
    cas_attributes = Column(Text)  # JSON字段，匹配数据库
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)  # 匹配数据库字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 匹配数据库字段
    last_login = Column(DateTime)  # 匹配数据库字段
    
    # 关系 - 修复关系名称以匹配其他模型
    owned_documents = relationship("Document", foreign_keys="Document.owner_id", back_populates="owner")
    sessions = relationship("UserSession", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")
    document_versions = relationship("DocumentVersion", back_populates="user")
    commit_infos = relationship("CommitInfo", back_populates="user")
    collaborations = relationship("DocumentCollaborator", foreign_keys="DocumentCollaborator.user_id", back_populates="user")
    
    # 组织相关关系
    owned_organizations = relationship("Organization", foreign_keys="Organization.owner_id", back_populates="owner")
    organization_memberships = relationship("OrganizationMember", foreign_keys="OrganizationMember.user_id", back_populates="user")


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
    ai_generated_message = Column(Text, nullable=True)  # AI生成的commit信息
    final_commit_message = Column(Text, nullable=False)  # 最终使用的commit信息

    # 代码变更信息
    diff_content = Column(Text, nullable=True)  # Git diff内容
    files_changed = Column(JSON, nullable=True)  # 变更文件列表
    lines_added = Column(Integer, default=0)
    lines_deleted = Column(Integer, default=0)

    # AI相关信息
    ai_model_used = Column(String(50), nullable=True)  # 使用的AI模型
    ai_parameters = Column(JSON, nullable=True)  # AI调用参数
    generation_time_ms = Column(Integer, nullable=True)  # AI生成耗时(毫秒)

    # 用户选择和反馈
    user_rating = Column(Integer, nullable=True)  # 用户对AI生成内容的评分 1-5
    user_feedback = Column(Text, nullable=True)  # 用户反馈
    commit_style = Column(String(50), default="conventional")  # commit风格

    # 状态和标签
    status = Column(String(20), default="draft")  # draft, committed, failed
    tags = Column(JSON, nullable=True)  # 自定义标签

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    committed_at = Column(DateTime(timezone=True), nullable=True)  # 实际提交时间

    # 关系
    user = relationship("User", back_populates="commit_infos")


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
    last_activity = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 状态
    is_active = Column(Boolean, default=True)

    # 关系
    user = relationship("User", back_populates="sessions")


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

    # 关系
    user = relationship("User", back_populates="api_keys")


class SystemSettings(Base):
    """系统设置表"""

    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)

    # 基本系统设置
    site_name = Column(String(100), default="NexCode")
    site_description = Column(Text, nullable=True)
    admin_email = Column(String(100), nullable=True)
    max_file_size = Column(Integer, default=10485760)  # 10MB
    session_timeout = Column(Integer, default=1800)  # 30分钟

    # 用户注册和验证
    enable_registration = Column(Boolean, default=True)
    enable_email_verification = Column(Boolean, default=False)

    # SMTP邮件设置
    smtp_host = Column(String(100), nullable=True)
    smtp_port = Column(Integer, default=587)
    smtp_username = Column(String(100), nullable=True)
    smtp_password = Column(String(255), nullable=True)
    smtp_use_tls = Column(Boolean, default=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
class PermissionLevel(str, enum.Enum):
    """权限级别枚举"""

    OWNER = "owner"  # 所有者
    EDITOR = "editor"  # 编辑者
    READER = "reader"  # 查看者


class DocumentStatus(str, enum.Enum):
    """文档状态枚举"""

    ACTIVE = "active"
    DELETED = "deleted"
    ARCHIVED = "archived"


class OperationType(str, enum.Enum):
    """操作类型枚举"""

    INSERT = "insert"
    DELETE = "delete"
    RETAIN = "retain"


class Document(Base):
    """文档表"""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    last_editor_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 最后编辑者

    # 组织关联
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    # 文档属性
    category = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)  # 存储标签数组

    # 状态和时间
    status = Column(Enum(DocumentStatus), default=DocumentStatus.ACTIVE)
    version = Column(Integer, nullable=False)  # 版本号
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关系
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_documents")
    last_editor = relationship("User", foreign_keys=[last_editor_id])
    collaborators = relationship("DocumentCollaborator", back_populates="document")
    operations = relationship("DocumentOperation", back_populates="document")
    versions = relationship("DocumentVersion", back_populates="document")
    organization = relationship("Organization", back_populates="documents")


class DocumentCollaborator(Base):
    """文档协作者表"""

    __tablename__ = "document_collaborators"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission = Column(Enum(PermissionLevel), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    added_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 关系
    document = relationship("Document", back_populates="collaborators")
    user = relationship("User", foreign_keys=[user_id], back_populates="collaborations")
    added_by_user = relationship("User", foreign_keys=[added_by])


class DocumentOperation(Base):
    """文档操作记录表 - 用于OT算法"""

    __tablename__ = "document_operations"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    operation_id = Column(String(50), nullable=False)  # 客户端生成的操作ID
    sequence_number = Column(Integer, nullable=False)  # 操作序号

    # 操作类型和内容
    operation_type = Column(Enum(OperationType), nullable=False)
    start_position = Column(Integer, nullable=False)
    end_position = Column(Integer, nullable=False)
    content = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    document = relationship("Document", back_populates="operations")
    user = relationship("User")


class DocumentVersion(Base):
    """文档版本表"""

    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    content_hash = Column(String(32), nullable=False)  # 新增：内容哈希值
    change_description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 关系
    document = relationship("Document", back_populates="versions")
    user = relationship("User", back_populates="document_versions")


class Organization(Base):
    """组织表"""
    
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 组织设置
    is_public = Column(Boolean, default=False)  # 是否公开组织
    allow_member_invite = Column(Boolean, default=True)  # 是否允许成员邀请其他用户
    require_admin_approval = Column(Boolean, default=False)  # 是否需要管理员审批新成员
    
    # 状态和时间
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_organizations")
    members = relationship("OrganizationMember", back_populates="organization")
    documents = relationship("Document", back_populates="organization")


class OrganizationMember(Base):
    """组织成员表"""
    
    __tablename__ = "organization_members"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="member")  # owner, admin, member
    
    # 成员信息
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # 关系
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="organization_memberships")
    inviter = relationship("User", foreign_keys=[invited_by])



