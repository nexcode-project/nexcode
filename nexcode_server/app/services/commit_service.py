from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import selectinload

from app.models.database import CommitInfo, User
from app.models.user_schemas import (
    CommitInfoCreate, CommitInfoUpdate, CommitInfoResponse,
    UserCommitStats, CommitTrends, CommitAnalytics
)

class CommitService:
    
    async def create_commit_info(self, db: AsyncSession, user_id: int, 
                               commit_data: CommitInfoCreate) -> CommitInfo:
        """创建commit信息记录"""
        commit_info = CommitInfo(
            user_id=user_id,
            **commit_data.model_dump()
        )
        
        db.add(commit_info)
        await db.commit()
        await db.refresh(commit_info)
        return commit_info
    
    async def get_commit_info(self, db: AsyncSession, commit_id: int, 
                            user_id: Optional[int] = None) -> Optional[CommitInfo]:
        """获取单个commit信息"""
        stmt = select(CommitInfo).where(CommitInfo.id == commit_id)
        if user_id:
            stmt = stmt.where(CommitInfo.user_id == user_id)
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_commit_info(self, db: AsyncSession, commit_id: int, 
                               user_id: int, commit_data: CommitInfoUpdate) -> Optional[CommitInfo]:
        """更新commit信息"""
        commit_info = await self.get_commit_info(db, commit_id, user_id)
        if not commit_info:
            return None
        
        update_data = commit_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(commit_info, field, value)
        
        await db.commit()
        await db.refresh(commit_info)
        return commit_info
    
    async def delete_commit_info(self, db: AsyncSession, commit_id: int, 
                               user_id: int) -> bool:
        """删除commit信息"""
        commit_info = await self.get_commit_info(db, commit_id, user_id)
        if not commit_info:
            return False
        
        await db.delete(commit_info)
        await db.commit()
        return True
    
    async def get_user_commits(self, db: AsyncSession, user_id: int,
                             skip: int = 0, limit: int = 100,
                             repository_name: Optional[str] = None,
                             status: Optional[str] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> List[CommitInfo]:
        """获取用户的commit列表"""
        stmt = select(CommitInfo).where(CommitInfo.user_id == user_id)
        
        # 添加筛选条件
        if repository_name:
            stmt = stmt.where(CommitInfo.repository_name == repository_name)
        if status:
            stmt = stmt.where(CommitInfo.status == status)
        if start_date:
            stmt = stmt.where(CommitInfo.created_at >= start_date)
        if end_date:
            stmt = stmt.where(CommitInfo.created_at <= end_date)
        
        # 排序和分页
        stmt = stmt.order_by(desc(CommitInfo.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_commits_with_user(self, db: AsyncSession, skip: int = 0, limit: int = 100,
                                  repository_name: Optional[str] = None) -> List[CommitInfo]:
        """获取包含用户信息的commit列表（管理员功能）"""
        stmt = select(CommitInfo).options(selectinload(CommitInfo.user))
        
        if repository_name:
            stmt = stmt.where(CommitInfo.repository_name == repository_name)
        
        stmt = stmt.order_by(desc(CommitInfo.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_commit_stats(self, db: AsyncSession, user_id: int) -> UserCommitStats:
        """获取用户commit统计信息"""
        # 总commit数
        total_stmt = select(func.count(CommitInfo.id)).where(CommitInfo.user_id == user_id)
        total_result = await db.execute(total_stmt)
        total_commits = total_result.scalar() or 0
        
        # 本月commit数
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_stmt = select(func.count(CommitInfo.id)).where(
            and_(
                CommitInfo.user_id == user_id,
                CommitInfo.created_at >= month_start
            )
        )
        month_result = await db.execute(month_stmt)
        commits_this_month = month_result.scalar() or 0
        
        # 平均评分
        rating_stmt = select(func.avg(CommitInfo.user_rating)).where(
            and_(
                CommitInfo.user_id == user_id,
                CommitInfo.user_rating.isnot(None)
            )
        )
        rating_result = await db.execute(rating_stmt)
        avg_rating = rating_result.scalar()
        
        # 最常用的commit风格
        style_stmt = select(
            CommitInfo.commit_style,
            func.count(CommitInfo.id).label('count')
        ).where(
            CommitInfo.user_id == user_id
        ).group_by(
            CommitInfo.commit_style
        ).order_by(
            desc('count')
        ).limit(1)
        style_result = await db.execute(style_stmt)
        style_row = style_result.first()
        most_used_style = style_row[0] if style_row else "conventional"
        
        # 代码行数统计
        lines_stmt = select(
            func.sum(CommitInfo.lines_added).label('total_added'),
            func.sum(CommitInfo.lines_deleted).label('total_deleted')
        ).where(CommitInfo.user_id == user_id)
        lines_result = await db.execute(lines_stmt)
        lines_row = lines_result.first()
        total_lines_added = lines_row[0] or 0
        total_lines_deleted = lines_row[1] or 0
        
        return UserCommitStats(
            total_commits=total_commits,
            commits_this_month=commits_this_month,
            avg_rating=float(avg_rating) if avg_rating else None,
            most_used_style=most_used_style,
            total_lines_added=total_lines_added,
            total_lines_deleted=total_lines_deleted
        )
    
    async def get_commit_trends(self, db: AsyncSession, user_id: int, 
                              days: int = 30) -> List[CommitTrends]:
        """获取commit趋势数据"""
        start_date = datetime.now() - timedelta(days=days)
        
        stmt = select(
            func.date(CommitInfo.created_at).label('date'),
            func.count(CommitInfo.id).label('commit_count'),
            func.avg(CommitInfo.generation_time_ms).label('avg_generation_time')
        ).where(
            and_(
                CommitInfo.user_id == user_id,
                CommitInfo.created_at >= start_date
            )
        ).group_by(
            func.date(CommitInfo.created_at)
        ).order_by(
            'date'
        )
        
        result = await db.execute(stmt)
        trends = []
        for row in result:
            trends.append(CommitTrends(
                date=row.date.isoformat(),
                commit_count=row.commit_count,
                avg_generation_time=float(row.avg_generation_time) if row.avg_generation_time else None
            ))
        
        return trends
    
    async def get_top_repositories(self, db: AsyncSession, user_id: int, 
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户最活跃的仓库"""
        stmt = select(
            CommitInfo.repository_name,
            func.count(CommitInfo.id).label('commit_count'),
            func.max(CommitInfo.created_at).label('last_commit')
        ).where(
            and_(
                CommitInfo.user_id == user_id,
                CommitInfo.repository_name.isnot(None)
            )
        ).group_by(
            CommitInfo.repository_name
        ).order_by(
            desc('commit_count')
        ).limit(limit)
        
        result = await db.execute(stmt)
        repositories = []
        for row in result:
            repositories.append({
                "repository_name": row.repository_name,
                "commit_count": row.commit_count,
                "last_commit": row.last_commit.isoformat() if row.last_commit else None
            })
        
        return repositories
    
    async def get_commit_analytics(self, db: AsyncSession, user_id: int) -> CommitAnalytics:
        """获取完整的commit分析数据"""
        user_stats = await self.get_commit_stats(db, user_id)
        recent_trends = await self.get_commit_trends(db, user_id)
        top_repositories = await self.get_top_repositories(db, user_id)
        
        return CommitAnalytics(
            user_stats=user_stats,
            recent_trends=recent_trends,
            top_repositories=top_repositories
        )
    
    async def search_commits(self, db: AsyncSession, user_id: Optional[int] = None,
                           query: Optional[str] = None,
                           repository_name: Optional[str] = None,
                           commit_style: Optional[str] = None,
                           min_rating: Optional[int] = None,
                           skip: int = 0, limit: int = 100) -> List[CommitInfo]:
        """搜索commit信息"""
        stmt = select(CommitInfo)
        
        if user_id:
            stmt = stmt.where(CommitInfo.user_id == user_id)
        
        if query:
            # 在commit消息中搜索
            search_filter = func.lower(CommitInfo.final_commit_message).contains(query.lower())
            stmt = stmt.where(search_filter)
        
        if repository_name:
            stmt = stmt.where(CommitInfo.repository_name == repository_name)
        
        if commit_style:
            stmt = stmt.where(CommitInfo.commit_style == commit_style)
        
        if min_rating:
            stmt = stmt.where(CommitInfo.user_rating >= min_rating)
        
        stmt = stmt.order_by(desc(CommitInfo.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def mark_commit_as_committed(self, db: AsyncSession, commit_id: int, 
                                     user_id: int, commit_hash: str) -> Optional[CommitInfo]:
        """标记commit为已提交状态"""
        commit_info = await self.get_commit_info(db, commit_id, user_id)
        if not commit_info:
            return None
        
        commit_info.status = "committed"
        commit_info.commit_hash = commit_hash
        commit_info.committed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(commit_info)
        return commit_info
    
    async def add_user_feedback(self, db: AsyncSession, commit_id: int, 
                              user_id: int, rating: int, feedback: Optional[str] = None) -> Optional[CommitInfo]:
        """添加用户反馈"""
        commit_info = await self.get_commit_info(db, commit_id, user_id)
        if not commit_info:
            return None
        
        commit_info.user_rating = rating
        commit_info.user_feedback = feedback
        
        await db.commit()
        await db.refresh(commit_info)
        return commit_info

# 创建全局实例
commit_service = CommitService() 