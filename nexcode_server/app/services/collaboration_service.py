import asyncio
import json
from typing import Dict, List, Set
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document_models import Document, DocumentSession, DocumentOperation
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
    
    async def connect(self, websocket: WebSocket, document_id: int, user_id: int):
        """用户连接到文档"""
        await websocket.accept()
        
        if document_id not in self.active_connections:
            self.active_connections[document_id] = {}
            self.operation_queues[document_id] = []
            self.document_locks[document_id] = asyncio.Lock()
        
        self.active_connections[document_id][user_id] = websocket
        
        # 通知其他用户有新用户加入
        await self.broadcast_user_joined(document_id, user_id)
        
        # 发送当前在线用户列表
        await self.send_online_users(document_id, user_id)
    
    async def disconnect(self, document_id: int, user_id: int):
        """用户断开连接"""
        if document_id in self.active_connections:
            self.active_connections[document_id].pop(user_id, None)
            
            # 如果没有用户了，清理资源
            if not self.active_connections[document_id]:
                del self.active_connections[document_id]
                del self.operation_queues[document_id]
                del self.document_locks[document_id]
            else:
                # 通知其他用户有用户离开
                await self.broadcast_user_left(document_id, user_id)
    
    async def handle_operation(self, document_id: int, user_id: int, operation: dict):
        """处理文档操作"""
        async with self.document_locks[document_id]:
            # 添加到操作队列
            operation['user_id'] = user_id
            operation['timestamp'] = asyncio.get_event_loop().time()
            self.operation_queues[document_id].append(operation)
            
            # 应用OT算法转换操作
            transformed_op = await self.transform_operation(document_id, operation)
            
            # 广播给其他用户
            await self.broadcast_operation(document_id, user_id, transformed_op)
            
            # 异步保存到数据库
            asyncio.create_task(self.save_operation_to_db(document_id, operation))
    
    async def transform_operation(self, document_id: int, operation: dict) -> dict:
        """OT算法转换操作"""
        # 简化的OT实现，实际项目中需要更复杂的算法
        queue = self.operation_queues[document_id]
        
        for existing_op in queue[:-1]:  # 排除当前操作
            if existing_op['user_id'] != operation['user_id']:
                operation = self.operational_transform(operation, existing_op)
        
        return operation
    
    def operational_transform(self, op1: dict, op2: dict) -> dict:
        """操作转换核心算法"""
        # 简化实现，实际需要根据操作类型进行复杂转换
        if op1['type'] == 'insert' and op2['type'] == 'insert':
            if op1['position'] <= op2['position']:
                op2['position'] += len(op1['content'])
        elif op1['type'] == 'delete' and op2['type'] == 'insert':
            if op1['position'] < op2['position']:
                op2['position'] -= op1['length']
        
        return op2
    
    async def broadcast_operation(self, document_id: int, sender_id: int, operation: dict):
        """广播操作给其他用户"""
        if document_id not in self.active_connections:
            return
        
        message = {
            'type': 'operation',
            'operation': operation,
            'sender_id': sender_id
        }
        
        for user_id, websocket in self.active_connections[document_id].items():
            if user_id != sender_id:
                try:
                    await websocket.send_text(json.dumps(message))
                except:
                    # 连接已断开，清理
                    await self.disconnect(document_id, user_id)

# 全局协作管理器实例
collaboration_manager = CollaborationManager()