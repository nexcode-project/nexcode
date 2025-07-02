import os
from typing import Optional

class Settings:
    # OpenAI 配置（API密钥由客户端提供）
    OPENAI_API_BASE: Optional[str] = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # 模型参数
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1500"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    SOLUTION_TEMPERATURE: float = float(os.getenv("SOLUTION_TEMPERATURE", "0.3"))
    
    # 服务配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # 认证配置
    API_TOKEN: Optional[str] = os.getenv("API_TOKEN")  # API 访问令牌
    REQUIRE_AUTH: bool = os.getenv("REQUIRE_AUTH", "False").lower() == "true"  # 是否需要认证

settings = Settings() 