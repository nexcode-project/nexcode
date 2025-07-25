from typing import Dict, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_, or_, desc
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import hashlib
import logging

from app.models.database import (
    Document,
    DocumentCollaborator,
    DocumentVersion,
    PermissionLevel,
    DocumentStatus,
    User
)

logger = logging.getLogger(__name__)


class DocumentService:
    """文档服务"""
    
    def __init__(self, db=None):
        """初始化文档服务
        
        Args:
            db: 同步数据库会话（可选，用于同步操作）
        """
        self.db = db

    async def create_document(
        self,
        db: AsyncSession,
        user_id: int,
        title: str,
        content: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Document:
        """创建文档（仅元数据，内容存储在ShareDB）"""

        # 创建文档元数据记录
        document = Document(
            title=title,
            content="",  # 内容存储在ShareDB，这里只保存空字符串作为占位符
            category=category,
            tags=",".join(tags) if tags else None,
            owner_id=user_id,
            last_editor_id=user_id,
            version=0,  # ShareDB 管理版本
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        # 注意：不再在PostgreSQL中创建版本记录
        # 文档内容将在ShareDB中初始化

        return document

    async def get_document(
        self, db: AsyncSession, document_id: int, user_id: int, sharedb_service=None
    ) -> Dict[str, Any]:
        """获取文档详情（元数据来自PostgreSQL，内容来自ShareDB）"""

        stmt = (
            select(Document)
            .options(
                selectinload(Document.owner),
                selectinload(Document.collaborators).selectinload(
                    DocumentCollaborator.user
                ),
            )
            .where(Document.id == document_id)
        )

        result = await db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在"
            )

        # 检查权限
        if not await self._check_read_permission(db, document_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此文档"
            )

        # 从 ShareDB 获取最新内容
        content = ""
        version = 0
        if sharedb_service:
            try:
                sharedb_doc = await sharedb_service.get_document(str(document_id))
                content = sharedb_doc.get("content", "")
                version = sharedb_doc.get("version", 0)
                
                # 如果 ShareDB 中的内容为空且 PostgreSQL 中有内容，则同步
                if not content and document.content:
                    logger.info(f"ShareDB content is empty, syncing from PostgreSQL for document {document_id}")
                    await sharedb_service.sync_document(
                        doc_id=str(document_id),
                        version=document.version,
                        content=document.content,
                        user_id=user_id,
                        create_version=False
                    )
                    content = document.content
                    version = document.version
                    
            except Exception as e:
                logger.warning(f"Failed to get content from ShareDB: {e}")
                # 降级到 PostgreSQL 内容（如果有）
                content = document.content
                version = document.version

        return {
            "id": document.id,
            "title": document.title,
            "content": content,  # 来自 ShareDB
            "version": version,  # 来自 ShareDB
            "category": document.category,
            "tags": document.tags,
            "owner": document.owner,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
            "status": document.status,
        }

    async def update_document(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,  # 保留参数但不使用，内容由ShareDB管理
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        change_description: Optional[str] = None,
        create_version: bool = True,  # 版本控制由ShareDB管理，此参数已无效
    ) -> Document:
        """更新文档元数据（内容更新请使用ShareDB）"""

        # 检查权限
        if not await self._check_write_permission(db, document_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权限编辑此文档"
            )

        # 获取文档
        stmt = select(Document).where(Document.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在"
            )

        # 更新元数据字段
        if title is not None:
            document.title = title
        if category is not None:
            document.category = category
        if tags is not None:
            document.tags = ",".join(tags)
        
        document.last_editor_id = user_id
        document.updated_at = datetime.utcnow()
        # 注意：不更新 content 和 version，这些由 ShareDB 管理

        await db.commit()
        await db.refresh(document)

        return document

    async def delete_document(self, db: AsyncSession, document_id: int, user_id: int):
        """删除文档（软删除）"""

        # 检查权限（只有所有者可以删除）
        stmt = select(Document).where(Document.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在"
            )

        if document.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有文档所有者可以删除文档",
            )

        # 软删除
        document.status = DocumentStatus.DELETED
        await db.commit()

    async def list_documents(
        self,
        db: AsyncSession,
        user_id: int,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Document]:
        """获取文档列表"""

        # 构建查询
        stmt = (
            select(Document)
            .options(
                selectinload(Document.owner),
                selectinload(Document.collaborators).selectinload(
                    DocumentCollaborator.user
                ),
            )
            .where(
                and_(
                    Document.status == DocumentStatus.ACTIVE,
                    or_(
                        Document.owner_id == user_id,
                        Document.collaborators.any(
                            DocumentCollaborator.user_id == user_id
                        ),
                    ),
                )
            )
        )

        # 添加过滤条件
        if category:
            stmt = stmt.where(Document.category == category)

        if tags:
            for tag in tags:
                stmt = stmt.where(Document.tags.contains([tag]))

        if search:
            stmt = stmt.where(
                or_(
                    Document.title.ilike(f"%{search}%"),
                    Document.content.ilike(f"%{search}%"),
                )
            )

        # 排序和分页
        stmt = stmt.order_by(desc(Document.updated_at)).offset(skip).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_document_versions(
        self, db: AsyncSession, document_id: int, user_id: int
    ) -> List[DocumentVersion]:
        """获取文档版本历史"""

        # 检查权限
        if not await self._check_read_permission(db, document_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此文档"
            )

        stmt = (
            select(DocumentVersion)
            .options(selectinload(DocumentVersion.changed_by))
            .where(DocumentVersion.document_id == document_id)
            .order_by(desc(DocumentVersion.version_number))
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    async def revert_to_version(
        self, db: AsyncSession, document_id: int, version_number: int, user_id: int
    ) -> Document:
        """回滚到指定版本"""

        # 检查权限
        if not await self._check_write_permission(db, document_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权限编辑此文档"
            )

        # 获取指定版本
        stmt = select(DocumentVersion).where(
            and_(
                DocumentVersion.document_id == document_id,
                DocumentVersion.version_number == version_number,
            )
        )
        result = await db.execute(stmt)
        target_version = result.scalar_one_or_none()

        if not target_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="指定版本不存在"
            )

        # 获取文档
        stmt = select(Document).where(Document.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在"
            )

        # 回滚内容
        document.title = target_version.title
        document.content = target_version.content
        document.last_editor_id = user_id
        document.version += 1

        # 创建新版本记录
        content_hash = hashlib.md5(document.content.encode()).hexdigest()
        new_version = DocumentVersion(
            document_id=document_id,
            version_number=document.version,
            title=document.title,
            content=document.content,
            content_hash=content_hash,  # 添加内容哈希
            changed_by=user_id,
            change_description=f"回滚到版本 {version_number}",
        )

        db.add(new_version)
        await db.commit()
        await db.refresh(document)

        return document

    async def _check_read_permission(
        self, db: AsyncSession, document_id: int, user_id: int
    ) -> bool:
        """检查读取权限"""

        stmt = select(Document).where(Document.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            return False

        # 所有者有权限
        if document.owner_id == user_id:
            return True

        # 检查协作者权限
        stmt = select(DocumentCollaborator).where(
            and_(
                DocumentCollaborator.document_id == document_id,
                DocumentCollaborator.user_id == user_id,
            )
        )
        result = await db.execute(stmt)
        collaborator = result.scalar_one_or_none()

        return collaborator is not None

    async def _check_write_permission(
        self, db: AsyncSession, document_id: int, user_id: int
    ) -> bool:
        """检查写入权限"""

        stmt = select(Document).where(Document.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            return False

        # 所有者有权限
        if document.owner_id == user_id:
            return True

        # 检查协作者权限（需要编辑权限）
        stmt = select(DocumentCollaborator).where(
            and_(
                DocumentCollaborator.document_id == document_id,
                DocumentCollaborator.user_id == user_id,
                DocumentCollaborator.permission == PermissionLevel.EDITOR,
            )
        )
        result = await db.execute(stmt)
        collaborator = result.scalar_one_or_none()

        return collaborator is not None

    async def get_user_documents(
        self,
        db,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict:
        """获取用户的文档列表，带分页信息"""
        # 基础查询条件
        base_condition = or_(
            Document.owner_id == user_id,
            Document.id.in_(
                select(DocumentCollaborator.document_id).where(
                    DocumentCollaborator.user_id == user_id
                )
            ),
        )
        query = select(Document).where(base_condition)
        count_query = select(func.count()).select_from(Document).where(base_condition)

        # 搜索
        if search:
            query = query.where(Document.title.ilike(f"%{search}%"))
            count_query = count_query.where(Document.title.ilike(f"%{search}%"))
        # 分类
        if category:
            query = query.where(Document.category == category)
            count_query = count_query.where(Document.category == category)

        # 排序、分页
        query = query.order_by(Document.updated_at.desc()).offset(skip).limit(limit)

        # 查询总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询文档
        result = await db.execute(query)
        documents = result.scalars().all()

        return {"documents": documents, "total": total, "skip": skip, "limit": limit}

    def should_create_version(self, document_id: int, new_content: str, user_id: int) -> bool:
        """判断是否应该创建新版本"""
        # 获取文档的最新版本
        latest_version = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.version_number.desc()).first()
        
        if not latest_version:
            # 如果没有版本历史，创建第一个版本
            return True
        
        # 检查内容是否有变化
        content_hash = hashlib.md5(new_content.encode()).hexdigest()
        if content_hash == latest_version.content_hash:
            # 内容没有变化，不创建版本
            return False
        
        # 检查距离上次版本创建的时间
        time_since_last_version = datetime.utcnow() - latest_version.created_at
        if time_since_last_version < timedelta(minutes=1):
            # 距离上次版本创建不到1分钟，不创建版本
            return False
        
        return True
    
    def update_document_sync(self, document_id: int, content: str, title: str = None, 
                       category: str = None, tags: list = None, 
                       create_version: bool = True, user_id: int = None) -> Document:
        """更新文档，智能版本控制（同步版本）"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("Document not found")
        
        # 检查是否需要创建版本
        should_version = create_version and self.should_create_version(document_id, content, user_id)
        
        # 更新文档内容
        document.content = content
        if title:
            document.title = title
        if category:
            document.category = category
        if tags:
            document.tags = ",".join(tags) if isinstance(tags, list) else str(tags)
        document.updated_at = datetime.utcnow()
        
        # 只有在需要创建版本时才增加版本号
        if should_version:
            document.version += 1
            
            # 创建版本记录
            content_hash = hashlib.md5(content.encode()).hexdigest()
            version = DocumentVersion(
                document_id=document_id,
                version_number=document.version,
                title=document.title,
                content=content,
                content_hash=content_hash,
                changed_by=user_id,
                change_description=f"自动版本保存 - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
                created_at=datetime.utcnow()
            )
            self.db.add(version)
        
        self.db.commit()
        return document


# 创建服务实例
document_service = DocumentService()
