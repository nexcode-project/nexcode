from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.database import User
from app.services.organization_service import organization_service
from app.models.schemas import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationMemberResponse,
    OrganizationMemberCreate,
    OrganizationMemberUpdate
)

router = APIRouter()


@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    organization_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建组织"""
    organization = await organization_service.create_organization(
        db=db,
        user_id=current_user.id,
        name=organization_data.name,
        description=organization_data.description,
        avatar_url=organization_data.avatar_url,
        is_public=organization_data.is_public,
        allow_member_invite=organization_data.allow_member_invite,
        require_admin_approval=organization_data.require_admin_approval
    )
    
    return OrganizationResponse(
        id=organization.id,
        name=organization.name,
        description=organization.description,
        avatar_url=organization.avatar_url,
        owner_id=organization.owner_id,
        is_public=organization.is_public,
        allow_member_invite=organization.allow_member_invite,
        require_admin_approval=organization.require_admin_approval,
        is_active=organization.is_active,
        created_at=organization.created_at,
        updated_at=organization.updated_at
    )


@router.get("/", response_model=List[OrganizationResponse])
async def get_user_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户所属的组织列表"""
    organizations = await organization_service.get_user_organizations(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    return [
        OrganizationResponse(
            id=org.id,
            name=org.name,
            description=org.description,
            avatar_url=org.avatar_url,
            owner_id=org.owner_id,
            is_public=org.is_public,
            allow_member_invite=org.allow_member_invite,
            require_admin_approval=org.require_admin_approval,
            is_active=org.is_active,
            created_at=org.created_at,
            updated_at=org.updated_at
        )
        for org in organizations
    ]


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取组织详情"""
    # 检查用户是否有权限查看组织
    has_permission = await organization_service.check_organization_permission(
        db, current_user.id, organization_id, "member"
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，无法查看组织"
        )
    
    organization = await organization_service.get_organization_by_id(db, organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组织不存在"
        )
    
    return OrganizationResponse(
        id=organization.id,
        name=organization.name,
        description=organization.description,
        avatar_url=organization.avatar_url,
        owner_id=organization.owner_id,
        is_public=organization.is_public,
        allow_member_invite=organization.allow_member_invite,
        require_admin_approval=organization.require_admin_approval,
        is_active=organization.is_active,
        created_at=organization.created_at,
        updated_at=organization.updated_at
    )


@router.post("/{organization_id}/members", response_model=OrganizationMemberResponse)
async def add_organization_member(
    organization_id: int,
    member_data: OrganizationMemberCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """添加组织成员"""
    # 检查用户是否有权限添加成员
    has_permission = await organization_service.check_organization_permission(
        db, current_user.id, organization_id, "admin"
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，只有管理员或所有者可以添加成员"
        )
    
    member = await organization_service.add_organization_member(
        db=db,
        organization_id=organization_id,
        inviter_id=current_user.id,
        user_email=member_data.user_email,
        role=member_data.role
    )
    
    return OrganizationMemberResponse(
        id=member.id,
        organization_id=member.organization_id,
        user_id=member.user_id,
        role=member.role,
        joined_at=member.joined_at,
        invited_by=member.invited_by,
        is_active=member.is_active
    )


@router.get("/{organization_id}/members", response_model=List[OrganizationMemberResponse])
async def get_organization_members(
    organization_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取组织成员列表"""
    # 检查用户是否有权限查看组织成员
    has_permission = await organization_service.check_organization_permission(
        db, current_user.id, organization_id, "member"
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，无法查看组织成员"
        )
    
    members = await organization_service.get_organization_members(
        db=db,
        organization_id=organization_id,
        skip=skip,
        limit=limit
    )
    
    return [
        OrganizationMemberResponse(
            id=member["id"],
            organization_id=organization_id,
            user_id=member["user_id"],
            role=member["role"],
            joined_at=member["joined_at"],
            invited_by=member["invited_by"],
            is_active=True,
            username=member["username"],
            email=member["email"],
            full_name=member["full_name"]
        )
        for member in members
    ]


@router.put("/{organization_id}/members/{member_id}", response_model=OrganizationMemberResponse)
async def update_organization_member_role(
    organization_id: int,
    member_id: int,
    member_data: OrganizationMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新组织成员角色"""
    member = await organization_service.update_member_role(
        db=db,
        organization_id=organization_id,
        operator_id=current_user.id,
        member_id=member_id,
        new_role=member_data.role
    )
    
    return OrganizationMemberResponse(
        id=member.id,
        organization_id=member.organization_id,
        user_id=member.user_id,
        role=member.role,
        joined_at=member.joined_at,
        invited_by=member.invited_by,
        is_active=member.is_active
    )


@router.delete("/{organization_id}/members/{member_id}")
async def remove_organization_member(
    organization_id: int,
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """移除组织成员"""
    success = await organization_service.remove_organization_member(
        db=db,
        organization_id=organization_id,
        operator_id=current_user.id,
        member_id=member_id
    )
    
    if success:
        return {"message": "成员移除成功"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="移除成员失败"
        ) 