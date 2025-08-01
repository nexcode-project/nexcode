from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, List, Optional, Annotated
import logging
from pydantic import BaseModel
from datetime import datetime, timedelta
import hashlib

from app.core.dependencies import get_current_user, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.sharedb_service import get_sharedb_service, ShareDBService
from app.models.database import User
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter()

class DocumentSyncRequest(BaseModel):
    doc_id: str
    version: int
    content: str
    create_version: bool = True  # 新增参数

class OperationRequest(BaseModel):
    doc_id: str
    operation: Dict[str, Any]

class DocumentResponse(BaseModel):
    doc_id: str
    content: str
    version: int
    created_at: str
    updated_at: str

class SyncResponse(BaseModel):
    success: bool
    version: int
    content: str
    operations: List[Dict[str, Any]]
    error: Optional[str] = None

class OperationResponse(BaseModel):
    success: bool
    version: Optional[int] = None
    content: Optional[str] = None
    operation_id: Optional[str] = None
    error: Optional[str] = None
    current_version: Optional[int] = None
    missing_operations: List[Dict[str, Any]] = []

@router.get("/ping")
async def ping():
    """健康检查端点"""
    return {"status": "ok", "message": "ShareDB service is running"}

@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    sharedb: ShareDBService = Depends(get_sharedb_service)
):
    """获取文档当前状态"""
    try:
        result = await sharedb.get_document(doc_id)
        return DocumentResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document")

@router.post("/documents/sync", response_model=SyncResponse)
async def sync_document(
    request: DocumentSyncRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Any, Depends(get_db)]
):
    """同步文档，智能版本控制"""
    try:
        # 调用 ShareDB 服务同步
        result = await get_sharedb_service().sync_document(
            doc_id=request.doc_id,
            version=request.version,
            content=request.content,
            user_id=current_user.id,
            create_version=request.create_version,
            db_session=db
        )
        
        # 返回 SyncResponse 对象
        return SyncResponse(**result)
    except Exception as e:
        logger.error(f"Sync document failed: {e}")
        return SyncResponse(
            success=False,
            error=str(e),
            content=request.content,
            version=request.version,
            operations=[]  # 添加缺失的 operations 字段
        )

@router.post("/documents/operations", response_model=OperationResponse)
async def apply_operation(
    request: OperationRequest,
    current_user: User = Depends(get_current_user),
    sharedb: ShareDBService = Depends(get_sharedb_service)
):
    """应用操作到文档"""
    try:
        result = await sharedb.apply_operation(
            doc_id=request.doc_id,
            operation=request.operation,
            user_id=current_user.id
        )
        
        # 确保响应格式正确
        operation_response = OperationResponse(
            success=result.get("success", True),
            version=result.get("version"),
            content=result.get("content"),
            operation_id=result.get("operation_id"),
            error=result.get("error"),
            current_version=result.get("current_version"),
            missing_operations=result.get("missing_operations", [])
        )
        
        return operation_response
    except Exception as e:
        logger.error(f"Failed to apply operation to {request.doc_id}: {e}")
        return OperationResponse(
            success=False,
            error=f"操作失败: {str(e)}"
        )

@router.get("/documents/{doc_id}/operations")
async def get_operations(
    doc_id: str,
    since_version: int = 0,
    current_user: User = Depends(get_current_user),
    sharedb: ShareDBService = Depends(get_sharedb_service)
):
    """获取指定版本之后的操作"""
    try:
        operations = await sharedb.get_operations_since(doc_id, since_version)
        return {
            "success": True,
            "operations": operations,
            "doc_id": doc_id,
            "since_version": since_version
        }
    except Exception as e:
        logger.error(f"Failed to get operations for {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get operations")

@router.post("/documents/{doc_id}/snapshot")
async def create_snapshot(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    sharedb: ShareDBService = Depends(get_sharedb_service)
):
    """创建文档快照（可用于备份或版本控制）"""
    try:
        document = await sharedb.get_document(doc_id)
        
        # 这里可以添加快照逻辑，比如保存到另一个集合
        # 目前简单返回当前文档状态
        return {
            "success": True,
            "snapshot": document,
            "created_by": current_user.id,
            "created_at": document["updated_at"]
        }
    except Exception as e:
        logger.error(f"Failed to create snapshot for {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create snapshot")

@router.get("/documents/{doc_id}/status")
async def get_document_status(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    sharedb: ShareDBService = Depends(get_sharedb_service)
):
    """获取文档状态信息"""
    try:
        document = await sharedb.get_document(doc_id)
        
        # 获取最近的操作
        recent_operations = await sharedb.get_operations_since(doc_id, max(0, document["version"] - 10))
        
        return {
            "success": True,
            "document": document,
            "recent_operations_count": len(recent_operations),
            "last_operations": recent_operations[-5:] if recent_operations else []
        }
    except Exception as e:
        logger.error(f"Failed to get document status for {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document status")

@router.post("/documents/{doc_id}/restore/{version_number}")
async def restore_document_version(
    doc_id: str,
    version_number: int,
    current_user: User = Depends(get_current_user),
    sharedb: ShareDBService = Depends(get_sharedb_service),
    db: AsyncSession = Depends(get_db)
):
    """从 PostgreSQL 版本历史恢复到指定版本"""
    try:
        result = await sharedb.restore_version(
            doc_id=doc_id,
            target_version_number=version_number,
            user_id=current_user.id,
            db_session=db
        )
        
        if result["success"]:
            return {
                "success": True,
                "content": result["content"],
                "version": result["version"],
                "restored_from_version": result["restored_from_version"],
                "message": f"已恢复到版本 {version_number}"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=result["error"]
            )
    except Exception as e:
        logger.error(f"Failed to restore version {version_number} for {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to restore version") 