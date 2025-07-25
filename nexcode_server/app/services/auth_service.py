from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import secrets
import os
import xml.etree.ElementTree as ET
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
    
    def parse_cas_xml_response(self, xml_content: str) -> Optional[Dict[str, Any]]:
        """
        解析CAS XML响应，提取用户信息
        """
        try:
            # 移除XML中的命名空间前缀，简化解析
            xml_content = xml_content.replace('cas:', '')
            root = ET.fromstring(xml_content)
            
            # 查找authenticationSuccess元素
            auth_success = root.find('.//authenticationSuccess')
            if auth_success is None:
                return None
            
            # 提取用户名
            user_element = auth_success.find('user')
            username = user_element.text if user_element is not None else None
            
            if not username:
                return None
            
            # 提取属性
            attributes = {}
            attrs_element = auth_success.find('attributes')
            if attrs_element is not None:
                for attr in attrs_element:
                    # 移除命名空间前缀
                    tag_name = attr.tag.split('}')[-1] if '}' in attr.tag else attr.tag
                    attributes[tag_name] = attr.text
            
            # 构建用户信息
            user_info = {
                "username": username,
                "email": attributes.get("mail", attributes.get("email", f"{username}@example.com")),
                "full_name": attributes.get("displayName", attributes.get("cn", username)),
                "attributes": attributes
            }
            
            return user_info
            
        except ET.ParseError as e:
            print(f"XML解析错误: {e}")
            return None
        except Exception as e:
            print(f"CAS响应解析错误: {e}")
            return None
    
    async def verify_cas_ticket(self, ticket: str, service: str) -> Optional[Dict[str, Any]]:
        """验证CAS ticket"""
        try:
            # 使用httpx异步验证CAS ticket
            validate_url = f"{CAS_SERVER_URL}/serviceValidate"
            params = {
                "ticket": ticket,
                "service": service
            }
            
            print(f"验证CAS ticket: {validate_url}")
            print(f"参数: {params}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(validate_url, params=params)
                response.raise_for_status()
                
                print(f"CAS响应状态: {response.status_code}")
                print(f"CAS响应内容: {response.text[:500]}...")
                
                # 解析XML响应
                user_info = self.parse_cas_xml_response(response.text)
                if user_info:
                    print(f"解析出的用户信息: {user_info}")
                    return user_info
                else:
                    print("CAS响应中未找到用户信息")
                    return None
                    
        except httpx.TimeoutException:
            print("CAS验证超时")
            return None
        except httpx.HTTPStatusError as e:
            print(f"CAS验证HTTP错误: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"CAS验证失败: {e}")
            return None
    
    async def test_cas_connection(self) -> Dict[str, Any]:
        """
        测试CAS连接
        """
        try:
            # 测试CAS服务器是否可达
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(CAS_SERVER_URL)
                
                return {
                    "success": True,
                    "message": "CAS服务器连接成功",
                    "server_url": CAS_SERVER_URL,
                    "status_code": response.status_code,
                    "response_time": "< 10s"
                }
        except httpx.TimeoutException:
            return {
                "success": False,
                "message": "CAS服务器连接超时",
                "server_url": CAS_SERVER_URL
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"CAS服务器连接失败: {str(e)}",
                "server_url": CAS_SERVER_URL
            }
    
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
    
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        stmt = select(User).where(User.email == email, User.is_active == True)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """生成密码哈希"""
        return pwd_context.hash(password)
    
    async def authenticate_user(self, db: AsyncSession, username: str, password: str) -> Optional[User]:
        """验证用户名和密码"""
        user = await self.get_user_by_username(db, username)
        if not user:
            return None
        if not user.password_hash:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user
    
    async def create_user(self, db: AsyncSession, user_create: UserCreate) -> User:
        """创建新用户"""
        password_hash = self.get_password_hash(user_create.password)
        
        user = User(
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            password_hash=password_hash,
            is_active=True,
            is_superuser=False
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    async def verify_session_token(self, db: AsyncSession, session_token: str) -> Optional[User]:
        """验证会话令牌"""
        try:
            # 查询用户和会话
            stmt = select(User).join(UserSession).where(
                UserSession.session_token == session_token,
                UserSession.expires_at > datetime.utcnow(),
                User.is_active == True
            )
            
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                # 更新最后访问时间
                from sqlalchemy import update
                await db.execute(
                    update(UserSession)
                    .where(UserSession.session_token == session_token)
                    .values(
                        expires_at=datetime.utcnow() + timedelta(hours=24),
                        last_activity=datetime.utcnow()
                    )
                )
                await db.commit()
            
            return user
        except Exception as e:
            print(f"Error verifying session token: {e}")
            return None
    
    def generate_api_key(self) -> tuple[str, str, str]:
        """生成API密钥 - GitHub风格
        返回: (完整密钥, 密钥哈希, 密钥前缀)
        """
        # 生成GitHub风格的token: nxc_随机字符串
        random_part = secrets.token_urlsafe(32)
        key = f"nxc_{random_part}"
        
        # 生成哈希
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        # 生成前缀用于显示 (nxc_前8位...)
        key_prefix = f"{key[:12]}..."
        
        return key, key_hash, key_prefix
    
    async def create_api_key(self, db: AsyncSession, user_id: int, 
                           key_name: str, scopes: Optional[list] = None,
                           rate_limit: int = 1000, 
                           expires_at: Optional[datetime] = None) -> tuple[APIKey, str]:
        """创建API密钥"""
        from app.models.user_schemas import TokenScope
        
        # 如果未指定权限，使用默认权限
        if not scopes:
            scopes = TokenScope.get_default_scopes()
            
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
        if not api_key.startswith("nxc_"):
            return None
            
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

    async def verify_api_key_permission(self, db: AsyncSession, api_key: str, required_scope: str) -> Optional[User]:
        """验证API密钥权限"""
        if not api_key.startswith("nxc_"):
            return None
            
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
                
            # 检查权限范围
            if api_key_obj.scopes and required_scope not in api_key_obj.scopes:
                # 检查是否有admin权限
                from app.models.user_schemas import TokenScope
                if TokenScope.ADMIN not in api_key_obj.scopes:
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