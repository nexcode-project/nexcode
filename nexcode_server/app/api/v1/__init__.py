from fastapi import APIRouter
from .git_error import router as git_error_router
from .code_review import router as code_review_router
from .commit_qa import router as commit_qa_router
from .commit_message import router as commit_message_router
from .code_quality import router as code_quality_router
from .push_strategy import router as push_strategy_router
from .intelligent_qa import router as intelligent_qa_router
from .repository_analysis import router as repository_analysis_router

router = APIRouter()

# 注册所有子路由
router.include_router(git_error_router)
router.include_router(code_review_router)
router.include_router(commit_qa_router)
router.include_router(commit_message_router)
router.include_router(code_quality_router)
router.include_router(push_strategy_router)
router.include_router(intelligent_qa_router)
router.include_router(repository_analysis_router) 