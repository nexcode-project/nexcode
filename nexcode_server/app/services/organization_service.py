from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from fastapi import HTTPException, status

from app.models.database import (
    Organization, OrganizationMember, 
    User, Document, DocumentCollaborator, PermissionLevel
)


class OrganizationService:
    """组织管理服务"""
    
    @staticmethod
    async def create_organization(
        db: AsyncSession,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        avatar_url: Optional[str] = None,
        is_public: bool = False,
        allow_member_invite: bool = True,
        require_admin_approval: bool = False
    ) -> Organization:
        """创建组织"""
        
        # 检查组织名称是否已存在
        stmt = select(Organization).where(
            and_(
                Organization.name == name,
                Organization.is_active == True
            )
        )
        result = await db.execute(stmt)
        existing_org = result.scalar_one_or_none()
        
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="组织名称已存在"
            )
        
        # 创建组织
        organization = Organization(
            name=name,
            description=description,
            avatar_url=avatar_url,
            owner_id=user_id,
            is_public=is_public,
            allow_member_invite=allow_member_invite,
            require_admin_approval=require_admin_approval
        )
        
        db.add(organization)
        await db.commit()
        await db.refresh(organization)
        
        # 自动将创建者添加为组织成员（owner角色）
        member = OrganizationMember(
            organization_id=organization.id,
            user_id=user_id,
            role="owner"
        )
        
        db.add(member)
        await db.commit()
        
        return organization
    
    @staticmethod
    async def get_user_organizations(
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Organization]:
        """获取用户所属的组织列表"""
        
        stmt = select(Organization).join(OrganizationMember).where(
            and_(
                OrganizationMember.user_id == user_id,
                OrganizationMember.is_active == True,
                Organization.is_active == True
            )
        ).offset(skip).limit(limit).order_by(Organization.created_at.desc())
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_organization_by_id(
        db: AsyncSession,
        organization_id: int
    ) -> Optional[Organization]:
        """根据ID获取组织信息"""
        
        stmt = select(Organization).where(
            and_(
                Organization.id == organization_id,
                Organization.is_active == True
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
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
    async def add_organization_member(
        db: AsyncSession,
        organization_id: int,
        inviter_id: int,
        user_email: str,
        role: str = "member"
    ) -> OrganizationMember:
        """添加组织成员"""
        
        # 检查邀请者权限
        has_permission = await OrganizationService.check_organization_permission(
            db, inviter_id, organization_id, "admin"
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，无法添加成员"
            )
        
        # 查找用户
        stmt = select(User).where(User.email == user_email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 检查用户是否已是组织成员
        stmt = select(OrganizationMember).where(
            and_(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user.id,
                OrganizationMember.is_active == True
            )
        )
        result = await db.execute(stmt)
        existing_member = result.scalar_one_or_none()
        
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户已是组织成员"
            )
        
        # 创建成员记录
        member = OrganizationMember(
            organization_id=organization_id,
            user_id=user.id,
            role=role,
            invited_by=inviter_id
        )
        
        db.add(member)
        await db.commit()
        await db.refresh(member)
        
        return member
    
    @staticmethod
    async def get_organization_members(
        db: AsyncSession,
        organization_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取组织成员列表"""
        
        stmt = select(
            OrganizationMember,
            User.username,
            User.email,
            User.full_name
        ).join(User).where(
            and_(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.is_active == True
            )
        ).offset(skip).limit(limit).order_by(OrganizationMember.joined_at.desc())
        
        result = await db.execute(stmt)
        members = []
        
        for row in result.all():
            member, username, email, full_name = row
            members.append({
                "id": member.id,
                "user_id": member.user_id,
                "username": username,
                "email": email,
                "full_name": full_name,
                "role": member.role,
                "joined_at": member.joined_at,
                "invited_by": member.invited_by
            })
        
        return members
    
    @staticmethod
    async def update_member_role(
        db: AsyncSession,
        organization_id: int,
        operator_id: int,
        member_id: int,
        new_role: str
    ) -> OrganizationMember:
        """更新成员角色"""
        
        # 检查操作者权限
        has_permission = await OrganizationService.check_organization_permission(
            db, operator_id, organization_id, "admin"
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，无法修改成员角色"
            )
        
        # 获取成员记录
        stmt = select(OrganizationMember).where(
            and_(
                OrganizationMember.id == member_id,
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.is_active == True
            )
        )
        result = await db.execute(stmt)
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="成员不存在"
            )
        
        # 更新角色
        member.role = new_role
        await db.commit()
        await db.refresh(member)
        
        return member
    
    @staticmethod
    async def remove_organization_member(
        db: AsyncSession,
        organization_id: int,
        operator_id: int,
        member_id: int
    ) -> bool:
        """移除组织成员"""
        
        # 检查操作者权限
        has_permission = await OrganizationService.check_organization_permission(
            db, operator_id, organization_id, "admin"
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，无法移除成员"
            )
        
        # 获取成员记录
        stmt = select(OrganizationMember).where(
            and_(
                OrganizationMember.id == member_id,
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.is_active == True
            )
        )
        result = await db.execute(stmt)
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="成员不存在"
            )
        
        # 软删除成员
        member.is_active = False
        await db.commit()
        
        return True


# 创建服务实例
organization_service = OrganizationService() 