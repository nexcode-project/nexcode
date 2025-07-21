from typing import Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_, or_, desc
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.document_models import (
    Document,
    DocumentCollaborator,
    DocumentVersion,
    PermissionLevel,
    DocumentStatus,
)
from app.models.database import User


class DocumentService:
    """文档服务"""

    async def create_document(
        self,
        db: AsyncSession,
        user_id: int,
        title: str,
        content: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Document:
        """创建文档"""

        document = Document(
            title=title,
            content=content or "",
            owner_id=user_id,
            category=category,
            tags=tags or [],
            version=1,
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        # 创建初始版本记录
        version = DocumentVersion(
            document_id=document.id,
            version_number=1,
            title=title,
            content=content or "",
            changed_by=user_id,
            change_description="初始版本",
        )

        db.add(version)
        await db.commit()

        return document

    async def get_document(
        self, db: AsyncSession, document_id: int, user_id: int
    ) -> Document:
        """获取文档详情"""

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
                    Document.id == document_id, Document.status == DocumentStatus.ACTIVE
                )
            )
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

        return document

    async def update_document(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        change_description: Optional[str] = None,
    ) -> Document:
        """更新文档"""

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

        # 保存旧版本
        old_content = document.content
        old_title = document.title

        # 更新文档
        if title is not None:
            document.title = title
        if content is not None:
            document.content = content
        if category is not None:
            document.category = category
        if tags is not None:
            document.tags = tags

        document.last_editor_id = user_id
        document.version += 1

        # 创建版本记录
        version = DocumentVersion(
            document_id=document_id,
            version_number=document.version,
            title=document.title,
            content=document.content,
            changed_by=user_id,
            change_description=change_description or "文档更新",
        )

        db.add(version)
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
        new_version = DocumentVersion(
            document_id=document_id,
            version_number=document.version,
            title=document.title,
            content=document.content,
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


# 创建服务实例
document_service = DocumentService()
