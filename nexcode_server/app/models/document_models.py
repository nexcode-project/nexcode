from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class PermissionLevel(str, enum.Enum):
    """权限级别枚举"""
    OWNER = "owner"      # 所有者
    EDITOR = "editor"    # 编辑者
    READER = "reader"    # 查看者

class DocumentStatus(str, enum.Enum):
    """文档状态枚举"""
    ACTIVE = "active"
    DELETED = "deleted"
    ARCHIVED = "archived"

class Document(Base):
    """文档表"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 文档属性
    category = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)  # 存储标签数组
    
    # 状态和时间
    status = Column(Enum(DocumentStatus), default=DocumentStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_editor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 版本控制
    version = Column(Integer, default=1)
    
    # 关系
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_documents")
    last_editor = relationship("User", foreign_keys=[last_editor_id])
    collaborators = relationship("DocumentCollaborator", back_populates="document", cascade="all, delete-orphan")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")

class DocumentCollaborator(Base):
    """文档协作者表"""
    __tablename__ = "document_collaborators"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission = Column(Enum(PermissionLevel), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    added_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 关系
    document = relationship("Document", back_populates="collaborators")
    user = relationship("User", foreign_keys=[user_id])
    added_by_user = relationship("User", foreign_keys=[added_by])

class DocumentVersion(Base):
    """文档版本表"""
    __tablename__ = "document_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    
    # 变更信息
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    change_description = Column(String(500), nullable=True)
    changes_diff = Column(Text, nullable=True)  # 存储diff信息
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    document = relationship("Document", back_populates="versions")
    changed_by_user = relationship("User")