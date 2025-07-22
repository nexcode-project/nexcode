from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PermissionLevel(str, Enum):
    """权限级别枚举"""

    OWNER = "owner"
    EDITOR = "editor"
    READER = "reader"


class DocumentStatus(str, Enum):
    """文档状态枚举"""

    ACTIVE = "active"
    DELETED = "deleted"
    ARCHIVED = "archived"


class DocumentCreate(BaseModel):
    """创建文档请求"""

    title: str = Field(..., min_length=1, max_length=200)
    content: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None


class DocumentUpdate(BaseModel):
    """更新文档请求"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    change_description: Optional[str] = Field(None, max_length=500)


class UserInfo(BaseModel):
    """用户信息"""

    id: int
    username: str
    email: Optional[str] = None


class CollaboratorResponse(BaseModel):
    """协作者响应"""

    id: int
    user: UserInfo
    permission: PermissionLevel
    added_at: datetime


class DocumentResponse(BaseModel):
    """文档响应"""

    id: int
    title: str
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: DocumentStatus
    version: int
    created_at: datetime
    updated_at: datetime

    owner: UserInfo
    collaborators: List[CollaboratorResponse] = []

    # 当前用户权限
    user_permission: Optional[PermissionLevel] = None

    class Config:
        from_attributes = True


class DocumentListItem(BaseModel):
    """文档列表项"""

    id: int
    title: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: DocumentStatus
    version: int
    created_at: datetime
    updated_at: datetime
    owner: UserInfo
    user_permission: Optional[PermissionLevel] = None


class DocumentListResponse(BaseModel):
    """文档列表响应"""

    documents: List[DocumentListItem]
    total: int
    page: int
    size: int


class DocumentListResult(BaseModel):
    """文档列表结果"""

    documents: List[DocumentListItem]
    total: int
    skip: int
    limit: int


class DocumentVersionResponse(BaseModel):
    """文档版本响应"""

    id: int
    version_number: int
    title: str
    content: Optional[str] = None
    change_description: Optional[str] = None
    created_at: datetime
    changed_by: UserInfo


class CollaboratorAdd(BaseModel):
    """添加协作者请求"""

    user_email: str = Field(..., min_length=1)
    permission: PermissionLevel


class CollaboratorUpdate(BaseModel):
    """更新协作者权限请求"""

    permission: PermissionLevel


class DocumentSearchQuery(BaseModel):
    """文档搜索查询"""

    search: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
