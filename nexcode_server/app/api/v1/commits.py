from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime

from app.core.dependencies import CurrentUser, CurrentSuperUser, DatabaseSession
from app.services.commit_service import commit_service
from app.models.user_schemas import (
    CommitInfoCreate, CommitInfoUpdate, CommitInfoResponse,
    CommitInfoWithUser, CommitAnalytics, UserCommitStats
)

router = APIRouter(prefix="/commits", tags=["commits"])

@router.post("/", response_model=CommitInfoResponse)
async def create_commit_info(
    commit_data: CommitInfoCreate,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """创建commit信息记录"""
    commit_info = await commit_service.create_commit_info(
        db=db,
        user_id=current_user.id,
        commit_data=commit_data
    )
    return commit_info

@router.get("/", response_model=List[CommitInfoResponse])
async def get_user_commits(
    current_user: CurrentUser,
    db: DatabaseSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    repository_name: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """获取当前用户的commit列表"""
    commits = await commit_service.get_user_commits(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        repository_name=repository_name,
        status=status,
        start_date=start_date,
        end_date=end_date
    )
    return commits

@router.get("/search", response_model=List[CommitInfoResponse])
async def search_commits(
    current_user: CurrentUser,
    db: DatabaseSession,
    query: Optional[str] = None,
    repository_name: Optional[str] = None,
    commit_style: Optional[str] = None,
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """搜索当前用户的commit信息"""
    commits = await commit_service.search_commits(
        db=db,
        user_id=current_user.id,
        query=query,
        repository_name=repository_name,
        commit_style=commit_style,
        min_rating=min_rating,
        skip=skip,
        limit=limit
    )
    return commits

@router.get("/analytics", response_model=CommitAnalytics)
async def get_commit_analytics(
    current_user: CurrentUser,
    db: DatabaseSession
):
    """获取当前用户的commit分析数据"""
    analytics = await commit_service.get_commit_analytics(db, current_user.id)
    return analytics

@router.get("/stats", response_model=UserCommitStats)
async def get_commit_stats(
    current_user: CurrentUser,
    db: DatabaseSession
):
    """获取当前用户的commit统计信息"""
    stats = await commit_service.get_commit_stats(db, current_user.id)
    return stats

@router.get("/{commit_id}", response_model=CommitInfoResponse)
async def get_commit_info(
    commit_id: int,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """获取单个commit信息"""
    commit_info = await commit_service.get_commit_info(db, commit_id, current_user.id)
    if not commit_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commit info not found"
        )
    return commit_info

@router.patch("/{commit_id}", response_model=CommitInfoResponse)
async def update_commit_info(
    commit_id: int,
    commit_data: CommitInfoUpdate,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """更新commit信息"""
    commit_info = await commit_service.update_commit_info(
        db=db,
        commit_id=commit_id,
        user_id=current_user.id,
        commit_data=commit_data
    )
    if not commit_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commit info not found"
        )
    return commit_info

@router.delete("/{commit_id}")
async def delete_commit_info(
    commit_id: int,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """删除commit信息"""
    success = await commit_service.delete_commit_info(
        db=db,
        commit_id=commit_id,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commit info not found"
        )
    return {"message": "Commit info deleted successfully"}

@router.post("/{commit_id}/commit", response_model=CommitInfoResponse)
async def mark_commit_as_committed(
    commit_id: int,
    commit_hash: str,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """标记commit为已提交状态"""
    commit_info = await commit_service.mark_commit_as_committed(
        db=db,
        commit_id=commit_id,
        user_id=current_user.id,
        commit_hash=commit_hash
    )
    if not commit_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commit info not found"
        )
    return commit_info

@router.post("/{commit_id}/feedback", response_model=CommitInfoResponse)
async def add_commit_feedback(
    commit_id: int,
    current_user: CurrentUser,
    db: DatabaseSession,
    rating: int = Query(..., ge=1, le=5),
    feedback: Optional[str] = None
):
    """添加commit反馈"""
    commit_info = await commit_service.add_user_feedback(
        db=db,
        commit_id=commit_id,
        user_id=current_user.id,
        rating=rating,
        feedback=feedback
    )
    if not commit_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commit info not found"
        )
    return commit_info

# 管理员接口
@router.get("/admin/all", response_model=List[CommitInfoWithUser])
async def get_all_commits(
    admin_user: CurrentSuperUser,
    db: DatabaseSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    repository_name: Optional[str] = None
):
    """获取所有用户的commit列表（管理员）"""
    commits = await commit_service.get_commits_with_user(
        db=db,
        skip=skip,
        limit=limit,
        repository_name=repository_name
    )
    return commits

@router.get("/admin/search", response_model=List[CommitInfoResponse])
async def admin_search_commits(
    admin_user: CurrentSuperUser,
    db: DatabaseSession,
    user_id: Optional[int] = None,
    query: Optional[str] = None,
    repository_name: Optional[str] = None,
    commit_style: Optional[str] = None,
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """搜索所有commit信息（管理员）"""
    commits = await commit_service.search_commits(
        db=db,
        user_id=user_id,
        query=query,
        repository_name=repository_name,
        commit_style=commit_style,
        min_rating=min_rating,
        skip=skip,
        limit=limit
    )
    return commits

@router.get("/admin/user/{user_id}/analytics", response_model=CommitAnalytics)
async def get_user_commit_analytics(
    user_id: int,
    admin_user: CurrentSuperUser,
    db: DatabaseSession
):
    """获取指定用户的commit分析数据（管理员）"""
    analytics = await commit_service.get_commit_analytics(db, user_id)
    return analytics 