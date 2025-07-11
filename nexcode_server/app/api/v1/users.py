from fastapi import APIRouter, HTTPException, status, Response, Request
from typing import List, Optional
from datetime import timedelta

from app.core.dependencies import CurrentUser, CurrentSuperUser, DatabaseSession
from app.services.auth_service import auth_service
from app.models.user_schemas import (
    UserResponse, UserUpdate, UserProfile, UserCASLogin, Token,
    APIKeyCreate, APIKeyResponse, APIKeyWithToken, UserSessionResponse,
    UserCreate
)

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: CurrentUser):
    """获取当前用户信息"""
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """更新当前用户信息"""
    # 检查用户名是否已存在
    if user_update.username:
        existing_user = await auth_service.get_user_by_username(db, user_update.username)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
    
    # 更新用户信息
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.get("/me/sessions", response_model=List[UserSessionResponse])
async def get_user_sessions(current_user: CurrentUser, db: DatabaseSession):
    """获取用户会话列表"""
    from sqlalchemy import select
    from app.models.database import UserSession
    
    stmt = select(UserSession).where(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).order_by(UserSession.created_at.desc())
    
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return sessions

@router.delete("/me/sessions/{session_id}")
async def revoke_user_session(
    session_id: int,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """撤销用户会话"""
    from sqlalchemy import select
    from app.models.database import UserSession
    
    stmt = select(UserSession).where(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    session.is_active = False
    await db.commit()
    
    return {"message": "Session revoked successfully"}

@router.get("/me/api-keys", response_model=List[APIKeyResponse])
async def get_user_api_keys(current_user: CurrentUser, db: DatabaseSession):
    """获取用户API密钥列表"""
    from sqlalchemy import select
    from app.models.database import APIKey
    
    stmt = select(APIKey).where(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True
    ).order_by(APIKey.created_at.desc())
    
    result = await db.execute(stmt)
    api_keys = result.scalars().all()
    return api_keys

@router.post("/me/api-keys", response_model=APIKeyWithToken)
async def create_user_api_key(
    api_key_data: APIKeyCreate,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """创建用户API密钥"""
    api_key, token = await auth_service.create_api_key(
        db=db,
        user_id=current_user.id,
        key_name=api_key_data.key_name,
        scopes=api_key_data.scopes,
        rate_limit=api_key_data.rate_limit,
        expires_at=api_key_data.expires_at
    )
    
    # 返回包含完整token的响应
    return APIKeyWithToken(
        **api_key.__dict__,
        token=token
    )

@router.delete("/me/api-keys/{api_key_id}")
async def revoke_user_api_key(
    api_key_id: int,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """撤销用户API密钥"""
    from sqlalchemy import select
    from app.models.database import APIKey
    
    stmt = select(APIKey).where(
        APIKey.id == api_key_id,
        APIKey.user_id == current_user.id
    )
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    api_key.is_active = False
    await db.commit()
    
    return {"message": "API key revoked successfully"}

# 管理员用户管理
@router.get("/", response_model=List[UserResponse])
async def list_users(
    admin_user: CurrentSuperUser,
    db: DatabaseSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
):
    """获取用户列表（管理员）"""
    from sqlalchemy import select, or_
    from app.models.database import User
    
    stmt = select(User)
    
    if search:
        search_filter = or_(
            User.username.contains(search),
            User.email.contains(search),
            User.full_name.contains(search)
        )
        stmt = stmt.where(search_filter)
    
    stmt = stmt.offset(skip).limit(limit).order_by(User.created_at.desc())
    
    result = await db.execute(stmt)
    users = result.scalars().all()
    return users

@router.get("/{user_id}", response_model=UserProfile)
async def get_user_by_id(
    user_id: int,
    admin_user: CurrentSuperUser,
    db: DatabaseSession
):
    """获取指定用户信息（管理员）"""
    user = await auth_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_by_id(
    user_id: int,
    user_update: UserUpdate,
    admin_user: CurrentSuperUser,
    db: DatabaseSession
):
    """更新指定用户信息（管理员）"""
    user = await auth_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 检查用户名是否已存在
    if user_update.username:
        existing_user = await auth_service.get_user_by_username(db, user_update.username)
        if existing_user and existing_user.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
    
    # 更新用户信息
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{user_id}")
async def deactivate_user(
    user_id: int,
    admin_user: CurrentSuperUser,
    db: DatabaseSession
):
    """停用用户（管理员）"""
    user = await auth_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    await db.commit()
    
    return {"message": f"User {user.username} deactivated successfully"} 

# 新增：管理员创建用户
@router.post("/admin/create", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    user_create: UserCreate,
    admin_user: CurrentSuperUser,
    db: DatabaseSession
):
    """管理员创建新用户"""
    # 检查用户名是否已存在
    existing_user = await auth_service.get_user_by_username(db, user_create.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # 检查邮箱是否已存在
    if user_create.email:
        existing_email = await auth_service.get_user_by_email(db, user_create.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )

    # 创建用户
    user = await auth_service.create_user(db, user_create)
    return UserResponse.model_validate(user)

# 兼容老前端：/users/admin/all
@router.get("/admin/all", response_model=List[UserResponse])
async def admin_list_users_alias(
    admin_user: CurrentSuperUser,
    db: DatabaseSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
):
    """获取用户列表（管理员）老接口兼容"""
    return await list_users(admin_user, db, skip, limit, search) 