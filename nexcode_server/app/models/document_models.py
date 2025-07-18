from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    JSON,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_editor_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 版本控制
    version = Column(Integer, default=1)

    # 关系
    owner = relationship(
        "User", foreign_keys=[owner_id], back_populates="owned_documents"
    )
    last_editor = relationship("User", foreign_keys=[last_editor_id])
    collaborators = relationship(
        "DocumentCollaborator", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentCollaborator(Base):
    """文档协作者表"""

    __tablename__ = "document_collaborators"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission = Column(Enum(PermissionLevel), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    added_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 关系 - 明确指定外键
    document = relationship("Document", back_populates="collaborators")
    user = relationship(
        "User", foreign_keys=[user_id], back_populates="collaborated_documents"
    )
    added_by_user = relationship("User", foreign_keys=[added_by])


class DocumentVersion(Base):
    """文档版本表"""

    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    change_description = Column(String(500), nullable=True)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    document = relationship("Document")
    changed_by_user = relationship("User", foreign_keys=[changed_by])
