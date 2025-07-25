"""
文档存储服务
提供文档内容的数据库存储、版本管理和操作记录功能
"""

import asyncio
import hashlib
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime

from app.core.database import get_db
from app.models.database import (
    Document, 
    DocumentVersion, 
    DocumentOperation, 
    OperationType,
    DocumentStatus
)


class DocumentStorageService:
    """文档存储服务"""
    
    def __init__(self):
        self.save_queue = asyncio.Queue()
        self.save_task = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """确保服务已初始化"""
        if not self._initialized:
            try:
                self._start_background_save()
                self._initialized = True
            except RuntimeError:
                # 如果没有运行的事件循环，延迟初始化
                pass
    
    def _start_background_save(self):
        """启动后台保存任务"""
        if self.save_task is None or self.save_task.done():
            self.save_task = asyncio.create_task(self._background_save_worker())
    
    async def _background_save_worker(self):
        """后台保存工作器"""
        while True:
            try:
                # 等待保存请求
                save_request = await self.save_queue.get()
                
                if save_request is None:  # 停止信号
                    break
                
                document_id, user_id, content, operation = save_request
                
                # 执行保存
                await self._save_document_content(document_id, user_id, content)
                
                # 如果有操作记录，也保存
                if operation:
                    await self._save_operation(document_id, user_id, operation)
                
                # 标记任务完成
                self.save_queue.task_done()
                
            except Exception as e:
                print(f"❌ 后台保存失败: {e}")
                import traceback
                traceback.print_exc()
    
    async def save_content(self, document_id: int, user_id: int, content: str, operation: Optional[Dict] = None):
        """保存文档内容（异步）"""
        self._ensure_initialized()
        await self.save_queue.put((document_id, user_id, content, operation))
    
    async def _save_document_content(self, document_id: int, user_id: int, content: str):
        """保存文档内容到数据库"""
        try:
            async for db in get_db():
                # 获取当前文档
                stmt = select(Document).where(Document.id == document_id)
                result = await db.execute(stmt)
                document = result.scalar_one_or_none()
                
                if not document:
                    print(f"❌ 文档 {document_id} 不存在")
                    return
                
                # 检查内容是否有变化
                if document.content == content:
                    print(f"📝 文档 {document_id} 内容无变化，跳过保存")
                    return
                
                # 保存旧版本
                content_hash = hashlib.md5(document.content.encode()).hexdigest()
                old_version = DocumentVersion(
                    document_id=document_id,
                    version_number=document.version,
                    title=document.title,
                    content=document.content,
                    content_hash=content_hash,  # 添加内容哈希
                    changed_by=document.last_editor_id or document.owner_id,
                    change_description=f"自动保存 - 版本 {document.version}"
                )
                db.add(old_version)
                
                # 更新文档内容
                document.content = content
                document.version += 1
                document.last_editor_id = user_id
                document.updated_at = datetime.utcnow()
                
                await db.commit()
                await db.refresh(document)  # 刷新对象以获取最新数据
                print(f"✅ 文档内容已保存: document_id={document_id}, version={document.version}, content_length={len(content)}")
                break
                
        except Exception as e:
            print(f"❌ 保存文档内容失败: {e}")
            import traceback
            traceback.print_exc()
    
    async def _save_operation(self, document_id: int, user_id: int, operation: Dict):
        """保存操作记录到数据库"""
        try:
            async for db in get_db():
                # 创建操作记录
                operation_record = DocumentOperation(
                    document_id=document_id,
                    user_id=user_id,
                    operation_id=operation.get("id", f"op_{document_id}_{user_id}_{asyncio.get_event_loop().time()}"),
                    sequence_number=operation.get("sequence", 0),
                    operation_type=OperationType.INSERT if operation.get("type") == "insert" else OperationType.DELETE,
                    start_position=operation.get("position", 0),
                    end_position=operation.get("position", 0) + len(operation.get("content", "")),
                    content=operation.get("content", "")
                )
                
                db.add(operation_record)
                await db.commit()
                print(f"✅ 操作已保存: document_id={document_id}, user_id={user_id}, operation_id={operation_record.operation_id}")
                break
                
        except Exception as e:
            print(f"❌ 保存操作记录失败: {e}")
            import traceback
            traceback.print_exc()

    async def get_document_versions(self, document_id: int, limit: int = 10) -> List[DocumentVersion]:
        """获取文档版本历史"""
        try:
            async for db in get_db():
                stmt = (
                    select(DocumentVersion)
                    .where(DocumentVersion.document_id == document_id)
                    .order_by(desc(DocumentVersion.version_number))
                    .limit(limit)
                )
                result = await db.execute(stmt)
                versions = result.scalars().all()
                return list(versions)
        except Exception as e:
            print(f"❌ 获取版本历史失败: {e}")
            return []

    async def create_version_snapshot(self, document_id: int, user_id: int, description: str):
        """创建版本快照 - 只有内容真正变化时才创建"""
        try:
            async for db in get_db():
                # 获取当前文档
                stmt = select(Document).where(Document.id == document_id)
                result = await db.execute(stmt)
                document = result.scalar_one_or_none()
                
                if not document:
                    return False
                
                # 计算当前内容的哈希值
                current_content_hash = hashlib.md5(document.content.encode()).hexdigest()
                
                # 检查最新版本的内容哈希
                latest_version_stmt = (
                    select(DocumentVersion.content_hash)
                    .where(DocumentVersion.document_id == document_id)
                    .order_by(desc(DocumentVersion.version_number))
                    .limit(1)
                )
                latest_result = await db.execute(latest_version_stmt)
                latest_hash = latest_result.scalar()
                
                # 如果内容哈希相同，说明内容没有变化，跳过创建版本
                if latest_hash == current_content_hash:
                    print(f"📝 文档内容未变化，跳过版本快照: document_id={document_id}")
                    return True  # 返回True表示操作成功，但没有创建新版本
                
                # 获取下一个版本号
                max_version_stmt = select(func.max(DocumentVersion.version_number)).where(
                    DocumentVersion.document_id == document_id
                )
                max_version_result = await db.execute(max_version_stmt)
                max_version = max_version_result.scalar() or 0
                next_version = max_version + 1
                
                # 内容有变化，创建新版本
                new_version = DocumentVersion(
                    document_id=document_id,
                    version_number=next_version,
                    title=document.title,
                    content=document.content,
                    content_hash=current_content_hash,
                    changed_by=user_id,
                    change_description=description
                )
                
                db.add(new_version)
                await db.commit()
                print(f"✅ 版本快照已创建（内容变化）: document_id={document_id}, version={next_version}")
                return True
                
        except Exception as e:
            print(f"❌ 创建版本快照失败: {e}")
            return False

    async def create_version_snapshot_with_content(self, document_id: int, user_id: int, description: str, content: str):
        """使用指定内容创建版本快照 - 只有内容真正变化时才创建"""
        try:
            async for db in get_db():
                # 获取当前文档
                stmt = select(Document).where(Document.id == document_id)
                result = await db.execute(stmt)
                document = result.scalar_one_or_none()
                
                if not document:
                    return False
                
                # 计算新内容的哈希值
                new_content_hash = hashlib.md5(content.encode()).hexdigest()
                
                # 检查最新版本的内容哈希
                latest_version_stmt = (
                    select(DocumentVersion.content_hash)
                    .where(DocumentVersion.document_id == document_id)
                    .order_by(desc(DocumentVersion.version_number))
                    .limit(1)
                )
                latest_result = await db.execute(latest_version_stmt)
                latest_hash = latest_result.scalar()
                
                # 如果内容哈希相同，说明内容没有变化，跳过创建版本
                if latest_hash == new_content_hash:
                    print(f"📝 指定内容未变化，跳过版本快照: document_id={document_id}")
                    return True  # 返回True表示操作成功，但没有创建新版本
                
                # 获取下一个版本号
                max_version_stmt = select(func.max(DocumentVersion.version_number)).where(
                    DocumentVersion.document_id == document_id
                )
                max_version_result = await db.execute(max_version_stmt)
                max_version = max_version_result.scalar() or 0
                next_version = max_version + 1
                
                # 内容有变化，创建新版本
                new_version = DocumentVersion(
                    document_id=document_id,
                    version_number=next_version,
                    title=document.title,
                    content=content,  # 使用提供的内容
                    content_hash=new_content_hash,
                    changed_by=user_id,
                    change_description=description
                )
                
                db.add(new_version)
                await db.commit()
                print(f"✅ 版本快照已创建（指定内容变化）: document_id={document_id}, version={next_version}")
                return True
                
        except Exception as e:
            print(f"❌ 创建版本快照失败: {e}")
            return False

    async def restore_version(self, document_id: int, version_number: int, user_id: int) -> bool:
        """恢复到指定版本"""
        try:
            async for db in get_db():
                # 获取指定版本
                version_stmt = select(DocumentVersion).where(
                    DocumentVersion.document_id == document_id,
                    DocumentVersion.version_number == version_number
                )
                version_result = await db.execute(version_stmt)
                target_version = version_result.scalar_one_or_none()
                
                if not target_version:
                    return False
                
                # 获取当前文档
                doc_stmt = select(Document).where(Document.id == document_id)
                doc_result = await db.execute(doc_stmt)
                document = doc_result.scalar_one_or_none()
                
                if not document:
                    return False
                
                # 恢复文档内容
                document.content = target_version.content
                document.title = target_version.title
                document.version += 1
                document.last_editor_id = user_id
                document.updated_at = datetime.utcnow()
                
                await db.commit()
                print(f"✅ 版本已恢复: document_id={document_id}, 恢复到版本={version_number}, 新版本={document.version}")
                return True
                
        except Exception as e:
            print(f"❌ 恢复版本失败: {e}")
            return False

    async def restore_version_with_content(self, document_id: int, version_number: int, user_id: int) -> Optional[Dict]:
        """恢复到指定版本并返回内容"""
        try:
            async for db in get_db():
                # 获取指定版本
                version_stmt = select(DocumentVersion).where(
                    DocumentVersion.document_id == document_id,
                    DocumentVersion.version_number == version_number
                )
                version_result = await db.execute(version_stmt)
                target_version = version_result.scalar_one_or_none()
                
                if not target_version:
                    return None
                
                # 获取当前文档
                doc_stmt = select(Document).where(Document.id == document_id)
                doc_result = await db.execute(doc_stmt)
                document = doc_result.scalar_one_or_none()
                
                if not document:
                    return None
                
                # 创建当前内容的备份版本
                backup_content_hash = hashlib.md5(document.content.encode()).hexdigest()
                backup_version = DocumentVersion(
                    document_id=document_id,
                    version_number=document.version,
                    title=document.title,
                    content=document.content,
                    content_hash=backup_content_hash,  # 添加内容哈希
                    changed_by=document.last_editor_id or document.owner_id,
                    change_description=f"恢复前的备份 - 版本 {document.version}"
                )
                db.add(backup_version)
                
                # 恢复文档内容
                document.content = target_version.content
                document.title = target_version.title
                document.version += 1
                document.last_editor_id = user_id
                document.updated_at = datetime.utcnow()
                
                # 创建恢复记录
                restore_content_hash = hashlib.md5(document.content.encode()).hexdigest()
                restore_version = DocumentVersion(
                    document_id=document_id,
                    version_number=document.version,
                    title=document.title,
                    content=document.content,
                    content_hash=restore_content_hash,  # 添加内容哈希
                    changed_by=user_id,
                    change_description=f"恢复到版本 {target_version.version_number}"
                )
                db.add(restore_version)
                
                await db.commit()
                await db.refresh(document)
                
                print(f"✅ 版本已恢复（带内容）: document_id={document_id}, 恢复到版本={version_number}, 新版本={document.version}")
                
                return {
                    "success": True,
                    "content": document.content,
                    "new_version": document.version
                }
                
        except Exception as e:
            print(f"❌ 恢复版本失败: {e}")
            return None

    async def get_version_content(self, document_id: int, version_number: int) -> Optional[str]:
        """获取指定版本的内容"""
        try:
            async for db in get_db():
                stmt = select(DocumentVersion).where(
                    DocumentVersion.document_id == document_id,
                    DocumentVersion.version_number == version_number
                )
                result = await db.execute(stmt)
                version = result.scalar_one_or_none()
                
                if version:
                    return version.content
                return None
                
        except Exception as e:
            print(f"❌ 获取版本内容失败: {e}")
            return None

    async def get_document_statistics(self, document_id: int) -> Dict:
        """获取文档统计信息"""
        try:
            async for db in get_db():
                # 获取版本数量
                version_count_stmt = select(func.count()).select_from(DocumentVersion).where(
                    DocumentVersion.document_id == document_id
                )
                version_count_result = await db.execute(version_count_stmt)
                version_count = version_count_result.scalar() or 0
                
                # 获取操作数量
                operation_count_stmt = select(func.count()).select_from(DocumentOperation).where(
                    DocumentOperation.document_id == document_id
                )
                operation_count_result = await db.execute(operation_count_stmt)
                operation_count = operation_count_result.scalar() or 0
                
                # 获取最新版本
                latest_version_stmt = select(func.max(DocumentVersion.version_number)).where(
                    DocumentVersion.document_id == document_id
                )
                latest_version_result = await db.execute(latest_version_stmt)
                latest_version = latest_version_result.scalar() or 0
                
                return {
                    "document_id": document_id,
                    "version_count": version_count,
                    "operation_count": operation_count,
                    "latest_version": latest_version,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            print(f"❌ 获取文档统计失败: {e}")
            return {
                "document_id": document_id,
                "version_count": 0,
                "operation_count": 0,
                "latest_version": 0,
                "generated_at": datetime.utcnow().isoformat(),
                "error": str(e)
            }

    async def cleanup_old_operations(self, document_id: int, keep_count: int = 100):
        """清理旧的操作记录"""
        try:
            async for db in get_db():
                # 获取需要保留的操作ID
                keep_operations_stmt = (
                    select(DocumentOperation.id)
                    .where(DocumentOperation.document_id == document_id)
                    .order_by(desc(DocumentOperation.created_at))
                    .limit(keep_count)
                )
                keep_operations_result = await db.execute(keep_operations_stmt)
                keep_ids = [row[0] for row in keep_operations_result.fetchall()]
                
                if not keep_ids:
                    return 0
                
                # 删除不在保留列表中的操作
                delete_stmt = select(DocumentOperation).where(
                    DocumentOperation.document_id == document_id,
                    ~DocumentOperation.id.in_(keep_ids)
                )
                delete_result = await db.execute(delete_stmt)
                operations_to_delete = delete_result.scalars().all()
                
                for operation in operations_to_delete:
                    await db.delete(operation)
                
                await db.commit()
                deleted_count = len(operations_to_delete)
                print(f"✅ 已清理 {deleted_count} 条旧操作记录")
                return deleted_count
                
        except Exception as e:
            print(f"❌ 清理操作记录失败: {e}")
            return 0


# 全局实例
document_storage_service = DocumentStorageService() 