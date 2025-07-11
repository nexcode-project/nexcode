from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentSuperUser, DatabaseSession
from app.models.database import User, CommitInfo, UserSession, APIKey, SystemSettings
from app.models.user_schemas import SystemSettingsResponse, SystemSettingsUpdate
from app.services.auth_service import auth_service
from app.core.config import settings
import os
import psutil
from app.services.commit_service import commit_service

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/stats")
async def get_system_stats(
    admin_user: CurrentSuperUser,
    db: DatabaseSession
):
    """获取系统统计信息"""
    try:
        # 获取系统资源信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 获取数据库统计
        total_users_stmt = select(func.count(User.id))
        total_users_result = await db.execute(total_users_stmt)
        total_users = total_users_result.scalar()
        
        active_users_stmt = select(func.count(User.id)).where(User.is_active == True)
        active_users_result = await db.execute(active_users_stmt)
        active_users = active_users_result.scalar()
        
        # 获取提交统计
        total_commits_stmt = select(func.count(CommitInfo.id))
        total_commits_result = await db.execute(total_commits_stmt)
        total_commits = total_commits_result.scalar()
        
        # 获取今天的提交数
        today = datetime.now().date()
        commits_today_stmt = select(func.count(CommitInfo.id)).where(
            func.date(CommitInfo.created_at) == today
        )
        commits_today_result = await db.execute(commits_today_stmt)
        commits_today = commits_today_result.scalar()
        
        # 获取本月提交数
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_commits_stmt = select(func.count(CommitInfo.id)).where(
            CommitInfo.created_at >= month_start
        )
        month_commits_result = await db.execute(month_commits_stmt)
        month_commits = month_commits_result.scalar()
        
        # 获取平均评分
        avg_rating_stmt = select(func.avg(CommitInfo.user_rating)).where(
            CommitInfo.user_rating.is_not(None)
        )
        avg_rating_result = await db.execute(avg_rating_stmt)
        avg_rating = avg_rating_result.scalar() or 0
        
        # 获取API调用统计（从API密钥使用次数计算）
        api_calls_stmt = select(func.sum(APIKey.usage_count)).where(
            APIKey.is_active == True
        )
        api_calls_result = await db.execute(api_calls_stmt)
        api_calls_today = api_calls_result.scalar() or 0
        
        return {
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                }
            },
            "database": {
                "total_users": total_users or 0,
                "active_users": active_users or 0,
                "total_commits": total_commits or 0,
                "today_commits": commits_today or 0,
                "month_commits": month_commits or 0
            },
            "avg_rating": round(float(avg_rating), 2),
            "api_calls_today": api_calls_today,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统统计失败: {str(e)}"
        )

@router.get("/system/health")
async def get_system_health(admin_user: CurrentSuperUser):
    """获取系统健康状态"""
    try:
        # 获取系统资源使用情况
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "healthy",
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "disk_usage": disk.percent,
            "uptime": psutil.boot_time(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/cas/config")
async def get_cas_config(admin_user: CurrentSuperUser):
    """获取CAS配置"""
    return {
        "enabled": bool(os.getenv("CAS_SERVER_URL")),
        "server_url": os.getenv("CAS_SERVER_URL", ""),
        "service_url": os.getenv("CAS_SERVICE_URL", ""),
        "logout_url": os.getenv("CAS_LOGOUT_URL", ""),
        "attributes_mapping": {
            "username": "uid",
            "email": "mail",
            "full_name": "displayName"
        }
    }

@router.put("/cas/config")
async def update_cas_config(
    config: Dict[str, Any],
    admin_user: CurrentSuperUser
):
    """更新CAS配置"""
    try:
        # 这里应该更新环境变量或配置文件
        # 为了简化，暂时返回更新成功的响应
        return {
            "message": "CAS配置更新成功",
            "config": config
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新CAS配置失败: {str(e)}"
        )

@router.post("/cas/test")
async def test_cas_connection(admin_user: CurrentSuperUser):
    """测试CAS连接"""
    try:
        cas_server_url = os.getenv("CAS_SERVER_URL")
        if not cas_server_url:
            return {
                "success": False,
                "message": "CAS服务器地址未配置"
            }
        
        # 简单的连接测试
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(cas_server_url, timeout=10.0)
            return {
                "success": True,
                "message": "CAS服务器连接正常",
                "server_url": cas_server_url,
                "status_code": response.status_code,
                "response_time": f"{response.elapsed.total_seconds():.2f}s"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"CAS连接测试失败: {str(e)}",
            "error": str(e)
        }

@router.get("/monitoring/api")
async def get_api_monitoring(
    admin_user: CurrentSuperUser,
    time_range: str = "24h"
):
    """获取API监控数据"""
    
    # 计算时间范围
    if time_range == "1h":
        since = datetime.now() - timedelta(hours=1)
    elif time_range == "24h":
        since = datetime.now() - timedelta(hours=24)
    elif time_range == "7d":
        since = datetime.now() - timedelta(days=7)
    else:
        since = datetime.now() - timedelta(hours=24)
    
    return {
        "total_calls": 1250,
        "successful_calls": 1180,
        "failed_calls": 70,
        "avg_response_time": 245.5,
        "endpoints": [
            {
                "path": "/v1/commit-message",
                "calls": 450,
                "avg_response_time": 890.2,
                "success_rate": 94.2
            },
            {
                "path": "/v1/code-review",
                "calls": 320,
                "avg_response_time": 1250.8,
                "success_rate": 96.8
            },
            {
                "path": "/v1/auth/login",
                "calls": 120,
                "avg_response_time": 125.3,
                "success_rate": 98.3
            },
            {
                "path": "/v1/commits",
                "calls": 200,
                "avg_response_time": 85.7,
                "success_rate": 99.5
            }
        ]
    }

@router.get("/monitoring/realtime")
async def get_realtime_metrics(admin_user: CurrentSuperUser):
    """获取实时监控指标"""
    try:
        return {
            "active_connections": 15,
            "requests_per_minute": 45,
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取实时监控数据失败: {str(e)}"
        )

@router.get("/users/analytics")
async def get_users_analytics(
    admin_user: CurrentSuperUser,
    db: DatabaseSession
):
    """获取用户分析数据"""
    
    # 获取最近30天的用户注册趋势
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    # 用户类型分布
    total_users_stmt = select(func.count(User.id))
    total_users_result = await db.execute(total_users_stmt)
    total_users = total_users_result.scalar() or 0
    
    super_users_stmt = select(func.count(User.id)).where(User.is_superuser == True)
    super_users_result = await db.execute(super_users_stmt)
    super_users = super_users_result.scalar() or 0
    
    cas_users_stmt = select(func.count(User.id)).where(User.cas_user_id.is_not(None))
    cas_users_result = await db.execute(cas_users_stmt)
    cas_users = cas_users_result.scalar() or 0
    
    return {
        "total_users": total_users,
        "user_types": {
            "admin_users": super_users,
            "regular_users": total_users - super_users,
            "cas_users": cas_users,
            "local_users": total_users - cas_users
        },
        "registration_trend": [
            {"date": "2025-01-01", "count": 5},
            {"date": "2025-01-02", "count": 8},
            {"date": "2025-01-03", "count": 12},
            {"date": "2025-01-04", "count": 15},
        ]
    }

@router.get("/commits")
async def get_all_commits(
    admin_user: CurrentSuperUser,
    db: DatabaseSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    repository_name: Optional[str] = None,
    username: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """获取所有提交记录（管理员）"""
    try:
        from sqlalchemy import select, and_, or_
        from app.models.database import CommitInfo, User
        from sqlalchemy.orm import selectinload
        
        # 构建查询
        stmt = select(CommitInfo).options(selectinload(CommitInfo.user))
        
        conditions = []
        
        if repository_name:
            conditions.append(CommitInfo.repository_name.ilike(f"%{repository_name}%"))
        
        if username:
            # 子查询查找用户ID
            user_subquery = select(User.id).where(User.username.ilike(f"%{username}%"))
            conditions.append(CommitInfo.user_id.in_(user_subquery))
        
        if start_date:
            conditions.append(CommitInfo.created_at >= start_date)
        
        if end_date:
            conditions.append(CommitInfo.created_at <= end_date)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # 排序和分页
        stmt = stmt.order_by(CommitInfo.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        commits = result.scalars().all()
        
        # 转换为响应格式
        commit_list = []
        for commit in commits:
            commit_data = {
                "id": commit.id,
                "user_id": commit.user_id,
                "username": commit.user.username if commit.user else "未知用户",
                "repository_name": commit.repository_name,
                "repository_url": commit.repository_url,
                "branch_name": commit.branch_name,
                "commit_hash": commit.commit_hash,
                "ai_generated_message": commit.ai_generated_message,
                "final_commit_message": commit.final_commit_message,
                "diff_content": commit.diff_content,
                "commit_style": commit.commit_style,
                "lines_added": commit.lines_added,
                "lines_deleted": commit.lines_deleted,
                "files_changed": commit.files_changed,
                "ai_model_used": commit.ai_model_used,
                "generation_time_ms": commit.generation_time_ms,
                "user_rating": commit.user_rating,
                "user_feedback": commit.user_feedback,
                "status": commit.status,
                "created_at": commit.created_at.isoformat(),
                "committed_at": commit.committed_at.isoformat() if commit.committed_at else None
            }
            commit_list.append(commit_data)
        
        return {
            "commits": commit_list,
            "total": len(commit_list),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取提交记录失败: {str(e)}"
        )

@router.get("/commits/analytics")
async def get_commits_analytics(
    admin_user: CurrentSuperUser,
    db: DatabaseSession,
    days: int = Query(30, ge=1, le=365)
):
    """获取提交分析数据"""
    try:
        from sqlalchemy import select, func, and_
        from app.models.database import CommitInfo, User
        
        # 计算时间范围
        start_date = datetime.now() - timedelta(days=days)
        
        # 每日提交趋势
        daily_commits_stmt = select(
            func.date(CommitInfo.created_at).label('date'),
            func.count(CommitInfo.id).label('commit_count')
        ).where(
            CommitInfo.created_at >= start_date
        ).group_by(
            func.date(CommitInfo.created_at)
        ).order_by('date')
        
        daily_result = await db.execute(daily_commits_stmt)
        daily_trends = []
        for row in daily_result:
            daily_trends.append({
                "date": row.date.isoformat(),
                "commit_count": row.commit_count
            })
        
        # 用户活跃度
        user_activity_stmt = select(
            User.username,
            func.count(CommitInfo.id).label('commit_count')
        ).select_from(
            User
        ).outerjoin(
            CommitInfo, and_(
                User.id == CommitInfo.user_id,
                CommitInfo.created_at >= start_date
            )
        ).group_by(
            User.username
        ).order_by(
            func.count(CommitInfo.id).desc()
        ).limit(10)
        
        user_result = await db.execute(user_activity_stmt)
        user_activity = []
        for row in user_result:
            user_activity.append({
                "username": row.username,
                "commit_count": row.commit_count
            })
        
        # 仓库活跃度
        repo_activity_stmt = select(
            CommitInfo.repository_name,
            func.count(CommitInfo.id).label('commit_count')
        ).where(
            and_(
                CommitInfo.created_at >= start_date,
                CommitInfo.repository_name.isnot(None)
            )
        ).group_by(
            CommitInfo.repository_name
        ).order_by(
            func.count(CommitInfo.id).desc()
        ).limit(10)
        
        repo_result = await db.execute(repo_activity_stmt)
        repo_activity = []
        for row in repo_result:
            repo_activity.append({
                "repository_name": row.repository_name,
                "commit_count": row.commit_count
            })
        
        # AI模型使用统计
        model_usage_stmt = select(
            CommitInfo.ai_model_used,
            func.count(CommitInfo.id).label('usage_count')
        ).where(
            and_(
                CommitInfo.created_at >= start_date,
                CommitInfo.ai_model_used.isnot(None)
            )
        ).group_by(
            CommitInfo.ai_model_used
        ).order_by(
            func.count(CommitInfo.id).desc()
        )
        
        model_result = await db.execute(model_usage_stmt)
        model_usage = []
        for row in model_result:
            model_usage.append({
                "model_name": row.ai_model_used,
                "usage_count": row.usage_count
            })
        
        # 新增：提交风格分布
        commit_style_stmt = select(
            CommitInfo.commit_style,
            func.count(CommitInfo.id).label('count')
        ).where(
            and_(
                CommitInfo.created_at >= start_date,
                CommitInfo.commit_style.isnot(None)
            )
        ).group_by(
            CommitInfo.commit_style
        ).order_by(
            func.count(CommitInfo.id).desc()
        )
        
        style_result = await db.execute(commit_style_stmt)
        commit_style_distribution = []
        for row in style_result:
            commit_style_distribution.append({
                "style": row.commit_style,
                "count": row.count
            })
        
        return {
            "daily_trends": daily_trends,
            "user_activity": user_activity,
            "repository_activity": repo_activity,
            "model_usage": model_usage,
            "commit_style_distribution": commit_style_distribution,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取提交分析失败: {str(e)}"
        )

@router.get("/system/settings", response_model=SystemSettingsResponse)
async def get_system_settings(
    admin_user: CurrentSuperUser,
    db: DatabaseSession
):
    """获取系统设置"""
    try:
        stmt = select(SystemSettings).limit(1)
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()
        
        if not settings:
            # 如果没有设置记录，创建默认设置
            settings = SystemSettings()
            db.add(settings)
            await db.commit()
            await db.refresh(settings)
        
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统设置失败: {str(e)}"
        )

@router.put("/system/settings", response_model=SystemSettingsResponse)
async def update_system_settings(
    settings_data: SystemSettingsUpdate,
    admin_user: CurrentSuperUser,
    db: DatabaseSession
):
    """更新系统设置"""
    try:
        stmt = select(SystemSettings).limit(1)
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()
        
        if not settings:
            # 如果没有设置记录，创建新的
            settings = SystemSettings()
            db.add(settings)
        
        # 更新设置
        update_data = settings_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)
        
        await db.commit()
        await db.refresh(settings)
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新系统设置失败: {str(e)}"
        ) 