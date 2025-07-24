import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from pymongo import MongoClient
from pymongo.collection import Collection
from fastapi import HTTPException

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
        """获取文档当前状态"""
        try:
            doc = self.documents.find_one({"doc_id": doc_id})
            if not doc:
                # 创建新文档
                doc = {
                    "doc_id": doc_id,
                    "content": "",
                    "version": 0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                self.documents.insert_one(doc)
            
            return {
                "doc_id": doc["doc_id"],
                "content": doc["content"],
                "version": doc["version"],
                "created_at": doc["created_at"].isoformat(),
                "updated_at": doc["updated_at"].isoformat()
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
    
    async def sync_document(self, doc_id: str, client_version: int, client_content: str, user_id: int) -> Dict[str, Any]:
        """同步文档状态"""
        lock = self._get_doc_lock(doc_id)
        async with lock:
            try:
                # 获取当前文档状态
                current_doc = self.documents.find_one({"doc_id": doc_id})
                if not current_doc:
                    # 创建新文档
                    doc = {
                        "doc_id": doc_id,
                        "content": client_content,
                        "version": 1,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    self.documents.insert_one(doc)
                    
                    return {
                        "success": True,
                        "version": 1,
                        "content": client_content,
                        "operations": [],
                        "error": None
                    }
                
                current_version = current_doc["version"]
                current_content = current_doc["content"]
                
                if client_version == current_version:
                    if client_content != current_content:
                        # 客户端有未同步的更改
                        new_version = current_version + 1
                        self.documents.update_one(
                            {"doc_id": doc_id},
                            {
                                "$set": {
                                    "content": client_content,
                                    "version": new_version,
                                    "updated_at": datetime.utcnow()
                                }
                            }
                        )
                        
                        # 记录操作
                        op_record = {
                            "doc_id": doc_id,
                            "version": new_version,
                            "operation": {
                                "type": "full_update",
                                "content": client_content
                            },
                            "user_id": user_id,
                            "timestamp": datetime.utcnow()
                        }
                        self.operations.insert_one(op_record)
                        
                        return {
                            "success": True,
                            "version": new_version,
                            "content": client_content,
                            "operations": [],
                            "error": None
                        }
                    else:
                        # 内容一致，无需更新
                        return {
                            "success": True,
                            "version": current_version,
                            "content": current_content,
                            "operations": [],
                            "error": None
                        }
                
                elif client_version < current_version:
                    # 获取客户端缺失的操作
                    missing_operations = await self.get_operations_since(doc_id, client_version)
                    
                    return {
                        "success": True,
                        "version": current_version,
                        "content": current_content,
                        "operations": missing_operations,
                        "error": None
                    }
                
                else:
                    # 客户端版本超前，这不应该发生
                    logger.warning(f"Client version {client_version} ahead of server version {current_version} for doc {doc_id}")
                    return {
                        "success": False,
                        "error": "invalid_version",
                        "version": current_version,
                        "content": current_content,
                        "operations": []
                    }
                    
            except Exception as e:
                logger.error(f"Failed to sync document {doc_id}: {e}")
                return {
                    "success": False,
                    "error": f"同步失败: {str(e)}",
                    "version": 0,
                    "content": "",
                    "operations": []
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