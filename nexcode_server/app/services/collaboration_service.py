import asyncio
import json
from typing import Dict, List, Optional
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.document_models import Document, DocumentVersion, DocumentOperation, OperationType
from app.core.database import get_db
from app.services.document_storage_service import document_storage_service


class CollaborationManager:
    """协作管理器"""

    def __init__(self):
        # 存储活跃连接 {document_id: {session_id: {"user_id": user_id, "websocket": websocket}}}
        self.active_connections: Dict[int, Dict[str, dict]] = {}
        # 操作队列 {document_id: [operations]}
        self.operation_queues: Dict[int, List] = {}
        # 文档锁
        self.document_locks: Dict[int, asyncio.Lock] = {}
        # 用户信息缓存 {user_id: user_info}
        self.user_cache: Dict[int, dict] = {}
        # 会话ID计数器
        self.session_counter = 0

    async def connect(self, websocket: WebSocket, document_id: int, user_id: int):
        """用户连接到文档"""
        # 注意：websocket.accept() 已经在WebSocket端点中调用

        # 生成唯一的会话ID
        self.session_counter += 1
        session_id = f"session_{self.session_counter}"
        
        print(f"🔗 用户 {user_id} 连接到文档 {document_id}，会话ID: {session_id}")

        if document_id not in self.active_connections:
            self.active_connections[document_id] = {}
            self.operation_queues[document_id] = []
            self.document_locks[document_id] = asyncio.Lock()
            print(f"📝 创建文档 {document_id} 的连接管理器")

        # 添加到连接列表，使用会话ID作为键
        self.active_connections[document_id][session_id] = {
            "user_id": user_id,
            "websocket": websocket,
            "session_id": session_id
        }
        print(f"✅ 用户 {user_id} 已添加到连接列表，会话ID: {session_id}")

        # 通知其他用户有新用户加入
        print(f"📤 准备广播用户加入消息...")
        await self.broadcast_user_joined(document_id, user_id)

        # 发送当前在线用户列表
        print(f"📤 准备发送在线用户列表...")
        await self.send_online_users(document_id, user_id)
        
        return session_id

    async def disconnect(self, document_id: int, user_id: int, session_id: str = None):
        """用户断开连接"""
        print(f"🔒 用户 {user_id} 断开文档 {document_id} 的连接，会话ID: {session_id}")
        
        if document_id in self.active_connections:
            if session_id:
                # 断开特定会话
                if session_id in self.active_connections[document_id]:
                    del self.active_connections[document_id][session_id]
                    print(f"✅ 会话 {session_id} 已从连接列表移除")
            else:
                # 断开用户的所有会话
                sessions_to_remove = [sid for sid, conn_info in self.active_connections[document_id].items() if conn_info["user_id"] == user_id]
                for sid in sessions_to_remove:
                    del self.active_connections[document_id][sid]
                    print(f"✅ 用户 {user_id} 的会话 {sid} 已移除")

            # 检查是否还有其他用户在线
            remaining_users = set(conn_info["user_id"] for conn_info in self.active_connections[document_id].values())
            
            # 如果没有用户了，清理资源
            if not remaining_users:
                del self.active_connections[document_id]
                del self.operation_queues[document_id]
                del self.document_locks[document_id]
                print(f"🧹 清理文档 {document_id} 的资源")
            else:
                # 通知其他用户有用户离开
                print(f"📤 准备广播用户离开消息...")
                await self.broadcast_user_left(document_id, user_id)

    async def handle_operation(self, document_id: int, user_id: int, operation: dict):
        """处理文档操作"""
        print(f"📝 处理用户 {user_id} 的操作: {operation}")
        
        async with self.document_locks[document_id]:
            # 转换操作
            transformed_operation = await self.transform_operation(document_id, operation)
            await self.broadcast_operation(document_id, user_id, transformed_operation)
            # 使用文档存储服务保存操作
            await document_storage_service.save_content(document_id, user_id, "", operation)

    async def handle_content_update(self, document_id: int, user_id: int, content: str, session_id: str = None):
        """处理完整内容更新"""
        print(f"📝 处理用户 {user_id} 的内容更新，长度: {len(content)}，会话ID: {session_id}")
        
        async with self.document_locks[document_id]:
            await self.broadcast_content_update(document_id, user_id, content, session_id)
            # 使用文档存储服务保存内容
            await document_storage_service.save_content(document_id, user_id, content)

    async def transform_operation(self, document_id: int, operation: dict) -> dict:
        """OT算法转换操作"""
        # 简单的操作转换逻辑
        return operation

    def operational_transform(self, op1: dict, op2: dict) -> dict:
        """操作转换核心算法"""
        # 操作转换算法
        return op1

    async def broadcast_operation(
        self, document_id: int, sender_id: int, operation: dict, sender_session_id: str = None
    ):
        """广播操作给其他用户"""
        if document_id not in self.active_connections:
            return

        message = {"type": "operation", "operation": operation, "sender_id": sender_id}

        for session_id, conn_info in self.active_connections[document_id].items():
            # 排除发送者的所有会话（如果指定了特定会话ID，则只排除该会话）
            if (sender_session_id and session_id != sender_session_id) or \
               (not sender_session_id and conn_info["user_id"] != sender_id):
                try:
                    await conn_info["websocket"].send_text(json.dumps(message))
                    print(f"📤 广播操作给用户 {conn_info['user_id']} (会话 {session_id})")
                except Exception as e:
                    print(f"❌ 广播操作失败: {e}")
                    await self.disconnect(document_id, conn_info["user_id"], session_id)

    async def broadcast_content_update(
        self, document_id: int, sender_id: int, content: str, sender_session_id: str = None
    ):
        """广播完整内容更新给其他用户"""
        if document_id not in self.active_connections:
            return

        message = {"type": "content_update", "content": content, "sender_id": sender_id}

        for session_id, conn_info in self.active_connections[document_id].items():
            # 排除发送者的所有会话（如果指定了特定会话ID，则只排除该会话）
            if (sender_session_id and session_id != sender_session_id) or \
               (not sender_session_id and conn_info["user_id"] != sender_id):
                try:
                    await conn_info["websocket"].send_text(json.dumps(message))
                    print(f"📤 广播完整内容给用户 {conn_info['user_id']} (会话 {session_id})，长度: {len(content)}")
                except Exception as e:
                    print(f"❌ 广播内容更新失败: {e}")
                    await self.disconnect(document_id, conn_info["user_id"], session_id)

    async def broadcast_cursor_position(
        self, document_id: int, user_id: int, position: dict, sender_session_id: str = None
    ):
        """广播光标位置给其他用户"""
        if document_id not in self.active_connections:
            return

        message = {"type": "cursor", "user_id": user_id, "position": position}

        for session_id, conn_info in self.active_connections[document_id].items():
            # 排除发送者的所有会话（如果指定了特定会话ID，则只排除该会话）
            if (sender_session_id and session_id != sender_session_id) or \
               (not sender_session_id and conn_info["user_id"] != user_id):
                try:
                    await conn_info["websocket"].send_text(json.dumps(message))
                except:
                    await self.disconnect(document_id, conn_info["user_id"], session_id)

    async def broadcast_user_joined(self, document_id: int, user_id: int):
        """广播用户加入消息"""
        if document_id not in self.active_connections:
            return

        # 获取用户信息
        user_info = self.user_cache.get(user_id, {"id": user_id, "username": f"User{user_id}"})
        
        message = {
            "type": "user_joined",
            "user": user_info
        }

        print(f"🔍 广播用户加入: {user_info['username']} (ID: {user_id})")
        print(f"🔍 当前连接数: {len(self.active_connections[document_id])}")

        for session_id, conn_info in self.active_connections[document_id].items():
            if conn_info["user_id"] != user_id:
                try:
                    await conn_info["websocket"].send_text(json.dumps(message))
                    print(f"📤 广播用户加入: {user_info['username']} 给用户 {conn_info['user_id']} (会话 {session_id})")
                except Exception as e:
                    print(f"❌ 广播用户加入失败: {e}")
                    await self.disconnect(document_id, conn_info["user_id"], session_id)

    async def broadcast_user_left(self, document_id: int, user_id: int):
        """广播用户离开消息"""
        if document_id not in self.active_connections:
            return

        message = {
            "type": "user_left",
            "user_id": user_id
        }

        print(f"🔍 广播用户离开: {user_id}")
        print(f"🔍 剩余连接数: {len(self.active_connections[document_id])}")

        for session_id, conn_info in self.active_connections[document_id].items():
            if conn_info["user_id"] != user_id:
                try:
                    await conn_info["websocket"].send_text(json.dumps(message))
                    print(f"📤 广播用户离开: {user_id} 给用户 {conn_info['user_id']} (会话 {session_id})")
                except Exception as e:
                    print(f"❌ 广播用户离开失败: {e}")
                    await self.disconnect(document_id, conn_info["user_id"], session_id)

    async def send_online_users(self, document_id: int, user_id: int):
        """发送在线用户列表给指定用户"""
        if document_id not in self.active_connections:
            return

        # 获取在线用户列表（去重）
        online_users = []
        seen_users = set()
        for conn_info in self.active_connections[document_id].values():
            uid = conn_info["user_id"]
            if uid not in seen_users:
                user_info = self.user_cache.get(uid, {"id": uid, "username": f"User{uid}"})
                online_users.append(user_info)
                seen_users.add(uid)

        message = {
            "type": "online_users",
            "users": online_users
        }

        # 发送给指定用户的所有会话
        for session_id, conn_info in self.active_connections[document_id].items():
            if conn_info["user_id"] == user_id:
                try:
                    await conn_info["websocket"].send_text(json.dumps(message))
                    print(f"📤 发送在线用户列表给用户 {user_id} (会话 {session_id}): {len(online_users)} 人")
                    for user in online_users:
                        print(f"   - {user['username']} (ID: {user['id']})")
                except Exception as e:
                    print(f"❌ 发送在线用户列表失败: {e}")
                    await self.disconnect(document_id, user_id, session_id)

    def update_user_cache(self, user_id: int, user_info: dict):
        """更新用户信息缓存"""
        self.user_cache[user_id] = user_info


# 全局协作管理器实例
collaboration_manager = CollaborationManager()
