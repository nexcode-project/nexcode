from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import settings

security = HTTPBearer(auto_error=False)

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    验证 API Token
    
    Args:
        credentials: HTTP Bearer 认证凭据
    
    Returns:
        bool: 认证是否成功
    
    Raises:
        HTTPException: 认证失败时抛出 401 错误
    """
    # 如果不需要认证，直接返回成功
    if not settings.REQUIRE_AUTH:
        return True
    
    # 检查是否提供了认证凭据
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查 token 是否配置
    if not settings.API_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="Server authentication not configured"
        )
    
    # 验证 token
    if credentials.credentials != settings.API_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True

def get_auth_dependency():
    """
    获取认证依赖
    
    Returns:
        function: 认证依赖函数
    """
    if settings.REQUIRE_AUTH:
        return verify_token
    else:
        # 如果不需要认证，返回一个空的依赖
        return lambda: True 