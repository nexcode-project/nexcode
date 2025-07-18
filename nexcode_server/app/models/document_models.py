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

    # 文档属性
    category = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)  # 存储标签数组

    # 状态和时间
    status = Column(Enum(DocumentStatus), default=DocumentStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关系
    owner = relationship("User", back_populates="owned_documents")
    collaborators = relationship("DocumentCollaborator", back_populates="document")
    operations = relationship("DocumentOperation", back_populates="document")


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
    user = relationship("User", foreign_keys=[user_id])
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
    change_description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 关系
    document = relationship("Document")
    user = relationship("User")
