from fastapi import APIRouter
from .git_error import router as git_error_router
from .code_review import router as code_review_router
from .commit_qa import router as commit_qa_router
from .commit_message import router as commit_message_router
from .code_quality import router as code_quality_router
from .push_strategy import router as push_strategy_router
from .intelligent_qa import router as intelligent_qa_router
from .repository_analysis import router as repository_analysis_router
from .openai_compatible import router as openai_router
from .sharedb import router as sharedb_router
from .organizations import router as organizations_router

router = APIRouter()

# 注册业务API路由
router.include_router(git_error_router, tags=["git_error"])
router.include_router(code_review_router, tags=["code_review"])
router.include_router(commit_qa_router, tags=["commit_qa"])
router.include_router(commit_message_router, tags=["commit_message"])
router.include_router(code_quality_router, tags=["code_quality"])
router.include_router(push_strategy_router, tags=["push_strategy"])
router.include_router(intelligent_qa_router, tags=["intelligent_qa"])
router.include_router(repository_analysis_router, tags=["repository_analysis"])

# 注册ShareDB协作API路由
router.include_router(sharedb_router, prefix="/sharedb", tags=["sharedb"])

# 注册OpenAI兼容API路由
router.include_router(openai_router, tags=["openai_compatible"])

# 注册组织管理API路由
router.include_router(organizations_router, prefix="/organizations", tags=["organizations"]) 