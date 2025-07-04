from fastapi import APIRouter, HTTPException, status, Response, Request, Depends
from fastapi.responses import RedirectResponse
from typing import Optional
from datetime import timedelta

from app.core.dependencies import DatabaseSession, OptionalUser
from app.services.auth_service import auth_service
from app.models.user_schemas import Token, UserCASLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.get("/cas/login")
async def cas_login():
    """获取CAS登录URL"""
    login_url = auth_service.get_cas_login_url()
    return {"login_url": login_url}

@router.get("/cas/login/redirect")
async def cas_login_redirect():
    """重定向到CAS登录页面"""
    login_url = auth_service.get_cas_login_url()
    return RedirectResponse(url=login_url)

@router.get("/cas/callback")
async def cas_callback(
    request: Request,
    response: Response,
    db: DatabaseSession,
    ticket: Optional[str] = None,
    service: Optional[str] = None
):
    """CAS登录回调处理"""
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing CAS ticket"
        )
    
    if not service:
        service = str(request.url_for("cas_callback"))
    
    # 验证CAS ticket
    cas_info = await auth_service.verify_cas_ticket(ticket, service)
    if not cas_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid CAS ticket"
        )
    
    # 创建或获取用户
    user = await auth_service.create_or_get_user_from_cas(db, cas_info)
    
    # 创建用户会话
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    session = await auth_service.create_user_session(
        db=db,
        user_id=user.id,
        cas_ticket=ticket,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    # 创建JWT token
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )
    
    # 设置Cookie
    response.set_cookie(
        key="session_token",
        value=session.session_token,
        max_age=86400,  # 24小时
        httponly=True,
        secure=True,  # 生产环境启用
        samesite="lax"
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800,  # 30分钟
        "user": UserResponse.model_validate(user),
        "session_token": session.session_token
    }

@router.post("/cas/verify", response_model=Token)
async def cas_verify_ticket(
    request: Request,
    response: Response,
    cas_login: UserCASLogin,
    db: DatabaseSession
):
    """手动验证CAS ticket"""
    # 验证CAS ticket
    cas_info = await auth_service.verify_cas_ticket(cas_login.cas_ticket, cas_login.service_url)
    if not cas_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid CAS ticket"
        )
    
    # 创建或获取用户
    user = await auth_service.create_or_get_user_from_cas(db, cas_info)
    
    # 创建用户会话
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    session = await auth_service.create_user_session(
        db=db,
        user_id=user.id,
        cas_ticket=cas_login.cas_ticket,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    # 创建JWT token
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )
    
    # 设置Cookie
    response.set_cookie(
        key="session_token",
        value=session.session_token,
        max_age=86400,  # 24小时
        httponly=True,
        secure=True,  # 生产环境启用
        samesite="lax"
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=1800  # 30分钟
    )

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: OptionalUser,
    db: DatabaseSession
):
    """用户登出"""
    if current_user:
        # 从Cookie获取session token
        session_token = request.cookies.get("session_token")
        if session_token:
            # 撤销会话
            from sqlalchemy import select
            from app.models.database import UserSession
            
            stmt = select(UserSession).where(
                UserSession.session_token == session_token,
                UserSession.user_id == current_user.id
            )
            result = await db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if session:
                session.is_active = False
                await db.commit()
    
    # 清除Cookie
    response.delete_cookie(key="session_token")
    
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: OptionalUser):
    """获取当前认证用户信息"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return current_user

@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    db: DatabaseSession
):
    """刷新JWT token"""
    # 从Cookie获取session token
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No valid session found"
        )
    
    # 验证会话
    user = await auth_service.verify_session_token(db, session_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )
    
    # 创建新的JWT token
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=1800  # 30分钟
    )

@router.get("/status")
async def auth_status(current_user: OptionalUser):
    """检查认证状态"""
    if current_user:
        return {
            "authenticated": True,
            "user": UserResponse.model_validate(current_user)
        }
    else:
        return {
            "authenticated": False,
            "user": None
        } 