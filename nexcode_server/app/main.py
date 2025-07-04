from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

from app.api.v1 import router as v1_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.commits import router as commits_router
from app.api.v1.admin import router as admin_router
from app.core.config import settings
from app.core.database import init_db
from app.models.schemas import HealthCheckResponse
from datetime import datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()
    yield
    # 关闭时的清理工作（如果需要）

app = FastAPI(
    title="NexCode AIOps Platform",
    description="A comprehensive AIOps platform with LLM-powered development tools, user management, and commit tracking.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(v1_router, prefix="/v1")
app.include_router(auth_router, prefix="/v1")
app.include_router(users_router, prefix="/v1")
app.include_router(commits_router, prefix="/v1")
app.include_router(admin_router, prefix="/v1")

@app.get("/")
async def root():
    """健康检查接口"""
    return {
        "message": "NexCode AIOps Platform is running",
        "version": "2.0.0",
        "docs_url": "/docs",
        "features": {
            "llm_proxy": True,
            "user_management": True,
            "cas_authentication": True,
            "commit_tracking": True,
            "openai_compatible": True
        },
        "endpoints": {
            "auth": "/v1/auth",
            "users": "/v1/users", 
            "commits": "/v1/commits",
            "openai": ["/v1/chat/completions", "/v1/completions"]
        }
    }

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """详细的服务健康检查"""
    return HealthCheckResponse(
        status="healthy",
        version="2.0.0",
        services={
            "git_error_analysis": "operational",
            "code_review": "operational", 
            "commit_message": "operational",
            "commit_qa": "operational",
            "code_quality": "operational",
            "push_strategy": "operational",
            "intelligent_qa": "operational",
            "repository_analysis": "operational",
            "openai_compatible_api": "operational",
            "user_management": "operational",
            "cas_authentication": "operational",
            "commit_tracking": "operational",
            "database": "operational"
        },
        timestamp=datetime.now().isoformat()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    ) 