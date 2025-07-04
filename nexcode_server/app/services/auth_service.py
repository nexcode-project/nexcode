from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import secrets
import os
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from cas import CASClient
import httpx

from app.models.database import User, UserSession, APIKey
from app.models.user_schemas import UserCreate, Token, TokenData

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# CAS配置
CAS_SERVER_URL = os.getenv("CAS_SERVER_URL", "https://cas.example.com")
CAS_SERVICE_URL = os.getenv("CAS_SERVICE_URL", "http://localhost:8000/auth/cas/callback")

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self):
        self.cas_client = CASClient(
            version=3,
            service_url=CAS_SERVICE_URL,
            server_url=CAS_SERVER_URL
        )
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """创建JWT token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """验证JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: int = payload.get("sub")
            username: str = payload.get("username")
            if user_id is None:
                return None
            token_data = TokenData(user_id=user_id, username=username)
            return token_data
        except JWTError:
            return None
    
    def get_cas_login_url(self) -> str:
        """获取CAS登录URL"""
        return self.cas_client.get_login_url()
    
    async def verify_cas_ticket(self, ticket: str, service: str) -> Optional[Dict[str, Any]]:
        """验证CAS ticket"""
        try:
            # 使用httpx异步验证CAS ticket
            validate_url = f"{CAS_SERVER_URL}/serviceValidate"
            params = {
                "ticket": ticket,
                "service": service
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(validate_url, params=params)
                response.raise_for_status()
                
                # 解析CAS响应（简化版，实际需要解析XML）
                if "cas:authenticationSuccess" in response.text:
                    # 提取用户信息（这里需要根据实际CAS响应格式解析）
                    return {
                        "username": "cas_user",  # 从响应中提取
                        "email": "cas_user@example.com",  # 从响应中提取
                        "attributes": {}  # 从响应中提取其他属性
                    }
                return None
        except Exception as e:
            print(f"CAS验证失败: {e}")
            return None
    
    async def create_or_get_user_from_cas(self, db: AsyncSession, cas_info: Dict[str, Any]) -> User:
        """从CAS信息创建或获取用户"""
        # 查找现有用户
        stmt = select(User).where(User.username == cas_info["username"])
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            # 更新CAS属性
            user.cas_attributes = cas_info.get("attributes", {})
            user.last_login = datetime.utcnow()
        else:
            # 创建新用户
            user = User(
                username=cas_info["username"],
                email=cas_info["email"],
                full_name=cas_info.get("full_name"),
                cas_user_id=cas_info["username"],
                cas_attributes=cas_info.get("attributes", {}),
                last_login=datetime.utcnow()
            )
            db.add(user)
        
        await db.commit()
        await db.refresh(user)
        return user
    
    async def create_user_session(self, db: AsyncSession, user_id: int, 
                                cas_ticket: Optional[str] = None,
                                ip_address: Optional[str] = None,
                                user_agent: Optional[str] = None) -> UserSession:
        """创建用户会话"""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)  # 24小时过期
        
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            cas_ticket=cas_ticket,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session
    
    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        stmt = select(User).where(User.id == user_id, User.is_active == True)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        stmt = select(User).where(User.username == username, User.is_active == True)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def verify_session_token(self, db: AsyncSession, session_token: str) -> Optional[User]:
        """验证会话token"""
        stmt = select(UserSession).where(
            UserSession.session_token == session_token,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if session:
            # 更新最后活动时间
            session.last_activity = datetime.utcnow()
            await db.commit()
            
            # 获取用户
            return await self.get_user_by_id(db, session.user_id)
        return None
    
    def generate_api_key(self) -> tuple[str, str, str]:
        """生成API密钥
        返回: (完整密钥, 密钥哈希, 密钥前缀)
        """
        # 生成随机密钥
        key = f"nxc_{secrets.token_urlsafe(32)}"
        
        # 生成哈希
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        # 生成前缀用于显示
        key_prefix = key[:10] + "..."
        
        return key, key_hash, key_prefix
    
    async def create_api_key(self, db: AsyncSession, user_id: int, 
                           key_name: str, scopes: Optional[list] = None,
                           rate_limit: int = 1000, 
                           expires_at: Optional[datetime] = None) -> tuple[APIKey, str]:
        """创建API密钥"""
        key, key_hash, key_prefix = self.generate_api_key()
        
        api_key = APIKey(
            user_id=user_id,
            key_name=key_name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            scopes=scopes,
            rate_limit=rate_limit,
            expires_at=expires_at
        )
        
        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)
        
        return api_key, key
    
    async def verify_api_key(self, db: AsyncSession, api_key: str) -> Optional[User]:
        """验证API密钥"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        stmt = select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        )
        result = await db.execute(stmt)
        api_key_obj = result.scalar_one_or_none()
        
        if api_key_obj:
            # 检查是否过期
            if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
                return None
            
            # 更新使用统计
            api_key_obj.usage_count += 1
            api_key_obj.last_used = datetime.utcnow()
            await db.commit()
            
            # 获取用户
            return await self.get_user_by_id(db, api_key_obj.user_id)
        return None

# 创建全局实例
auth_service = AuthService() 