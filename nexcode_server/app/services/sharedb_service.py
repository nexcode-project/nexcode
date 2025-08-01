import json
import asyncio
import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from pymongo import MongoClient
from pymongo.collection import Collection
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.database import Base
from .document_service import DocumentService
from app.models.database import Document, DocumentVersion

logger = logging.getLogger(__name__)

class ShareDBService:
    """ShareDB 协作服务 - 使用 HTTP 接口实现文档同步"""
    
    def __init__(self, mongo_url: str = "mongodb://localhost:27017", db_name: str = "nexcode_sharedb"):
        """初始化 ShareDB 服务"""
        self.mongo_client = MongoClient(mongo_url)
        self.db = self.mongo_client[db_name]
        self.documents: Collection = self.db.documents
        self.operations: Collection = self.db.operations
        
        # 文档锁，防止并发冲突
        self.doc_locks: Dict[str, asyncio.Lock] = {}
        
        # 创建索引
        self._create_indexes()
    
    def _create_indexes(self):
        """创建必要的索引"""
        try:
            # 文档集合索引
            self.documents.create_index("doc_id", unique=True)
            self.documents.create_index("version")
            
            # 操作集合索引
            self.operations.create_index([("doc_id", 1), ("version", 1)])
            self.operations.create_index("timestamp")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    def _get_doc_lock(self, doc_id: str) -> asyncio.Lock:
        """获取文档锁"""
        if doc_id not in self.doc_locks:
            self.doc_locks[doc_id] = asyncio.Lock()
        return self.doc_locks[doc_id]
    
    async def get_document(self, doc_id: str) -> Dict[str, Any]:
        """获取文档当前状态，确保返回最新版本"""
        try:
            # 使用排序确保获取最新状态
            doc = self.documents.find_one(
                {"doc_id": doc_id},
                sort=[("updated_at", -1)]  # 按更新时间降序排列
            )
            
            if not doc:
                # 检查是否应该从 PostgreSQL 同步内容
                # 这里我们创建一个空文档，让调用方决定是否同步
                doc = {
                    "doc_id": doc_id,
                    "content": "",
                    "version": 0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "last_editor_id": None
                }
                result = self.documents.insert_one(doc)
                doc["_id"] = result.inserted_id
                logger.info(f"Created new empty document {doc_id} in ShareDB")
            
            return {
                "doc_id": doc["doc_id"],
                "content": doc["content"],
                "version": doc["version"],
                "created_at": doc["created_at"].isoformat(),
                "updated_at": doc["updated_at"].isoformat(),
                "last_editor_id": doc.get("last_editor_id")
            }
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get document")
    
    async def apply_operation(self, doc_id: str, operation: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """应用操作到文档"""
        lock = self._get_doc_lock(doc_id)
        async with lock:
            try:
                # 获取当前文档
                current_doc = self.documents.find_one({"doc_id": doc_id})
                if not current_doc:
                    raise HTTPException(status_code=404, detail="Document not found")
                
                # 验证版本
                client_version = operation.get("version", 0)
                current_version = current_doc["version"]
                
                if client_version < current_version:
                    # 需要获取缺失的操作
                    missing_ops = list(self.operations.find({
                        "doc_id": doc_id,
                        "version": {"$gt": client_version}
                    }).sort("version", 1))
                    
                    return {
                        "success": False,
                        "error": "version_mismatch",
                        "current_version": current_version,
                        "missing_operations": [self._serialize_operation(op) for op in missing_ops]
                    }
                
                # 应用操作
                new_content = self._apply_text_operation(current_doc["content"], operation)
                new_version = current_version + 1
                
                # 更新文档
                self.documents.update_one(
                    {"doc_id": doc_id},
                    {
                        "$set": {
                            "content": new_content,
                            "version": new_version,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                # 保存操作记录
                op_record = {
                    "doc_id": doc_id,
                    "version": new_version,
                    "operation": operation,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow()
                }
                self.operations.insert_one(op_record)
                
                return {
                    "success": True,
                    "version": new_version,
                    "content": new_content,
                    "operation_id": str(op_record["_id"])
                }
                
            except Exception as e:
                logger.error(f"Failed to apply operation to {doc_id}: {e}")
                raise HTTPException(status_code=500, detail="Failed to apply operation")
    
    def _apply_text_operation(self, content: str, operation: Dict[str, Any]) -> str:
        """应用文本操作"""
        op_type = operation.get("type")
        
        if op_type == "insert":
            position = operation.get("position", 0)
            text = operation.get("text", "")
            return content[:position] + text + content[position:]
        
        elif op_type == "delete":
            position = operation.get("position", 0)
            length = operation.get("length", 0)
            return content[:position] + content[position + length:]
        
        elif op_type == "replace":
            position = operation.get("position", 0)
            length = operation.get("length", 0)
            text = operation.get("text", "")
            return content[:position] + text + content[position + length:]
        
        elif op_type == "full_update":
            return operation.get("content", content)
        
        else:
            logger.warning(f"Unknown operation type: {op_type}")
            return content
    
    def _serialize_operation(self, op_record: Dict[str, Any]) -> Dict[str, Any]:
        """序列化操作记录"""
        return {
            "doc_id": op_record["doc_id"],
            "version": op_record["version"],
            "operation": op_record["operation"],
            "user_id": op_record["user_id"],
            "timestamp": op_record["timestamp"].isoformat()
        }
    
    async def get_operations_since(self, doc_id: str, since_version: int) -> List[Dict[str, Any]]:
        """获取指定版本之后的所有操作"""
        try:
            operations = list(self.operations.find({
                "doc_id": doc_id,
                "version": {"$gt": since_version}
            }).sort("version", 1))
            
            return [self._serialize_operation(op) for op in operations]
        except Exception as e:
            logger.error(f"Failed to get operations for {doc_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get operations")
    
    async def sync_document(self, doc_id: str, version: int, content: str, 
                           user_id: int, create_version: bool = False, db_session: AsyncSession = None) -> dict:
        """同步文档到ShareDB，可选创建PostgreSQL版本快照"""
        lock = self._get_doc_lock(doc_id)
        async with lock:
            try:
                # ShareDB 版本号始终递增（用于协作同步检测）
                new_sharedb_version = version + 1
                
                # 1. 更新 ShareDB (MongoDB) 中的文档内容
                result = self.documents.update_one(
                    {"doc_id": doc_id},
                    {
                        "$set": {
                            "content": content,
                            "version": new_sharedb_version,  # ShareDB 版本总是递增
                            "updated_at": datetime.utcnow(),
                            "last_editor_id": user_id
                        }
                    },
                    upsert=True
                )
                
                # 2. 记录操作历史
                operation = {
                    "doc_id": doc_id,
                    "version": new_sharedb_version,
                    "content": content,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow(),
                    "operation_type": "sync"
                }
                self.operations.insert_one(operation)
                
                # 3. 可选：在PostgreSQL中创建版本快照（用于长期存储和恢复）
                if create_version and db_session:
                    await self._create_version_snapshot(
                        db_session, doc_id, content, user_id, new_sharedb_version
                    )
                
                logger.info(f"Document {doc_id} synced: ShareDB v{new_sharedb_version}, PostgreSQL snapshot: {create_version}")
                
                return {
                    "success": True,
                    "content": content,
                    "version": new_sharedb_version,  # 返回新的 ShareDB 版本号
                    "operations": []
                }
            except Exception as e:
                logger.error(f"Sync document failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "content": content,
                    "version": version,
                    "operations": []
                }
    
    async def _create_version_snapshot(self, db_session: AsyncSession, doc_id: str, 
                                     content: str, user_id: int, version: int):
        """在PostgreSQL中创建版本快照（仅用于长期存储）- 只有内容真正变化时才创建"""
        try:
            from sqlalchemy import select, func, desc
            
            # 获取文档元数据
            stmt = select(Document).where(Document.id == int(doc_id))
            result = await db_session.execute(stmt)
            document = result.scalar_one_or_none()
            
            if not document:
                logger.warning(f"Document {doc_id} not found, skipping snapshot")
                return
            
            # 计算新内容的哈希值
            new_content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # 检查最新版本的内容哈希
            latest_version_stmt = (
                select(DocumentVersion.content_hash)
                .where(DocumentVersion.document_id == int(doc_id))
                .order_by(desc(DocumentVersion.version_number))
                .limit(1)
            )
            latest_result = await db_session.execute(latest_version_stmt)
            latest_hash = latest_result.scalar()
            
            # 如果内容哈希相同，说明内容没有变化，跳过创建版本
            if latest_hash == new_content_hash:
                logger.info(f"Document {doc_id} content unchanged (hash: {new_content_hash}), skipping snapshot")
                return
                
            # 内容有变化，创建新版本快照
            snapshot = DocumentVersion(
                document_id=int(doc_id),
                version_number=version,
                title=document.title,
                content=content,
                content_hash=new_content_hash,
                changed_by=user_id,
                change_description=f"自动快照 - 版本 {version}",
            )
            db_session.add(snapshot)
            await db_session.commit()
            logger.info(f"✅ Version snapshot created for document {doc_id}, version {version} (content changed)")
            
        except Exception as e:
            logger.warning(f"Failed to create version snapshot: {e}")

    async def restore_version(self, doc_id: str, target_version_number: int, user_id: int, db_session: AsyncSession = None) -> Dict[str, Any]:
        """从 PostgreSQL 版本历史恢复到指定版本，并同步到 ShareDB"""
        try:
            from sqlalchemy import select
            
            if not db_session:
                raise ValueError("Database session is required for version restoration")
            
            # 从 PostgreSQL 获取目标版本内容
            version_stmt = select(DocumentVersion).where(
                DocumentVersion.document_id == int(doc_id),
                DocumentVersion.version_number == target_version_number
            )
            result = await db_session.execute(version_stmt)
            target_version = result.scalar_one_or_none()
            
            if not target_version:
                return {
                    "success": False,
                    "error": f"Version {target_version_number} not found"
                }
            
            # 获取当前 ShareDB 版本
            current_doc = self.documents.find_one({"doc_id": doc_id})
            current_sharedb_version = current_doc["version"] if current_doc else 0
            
            # 更新 ShareDB 内容
            new_sharedb_version = current_sharedb_version + 1
            self.documents.update_one(
                {"doc_id": doc_id},
                {
                    "$set": {
                        "content": target_version.content,
                        "version": new_sharedb_version,
                        "updated_at": datetime.utcnow(),
                        "last_editor_id": user_id
                    }
                },
                upsert=True
            )
            
            # 记录恢复操作
            operation = {
                "doc_id": doc_id,
                "version": new_sharedb_version,
                "content": target_version.content,
                "user_id": user_id,
                "timestamp": datetime.utcnow(),
                "operation_type": "version_restore",
                "restored_from_version": target_version_number
            }
            self.operations.insert_one(operation)
            
            logger.info(f"✅ Version restored in ShareDB: {doc_id} -> version {target_version_number} (ShareDB v{new_sharedb_version})")
            
            return {
                "success": True,
                "content": target_version.content,
                "version": new_sharedb_version,
                "restored_from_version": target_version_number
            }
            
        except Exception as e:
            logger.error(f"Failed to restore version: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def close(self):
        """关闭服务"""
        if self.mongo_client:
            self.mongo_client.close()

# 全局 ShareDB 服务实例
sharedb_service: Optional[ShareDBService] = None

def get_sharedb_service() -> ShareDBService:
    """获取 ShareDB 服务实例"""
    global sharedb_service
    if sharedb_service is None:
        sharedb_service = ShareDBService()
    return sharedb_service 