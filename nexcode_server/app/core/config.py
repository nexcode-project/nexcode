import os
from typing import Optional

class Settings:
    # OpenAI 配置
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")  # 服务器的 OpenAI API Key
    OPENAI_API_BASE: Optional[str] = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # 改用更好的模型
    
    # 模型参数 - 针对代码分析优化
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))  # 增加token限制
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.3"))  # 降低温度提高确定性
    SOLUTION_TEMPERATURE: float = float(os.getenv("SOLUTION_TEMPERATURE", "0.1"))  # 更低的温度用于解决方案
    
    # 服务配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # 认证配置
    API_TOKEN: Optional[str] = os.getenv("API_TOKEN")  # API 访问令牌
    REQUIRE_AUTH: bool = os.getenv("REQUIRE_AUTH", "False").lower() == "true"  # 是否需要认证

settings = Settings() 