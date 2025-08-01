from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import difflib

from app.core.dependencies import CurrentUser, DatabaseSession
from app.services.document_service import document_service
from app.services.permission_service import permission_service
from app.services.auth_service import auth_service
from app.services.document_storage_service import document_storage_service
from app.services.sharedb_service import get_sharedb_service
from app.models.document_schemas import (
    DocumentCreate,
    DocumentListItem,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    DocumentListResult,
    DocumentVersionResponse,
    CollaboratorAdd,
    CollaboratorUpdate,
    CollaboratorResponse,
    PermissionLevel,
    DocumentSearchQuery,
    UserInfo,
)


class VersionSnapshotRequest(BaseModel):
    description: str
    content: Optional[str] = None  # 添加content字段


class VersionDiffResponse(BaseModel):
    from_version: int
    to_version: int
    diff_html: str
    diff_text: str


class VersionRestoreResponse(BaseModel):
    success: bool
    content: str
    version_number: int
    message: str


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document_data: DocumentCreate, current_user: CurrentUser, db: DatabaseSession
):
    """创建文档"""
    document = await document_service.create_document(
        db=db,
        user_id=current_user.id,
        title=document_data.title,
        content=document_data.content,
        category=document_data.category,
        tags=document_data.tags,
        organization_id=document_data.organization_id,
    )
    user_info = user_to_dict(current_user)
    # 设置用户权限信息
    # response_data = DocumentResponse.model_validate(document)
    response_data = DocumentResponse(
        id=document.id,
        title=document.title,
        content=document.content,
        category=document.category,
        tags=document.tags,
        status=document.status,
        version=document.version,
        created_at=document.created_at,
        updated_at=document.updated_at,
        owner=user_info,
        collaborators=[],
        user_permission=PermissionLevel.OWNER,
    )
    response_data.user_permission = PermissionLevel.OWNER
    return response_data


@router.get("/", response_model=DocumentListResult)
async def get_user_documents(
    current_user: CurrentUser,
    db: DatabaseSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    organization_id: Optional[int] = Query(None),
):
    """获取用户文档列表"""
    result = await document_service.get_user_documents(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        organization_id=organization_id,
        search=search,
        category=category,
    )

    # 转换为响应格式
    documents = []
    for doc in result["documents"]:
        doc_response = DocumentListItem(
            id=doc.id,
            title=doc.title,
            content=doc.content,
            category=doc.category,
            tags=doc.tags,
            status=doc.status,
            version=doc.version,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            owner=(
                UserInfo.model_validate(user_to_dict(doc.owner)) if doc.owner else None
            ),
            collaborators=[],
            user_permission=PermissionLevel.READER,  # 你的权限逻辑
        )
        documents.append(doc_response)

    return DocumentListResult(
        documents=documents,
        total=result["total"],
        skip=result["skip"],
        limit=result["limit"],
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int, current_user: CurrentUser, db: DatabaseSession
):
    """获取文档详情"""
    # 获取 ShareDB 服务
    sharedb_service = get_sharedb_service()
    
    document_data = await document_service.get_document(
        db, document_id, current_user.id, sharedb_service
    )
    
    # document_data 现在是字典格式，包含来自 ShareDB 的内容
    return DocumentResponse(
        id=document_data["id"],
        title=document_data["title"],
        content=document_data["content"],  # 来自 ShareDB
        category=document_data["category"],
        tags=document_data["tags"],
        version=document_data["version"],  # 来自 ShareDB
        owner=user_to_dict(document_data["owner"]) if document_data["owner"] else None,
        collaborators=[],
        created_at=document_data["created_at"],
        updated_at=document_data["updated_at"],
        status=document_data["status"]
    )


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_data: DocumentUpdate,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """更新文档"""
    document = await document_service.update_document(
        db=db,  # 全部使用关键字参数
        document_id=document_id,
        user_id=current_user.id,
        title=document_data.title,
        content=document_data.content,
        category=document_data.category,
        tags=document_data.tags,
        change_description=document_data.change_description,
        create_version=document_data.create_version,  # 使用请求中的参数
    )
    
    # 转换为响应格式 - 简化处理，避免异步关系访问
    user_info = user_to_dict(document.owner) if document.owner else None
    collaborators = []
    
    # 暂时跳过协作者信息的加载，避免异步问题
    # for collab in document.collaborators:
    #     collaborator_response = CollaboratorResponse(
    #         user=UserInfo.model_validate(user_to_dict(collab.user)),
    #         permission=collab.permission,
    #         added_at=collab.added_at,
    #     )
    #     collaborators.append(collaborator_response)
    
    response_data = DocumentResponse(
        id=document.id,
        title=document.title,
        content=document.content,
        category=document.category,
        tags=document.tags,
        status=document.status,
        version=document.version,
        created_at=document.created_at,
        updated_at=document.updated_at,
        owner=UserInfo.model_validate(user_info) if user_info else None,
        collaborators=collaborators,
        user_permission=PermissionLevel.READER,  # 根据实际权限设置
    )
    
    return response_data


@router.delete("/{document_id}")
async def delete_document(
    document_id: int, current_user: CurrentUser, db: DatabaseSession
):
    """删除文档"""
    await document_service.delete_document(db, document_id, current_user.id)
    return {"message": "文档已删除"}


# 新增的文档存储相关端点

@router.get("/{document_id}/versions")
async def get_document_versions(
    document_id: int, 
    current_user: CurrentUser, 
    db: DatabaseSession,
    limit: int = Query(10, ge=1, le=50)
):
    """获取文档版本历史"""
    # 检查权限
    has_permission = await permission_service.check_document_permission(
        db, current_user.id, document_id, PermissionLevel.READER
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此文档"
        )
    
    versions = await document_storage_service.get_document_versions(document_id, limit)
    
    version_responses = []
    for version in versions:
        # 获取用户信息
        user = await auth_service.get_user_by_id(db, version.changed_by)
        if not user:
            # 如果用户不存在，创建一个默认的用户信息
            user_info = UserInfo(
                id=version.changed_by,
                username="未知用户",
                email=None
            )
        else:
            user_info = UserInfo(
                id=user.id,
                username=user.username,
                email=user.email
            )
        
        version_response = DocumentVersionResponse(
            id=version.id,
            version_number=version.version_number,
            title=version.title,
            content=version.content,
            change_description=version.change_description,
            created_at=version.created_at,
            changed_by=user_info
        )
        version_responses.append(version_response)
    
    return {"versions": version_responses}


@router.post("/{document_id}/versions")
async def create_version_snapshot(
    document_id: int,
    request: VersionSnapshotRequest,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """创建版本快照"""
    # 检查权限
    has_permission = await permission_service.check_document_permission(
        db, current_user.id, document_id, PermissionLevel.EDITOR
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限编辑此文档"
        )
    
    # 如果请求中包含内容，使用提供的内容创建版本
    if request.content is not None:
        await document_storage_service.create_version_snapshot_with_content(
            document_id, current_user.id, request.description, request.content
        )
    else:
        await document_storage_service.create_version_snapshot(
            document_id, current_user.id, request.description
        )
    
    return {"message": "版本快照已创建"}


@router.post("/{document_id}/versions/{version_number}/restore", response_model=VersionRestoreResponse)
async def restore_version(
    document_id: int,
    version_number: int,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """恢复到指定版本"""
    # 检查权限
    has_permission = await permission_service.check_document_permission(
        db, current_user.id, document_id, PermissionLevel.EDITOR
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限编辑此文档"
        )
    
    result = await document_storage_service.restore_version_with_content(
        document_id, version_number, current_user.id
    )
    
    if result and result.get("success"):
        # 同步到 ShareDB
        try:
            from app.services.sharedb_service import get_sharedb_service
            sharedb_service = get_sharedb_service()
            await sharedb_service.sync_document(
                doc_id=str(document_id),
                version=result["new_version"],
                content=result["content"],
                user_id=current_user.id,
                create_version=False,  # 不创建新版本，因为已经在 PostgreSQL 中创建了
                db_session=db
            )
            print(f"✅ 版本恢复已同步到 ShareDB: document_id={document_id}, version={result['new_version']}")
        except Exception as e:
            print(f"⚠️ 同步到 ShareDB 失败: {e}")
            # 不抛出异常，因为 PostgreSQL 恢复已经成功
        
        return VersionRestoreResponse(
            success=True,
            content=result["content"],
            version_number=result["new_version"],
            message=f"已恢复到版本 {version_number}"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="版本不存在"
        )


@router.get("/{document_id}/versions/{from_version}/diff/{to_version}", response_model=VersionDiffResponse)
async def get_version_diff(
    document_id: int,
    from_version: int,
    to_version: int,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """获取两个版本之间的差异"""
    # 检查权限
    has_permission = await permission_service.check_document_permission(
        db, current_user.id, document_id, PermissionLevel.READER
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限查看版本差异"
        )
    
    # 获取两个版本的内容
    from_content = await document_storage_service.get_version_content(document_id, from_version)
    to_content = await document_storage_service.get_version_content(document_id, to_version)
    
    if from_content is None or to_content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="指定版本不存在"
        )
    
    # 生成文本差异
    diff_lines = list(difflib.unified_diff(
        from_content.splitlines(keepends=True),
        to_content.splitlines(keepends=True),
        fromfile=f"版本 {from_version}",
        tofile=f"版本 {to_version}",
        n=3
    ))
    diff_text = ''.join(diff_lines)
    
    # 生成HTML差异
    html_diff = difflib.HtmlDiff()
    diff_html = html_diff.make_file(
        from_content.splitlines(),
        to_content.splitlines(),
        fromdesc=f"版本 {from_version}",
        todesc=f"版本 {to_version}",
        context=True,
        numlines=2
    )
    
    return VersionDiffResponse(
        from_version=from_version,
        to_version=to_version,
        diff_html=diff_html,
        diff_text=diff_text
    )


@router.get("/{document_id}/statistics")
async def get_document_statistics(
    document_id: int,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """获取文档统计信息"""
    # 检查权限
    has_permission = await permission_service.check_document_permission(
        db, current_user.id, document_id, PermissionLevel.READER
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此文档"
        )
    
    stats = await document_storage_service.get_document_statistics(document_id)
    return stats


@router.post("/{document_id}/operations/cleanup")
async def cleanup_old_operations(
    document_id: int,
    current_user: CurrentUser,
    db: DatabaseSession,
    keep_count: int = Query(100, ge=10, le=1000)
):
    """清理旧的操作记录"""
    # 检查权限（只有文档所有者可以清理）
    document = await document_service.get_document(db, document_id, current_user.id)
    if document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="只有文档所有者可以清理操作记录"
        )
    
    await document_storage_service.cleanup_old_operations(document_id, keep_count)
    return {"message": f"已清理旧操作记录，保留 {keep_count} 条最新记录"}


def user_to_dict(user):
    """将用户对象转换为字典"""
    if not user:
        return None
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }
