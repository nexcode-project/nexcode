from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import router as v1_router
from app.core.config import settings
from app.models.schemas import HealthCheckResponse
from datetime import datetime

app = FastAPI(
    title="NexCode LLM Proxy Server",
    description="A FastAPI backend for LLM-powered code and git assistant.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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

@app.get("/")
async def root():
    """健康检查接口"""
    return {
        "message": "NexCode LLM Proxy Server is running",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """详细的服务健康检查"""
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        services={
            "git_error_analysis": "operational",
            "code_review": "operational", 
            "commit_message": "operational",
            "commit_qa": "operational",
            "code_quality": "operational",
            "push_strategy": "operational",
            "intelligent_qa": "operational",
            "repository_analysis": "operational"
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