from fastapi import APIRouter
from .git_error import router as git_error_router
from .code_review import router as code_review_router
from .commit_qa import router as commit_qa_router

router = APIRouter()

# 注册所有子路由
router.include_router(git_error_router)
router.include_router(code_review_router)
router.include_router(commit_qa_router) 