from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Annotated

from app.core.database import get_db
from app.services.auth_service import auth_service
from app.models.database import User

# HTTP Bearer 认证
security = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户（JWT或API Key认证）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user = None
    
    if credentials:
        token = credentials.credentials
        
        # 首先尝试JWT验证
        token_data = auth_service.verify_token(token)
        if token_data and token_data.user_id:
            user = await auth_service.get_user_by_id(db, token_data.user_id)
        
        # 如果JWT验证失败，尝试API Key验证
        if not user:
            user = await auth_service.verify_api_key(db, token)
    
    # 检查Session Token（从Cookie或Header）
    if not user:
        session_token = None
        
        # 从Cookie获取
        if "session_token" in request.cookies:
            session_token = request.cookies["session_token"]
        
        # 从Header获取
        elif "X-Session-Token" in request.headers:
            session_token = request.headers["X-Session-Token"]
        
        if session_token:
            user = await auth_service.verify_session_token(db, session_token)
    
    if not user:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """获取可选用户（不强制认证）"""
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None

# 类型别名
CurrentUser = Annotated[User, Depends(get_current_active_user)]
CurrentSuperUser = Annotated[User, Depends(get_current_superuser)]
OptionalUser = Annotated[Optional[User], Depends(get_optional_user)]
DatabaseSession = Annotated[AsyncSession, Depends(get_db)] 