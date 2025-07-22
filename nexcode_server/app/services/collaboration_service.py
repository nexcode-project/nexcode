import asyncio
import json
from typing import Dict, List, Set
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document_models import Document, DocumentOperation
from app.core.redis_client import redis_client


class CollaborationManager:
    """协作管理器"""

    def __init__(self):
        # 存储活跃连接 {document_id: {user_id: websocket}}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
        # 操作队列 {document_id: [operations]}
        self.operation_queues: Dict[int, List] = {}
        # 文档锁
        self.document_locks: Dict[int, asyncio.Lock] = {}
        # 用户信息缓存 {user_id: user_info}
        self.user_cache: Dict[int, dict] = {}

    async def connect(self, websocket: WebSocket, document_id: int, user_id: int):
        """用户连接到文档"""
        # 注意：websocket.accept() 已经在WebSocket端点中调用

        print(f"🔗 用户 {user_id} 连接到文档 {document_id}")

        if document_id not in self.active_connections:
            self.active_connections[document_id] = {}
            self.operation_queues[document_id] = []
            self.document_locks[document_id] = asyncio.Lock()
            print(f"📝 创建文档 {document_id} 的连接管理器")

        # 先添加到连接列表
        self.active_connections[document_id][user_id] = websocket
        print(f"✅ 用户 {user_id} 已添加到连接列表")

        # 通知其他用户有新用户加入
        print(f"📤 准备广播用户加入消息...")
        await self.broadcast_user_joined(document_id, user_id)

        # 发送当前在线用户列表
        print(f"📤 准备发送在线用户列表...")
        await self.send_online_users(document_id, user_id)

    async def disconnect(self, document_id: int, user_id: int):
        """用户断开连接"""
        print(f"🔒 用户 {user_id} 断开文档 {document_id} 的连接")
        
        if document_id in self.active_connections:
            # 先通知其他用户有用户离开
            print(f"📤 准备广播用户离开消息...")
            await self.broadcast_user_left(document_id, user_id)
            
            # 然后移除连接
            self.active_connections[document_id].pop(user_id, None)
            print(f"✅ 用户 {user_id} 已从连接列表移除")

            # 如果没有用户了，清理资源
            if not self.active_connections[document_id]:
                del self.active_connections[document_id]
                del self.operation_queues[document_id]
                del self.document_locks[document_id]
                print(f"🧹 清理文档 {document_id} 的资源")

    async def handle_operation(self, document_id: int, user_id: int, operation: dict):
        """处理文档操作"""
        print(f"📝 处理用户 {user_id} 的操作: {operation.get('type')}")
        
        async with self.document_locks[document_id]:
            # 添加到操作队列
            operation["user_id"] = user_id
            operation["timestamp"] = asyncio.get_event_loop().time()
            self.operation_queues[document_id].append(operation)

            # 应用OT算法转换操作
            transformed_op = await self.transform_operation(document_id, operation)

            # 广播给其他用户
            print(f"📤 准备广播操作...")
            await self.broadcast_operation(document_id, user_id, transformed_op)

            # 异步保存到数据库
            asyncio.create_task(self.save_operation_to_db(document_id, operation))

    async def handle_content_update(self, document_id: int, user_id: int, content: str):
        """处理完整内容更新"""
        print(f"📝 处理用户 {user_id} 的内容更新，长度: {len(content)}")
        
        async with self.document_locks[document_id]:
            # 广播完整内容给其他用户
            print(f"📤 准备广播完整内容...")
            await self.broadcast_content_update(document_id, user_id, content)

            # 异步保存到数据库
            asyncio.create_task(self.save_content_to_db(document_id, content))

    async def transform_operation(self, document_id: int, operation: dict) -> dict:
        """OT算法转换操作"""
        # 简化的OT实现，实际项目中需要更复杂的算法
        queue = self.operation_queues[document_id]

        for existing_op in queue[:-1]:  # 排除当前操作
            if existing_op["user_id"] != operation["user_id"]:
                operation = self.operational_transform(operation, existing_op)

        return operation

    def operational_transform(self, op1: dict, op2: dict) -> dict:
        """操作转换核心算法"""
        # 简化实现，实际需要根据操作类型进行复杂转换
        if op1["type"] == "insert" and op2["type"] == "insert":
            if op1["position"] <= op2["position"]:
                op2["position"] += len(op1["content"])
        elif op1["type"] == "delete" and op2["type"] == "insert":
            if op1["position"] < op2["position"]:
                op2["position"] -= op1["length"]

        return op2

    async def broadcast_operation(
        self, document_id: int, sender_id: int, operation: dict
    ):
        """广播操作给其他用户"""
        if document_id not in self.active_connections:
            return

        message = {"type": "operation", "operation": operation, "sender_id": sender_id}

        for user_id, websocket in self.active_connections[document_id].items():
            if user_id != sender_id:
                try:
                    await websocket.send_text(json.dumps(message))
                    print(f"📤 广播操作给用户 {user_id}: {operation.get('content', 'N/A')}")
                except Exception as e:
                    print(f"❌ 广播操作失败: {e}")
                    # 连接已断开，清理
                    await self.disconnect(document_id, user_id)

    async def broadcast_content_update(
        self, document_id: int, sender_id: int, content: str
    ):
        """广播完整内容更新给其他用户"""
        if document_id not in self.active_connections:
            return

        message = {"type": "content_update", "content": content, "sender_id": sender_id}

        for user_id, websocket in self.active_connections[document_id].items():
            if user_id != sender_id:
                try:
                    await websocket.send_text(json.dumps(message))
                    print(f"📤 广播完整内容给用户 {user_id}，长度: {len(content)}")
                except Exception as e:
                    print(f"❌ 广播内容更新失败: {e}")
                    # 连接已断开，清理
                    await self.disconnect(document_id, user_id)

    async def broadcast_cursor_position(
        self, document_id: int, user_id: int, position: dict
    ):
        """广播光标位置给其他用户"""
        if document_id not in self.active_connections:
            return

        message = {"type": "cursor", "user_id": user_id, "position": position}

        for uid, websocket in self.active_connections[document_id].items():
            if uid != user_id:
                try:
                    await websocket.send_text(json.dumps(message))
                except:
                    # 连接已断开，清理
                    await self.disconnect(document_id, uid)

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

        for uid, websocket in self.active_connections[document_id].items():
            if uid != user_id:
                try:
                    await websocket.send_text(json.dumps(message))
                    print(f"📤 广播用户加入: {user_info['username']} 给用户 {uid}")
                except Exception as e:
                    print(f"❌ 广播用户加入失败: {e}")
                    await self.disconnect(document_id, uid)

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

        for uid, websocket in self.active_connections[document_id].items():
            if uid != user_id:
                try:
                    await websocket.send_text(json.dumps(message))
                    print(f"📤 广播用户离开: {user_id} 给用户 {uid}")
                except Exception as e:
                    print(f"❌ 广播用户离开失败: {e}")
                    await self.disconnect(document_id, uid)

    async def send_online_users(self, document_id: int, user_id: int):
        """发送在线用户列表给指定用户"""
        if document_id not in self.active_connections:
            return

        # 获取在线用户列表
        online_users = []
        for uid in self.active_connections[document_id].keys():
            user_info = self.user_cache.get(uid, {"id": uid, "username": f"User{uid}"})
            online_users.append(user_info)

        message = {
            "type": "online_users",
            "users": online_users
        }

        websocket = self.active_connections[document_id].get(user_id)
        if websocket:
            try:
                await websocket.send_text(json.dumps(message))
                print(f"📤 发送在线用户列表给用户 {user_id}: {len(online_users)} 人")
                for user in online_users:
                    print(f"   - {user['username']} (ID: {user['id']})")
            except Exception as e:
                print(f"❌ 发送在线用户列表失败: {e}")
                await self.disconnect(document_id, user_id)

    async def save_operation_to_db(self, document_id: int, operation: dict):
        """保存操作到数据库"""
        try:
            # 这里应该保存到数据库，暂时只是日志
            print(f"Saving operation to DB: document_id={document_id}, operation={operation}")
        except Exception as e:
            print(f"Failed to save operation: {e}")

    async def save_content_to_db(self, document_id: int, content: str):
        """保存内容到数据库"""
        try:
            # 这里应该保存到数据库，暂时只是日志
            print(f"Saving content to DB: document_id={document_id}, content_length={len(content)}")
        except Exception as e:
            print(f"Failed to save content: {e}")

    def update_user_cache(self, user_id: int, user_info: dict):
        """更新用户信息缓存"""
        self.user_cache[user_id] = user_info


# 全局协作管理器实例
collaboration_manager = CollaborationManager()
