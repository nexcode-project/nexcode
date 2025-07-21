from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, DatabaseSession
from app.services.document_service import document_service
from app.services.permission_service import permission_service
from app.services.auth_service import auth_service
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


def user_to_dict(user):
    return (
        {"id": user.id, "username": user.username, "email": user.email}
        if user
        else None
    )


@router.get("/", response_model=DocumentListResult)
async def get_user_documents(
    current_user: CurrentUser,
    db: DatabaseSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
):
    """获取用户文档列表"""
    result = await document_service.get_user_documents(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
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
    document = await document_service.get_document(
        db=db, document_id=document_id, user_id=current_user.id
    )
    document.collaborators = []

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
        owner=(
            UserInfo.model_validate(user_to_dict(document.owner))
            if document.owner
            else None
        ),
        collaborators=[],
        user_permission=PermissionLevel.OWNER,  # 你的权限逻辑
    )

    # 设置用户权限
    if document.owner_id == current_user.id:
        response_data.user_permission = PermissionLevel.OWNER
    else:
        for collab in document.collaborators:
            if collab.user_id == current_user.id:
                response_data.user_permission = collab.permission
                break

    return response_data


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_data: DocumentUpdate,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """更新文档"""
    document = await document_service.update_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
        title=document_data.title,
        content=document_data.content,
        category=document_data.category,
        tags=document_data.tags,
        change_description=document_data.change_description,
    )

    response_data = DocumentResponse.model_validate(document)

    # 设置用户权限
    if document.owner_id == current_user.id:
        response_data.user_permission = PermissionLevel.OWNER
    else:
        for collab in document.collaborators:
            if collab.user_id == current_user.id:
                response_data.user_permission = collab.permission
                break

    return response_data


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int, current_user: CurrentUser, db: DatabaseSession
):
    """删除文档"""
    await document_service.delete_document(
        db=db, document_id=document_id, user_id=current_user.id
    )


# 协作者管理
@router.get("/{document_id}/collaborators", response_model=List[CollaboratorResponse])
async def get_document_collaborators(
    document_id: int, current_user: CurrentUser, db: DatabaseSession
):
    """获取文档协作者列表"""
    collaborators = await permission_service.get_document_collaborators(
        db=db, document_id=document_id, user_id=current_user.id
    )

    return [CollaboratorResponse.model_validate(collab) for collab in collaborators]


@router.post(
    "/{document_id}/collaborators",
    response_model=CollaboratorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_document_collaborator(
    document_id: int,
    collaborator_data: CollaboratorAdd,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """添加文档协作者"""
    # 根据邮箱查找用户
    user = await auth_service.get_user_by_email(db, collaborator_data.user_email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    collaborator = await permission_service.add_collaborator(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
        collaborator_user_id=user.id,
        permission=collaborator_data.permission,
    )

    return CollaboratorResponse.model_validate(collaborator)


@router.put(
    "/{document_id}/collaborators/{collaborator_user_id}",
    response_model=CollaboratorResponse,
)
async def update_collaborator_permission(
    document_id: int,
    collaborator_user_id: int,
    permission_data: CollaboratorUpdate,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """更新协作者权限"""
    collaborator = await permission_service.update_collaborator_permission(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
        collaborator_user_id=collaborator_user_id,
        new_permission=permission_data.permission,
    )

    return CollaboratorResponse.model_validate(collaborator)


@router.delete(
    "/{document_id}/collaborators/{collaborator_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_document_collaborator(
    document_id: int,
    collaborator_user_id: int,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """移除文档协作者"""
    await permission_service.remove_collaborator(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
        collaborator_user_id=collaborator_user_id,
    )


# 版本管理
@router.get("/{document_id}/versions", response_model=List[DocumentVersionResponse])
async def get_document_versions(
    document_id: int,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """获取文档版本历史"""
    versions = await document_service.get_document_versions(
        db=db, document_id=document_id, user_id=current_user.id
    )

    return [DocumentVersionResponse.model_validate(version) for version in versions]


@router.post("/{document_id}/revert/{version_number}", response_model=DocumentResponse)
async def revert_document_to_version(
    document_id: int,
    version_number: int,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """回滚文档到指定版本"""
    document = await document_service.revert_to_version(
        db=db,
        document_id=document_id,
        version_number=version_number,
        user_id=current_user.id,
    )

    response_data = DocumentResponse.model_validate(document)

    # 设置用户权限
    if document.owner_id == current_user.id:
        response_data.user_permission = PermissionLevel.OWNER
    else:
        for collab in document.collaborators:
            if collab.user_id == current_user.id:
                response_data.user_permission = collab.permission
                break

    return response_data
