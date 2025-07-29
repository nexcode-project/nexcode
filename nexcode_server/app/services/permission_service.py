from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from fastapi import HTTPException, status

from app.models.database import Document, DocumentCollaborator, PermissionLevel, Organization, OrganizationMember
from app.models.database import User

class PermissionService:
    """权限管理服务"""
    
    @staticmethod
    async def check_document_permission(
        db: AsyncSession,
        user_id: int,
        document_id: int,
        required_permission: PermissionLevel
    ) -> bool:
        """检查用户对文档的权限"""
        
        # 获取文档信息
        stmt = select(Document).where(Document.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 检查是否为文档所有者
        if document.owner_id == user_id:
            return True
        
        # 检查协作者权限
        stmt = select(DocumentCollaborator).where(
            and_(
                DocumentCollaborator.document_id == document_id,
                DocumentCollaborator.user_id == user_id
            )
        )
        result = await db.execute(stmt)
        collaborator = result.scalar_one_or_none()
        
        if not collaborator:
            return False
        
        # 权限级别检查
        permission_hierarchy = {
            PermissionLevel.READER: 1,
            PermissionLevel.EDITOR: 2,
            PermissionLevel.OWNER: 3
        }
        
        user_permission_level = permission_hierarchy.get(collaborator.permission, 0)
        required_permission_level = permission_hierarchy.get(required_permission, 0)
        
        return user_permission_level >= required_permission_level
    
    @staticmethod
    async def check_organization_permission(
        db: AsyncSession,
        user_id: int,
        organization_id: int,
        required_role: str = "member"
    ) -> bool:
        """检查用户对组织的权限"""
        
        stmt = select(OrganizationMember).where(
            and_(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id,
                OrganizationMember.is_active == True
            )
        )
        result = await db.execute(stmt)
        member = result.scalar_one_or_none()
        
        if not member:
            return False
        
        # 角色权限检查
        role_hierarchy = {
            "member": 1,
            "admin": 2,
            "owner": 3
        }
        
        user_role_level = role_hierarchy.get(member.role, 0)
        required_role_level = role_hierarchy.get(required_role, 0)
        
        return user_role_level >= required_role_level
    
    @staticmethod
    async def get_user_documents(
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        category: Optional[str] = None,
        organization_id: Optional[int] = None
    ) -> List[Document]:
        """获取用户有权限访问的文档列表"""
        
        # 构建查询条件
        conditions = [
            Document.status == "active",
            or_(
                Document.owner_id == user_id,
                Document.id.in_(
                    select(DocumentCollaborator.document_id).where(
                        DocumentCollaborator.user_id == user_id
                    )
                )
            )
        ]
        
        # 如果指定了组织，检查用户是否有权限访问该组织的文档
        if organization_id:
            has_org_permission = await PermissionService.check_organization_permission(
                db, user_id, organization_id, "member"
            )
            if has_org_permission:
                # 添加组织文档条件
                conditions.append(
                    or_(
                        Document.organization_id == organization_id,
                        Document.owner_id == user_id,
                        Document.id.in_(
                            select(DocumentCollaborator.document_id).where(
                                DocumentCollaborator.user_id == user_id
                            )
                        )
                    )
                )
            else:
                # 如果没有组织权限，只返回用户自己的文档
                conditions.append(Document.owner_id == user_id)
        
        if search:
            search_condition = or_(
                Document.title.contains(search),
                Document.content.contains(search)
            )
            conditions.append(search_condition)
        
        if category:
            conditions.append(Document.category == category)
        
        stmt = select(Document).where(and_(*conditions)).offset(skip).limit(limit).order_by(Document.updated_at.desc())
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def add_collaborator(
        db: AsyncSession,
        document_id: int,
        user_id: int,
        collaborator_user_id: int,
        permission: PermissionLevel
    ) -> DocumentCollaborator:
        """添加协作者"""
        
        # 检查操作者权限（只有所有者可以添加协作者）
        has_permission = await PermissionService.check_document_permission(
            db, user_id, document_id, PermissionLevel.OWNER
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有文档所有者可以添加协作者"
            )
        
        # 检查协作者是否已存在
        stmt = select(DocumentCollaborator).where(
            and_(
                DocumentCollaborator.document_id == document_id,
                DocumentCollaborator.user_id == collaborator_user_id
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户已是该文档的协作者"
            )
        
        # 创建协作者记录
        collaborator = DocumentCollaborator(
            document_id=document_id,
            user_id=collaborator_user_id,
            permission=permission,
            added_by=user_id
        )
        
        db.add(collaborator)
        await db.commit()
        await db.refresh(collaborator)
        
        return collaborator
    
    @staticmethod
    async def update_collaborator_permission(
        db: AsyncSession,
        document_id: int,
        user_id: int,
        collaborator_user_id: int,
        new_permission: PermissionLevel
    ) -> DocumentCollaborator:
        """更新协作者权限"""
        
        # 检查操作者权限
        has_permission = await PermissionService.check_document_permission(
            db, user_id, document_id, PermissionLevel.OWNER
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有文档所有者可以修改协作者权限"
            )
        
        # 获取协作者记录
        stmt = select(DocumentCollaborator).where(
            and_(
                DocumentCollaborator.document_id == document_id,
                DocumentCollaborator.user_id == collaborator_user_id
            )
        )
        result = await db.execute(stmt)
        collaborator = result.scalar_one_or_none()
        
        if not collaborator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="协作者不存在"
            )
        
        # 更新权限
        collaborator.permission = new_permission
        await db.commit()
        await db.refresh(collaborator)
        
        return collaborator
    
    @staticmethod
    async def remove_collaborator(
        db: AsyncSession,
        document_id: int,
        user_id: int,
        collaborator_user_id: int
    ) -> bool:
        """移除协作者"""
        
        # 检查操作者权限
        has_permission = await PermissionService.check_document_permission(
            db, user_id, document_id, PermissionLevel.OWNER
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有文档所有者可以移除协作者"
            )
        
        # 获取协作者记录
        stmt = select(DocumentCollaborator).where(
            and_(
                DocumentCollaborator.document_id == document_id,
                DocumentCollaborator.user_id == collaborator_user_id
            )
        )
        result = await db.execute(stmt)
        collaborator = result.scalar_one_or_none()
        
        if not collaborator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="协作者不存在"
            )
        
        # 删除协作者记录
        await db.delete(collaborator)
        await db.commit()
        
        return True
    
    @staticmethod
    async def get_document_collaborators(
        db: AsyncSession,
        document_id: int,
        user_id: int
    ) -> List[DocumentCollaborator]:
        """获取文档协作者列表"""
        
        # 检查用户是否有权限查看协作者列表
        has_permission = await PermissionService.check_document_permission(
            db, user_id, document_id, PermissionLevel.READER
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看协作者列表"
            )
        
        stmt = select(DocumentCollaborator).where(
            DocumentCollaborator.document_id == document_id
        ).order_by(DocumentCollaborator.added_at.desc())
        
        result = await db.execute(stmt)
        return result.scalars().all()

permission_service = PermissionService()