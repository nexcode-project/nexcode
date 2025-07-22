#!/usr/bin/env python3
"""
WebSocket调试脚本
用于测试协作编辑功能的连接和消息传递
"""

import asyncio
import websockets
import json
import logging
from typing import Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketDebugger:
    def __init__(self, base_url: str = "ws://localhost:8000"):
        self.base_url = base_url
        self.connections = {}
        
    async def get_token(self) -> Optional[str]:
        """获取测试用的token"""
        try:
            import requests
            
            # 登录获取token
            login_data = {
                "username": "demo",
                "password": "demo123"
            }
            
            response = requests.post(
                f"{self.base_url.replace('ws://', 'http://')}/v1/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                logger.info(f"✅ 获取到token: {token[:20]}...")
                return token
            else:
                logger.error(f"❌ 登录失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取token失败: {e}")
            return None
    
    async def connect_user(self, user_id: int, document_id: int, token: str):
        """连接用户到文档"""
        url = f"{self.base_url}/v1/documents/{document_id}/collaborate?token={token}"
        
        try:
            websocket = await websockets.connect(url)
            self.connections[user_id] = websocket
            logger.info(f"✅ 用户 {user_id} 连接到文档 {document_id}")
            return websocket
        except Exception as e:
            logger.error(f"❌ 用户 {user_id} 连接失败: {e}")
            return None
    
    async def listen_messages(self, user_id: int, timeout: float = 5.0):
        """监听用户消息"""
        websocket = self.connections.get(user_id)
        if not websocket:
            logger.error(f"❌ 用户 {user_id} 未连接")
            return []
        
        messages = []
        try:
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                    messages.append(json.loads(message))
                    logger.info(f"📨 用户 {user_id} 收到消息: {message[:100]}...")
                except asyncio.TimeoutError:
                    break
        except Exception as e:
            logger.error(f"❌ 监听用户 {user_id} 消息失败: {e}")
        
        return messages
    
    async def send_operation(self, user_id: int, operation: dict):
        """发送操作"""
        websocket = self.connections.get(user_id)
        if not websocket:
            logger.error(f"❌ 用户 {user_id} 未连接")
            return False
        
        try:
            message = {
                "type": "operation",
                "operation": operation
            }
            await websocket.send(json.dumps(message))
            logger.info(f"📤 用户 {user_id} 发送操作: {operation}")
            return True
        except Exception as e:
            logger.error(f"❌ 用户 {user_id} 发送操作失败: {e}")
            return False
    
    async def close_connection(self, user_id: int):
        """关闭连接"""
        websocket = self.connections.get(user_id)
        if websocket:
            await websocket.close()
            del self.connections[user_id]
            logger.info(f"🔒 用户 {user_id} 连接已关闭")
    
    async def test_basic_connection(self):
        """测试基本连接"""
        logger.info("🧪 测试基本WebSocket连接...")
        
        # 获取token
        token = await self.get_token()
        if not token:
            logger.error("❌ 无法获取token，测试终止")
            return
        
        # 连接用户1
        await self.connect_user(1, 12, token)
        
        # 监听消息
        messages = await self.listen_messages(1, timeout=3.0)
        
        logger.info(f"📊 用户1收到 {len(messages)} 条消息:")
        for i, msg in enumerate(messages, 1):
            logger.info(f"  {i}. {msg.get('type', 'unknown')}: {msg}")
        
        # 关闭连接
        await self.close_connection(1)
    
    async def test_two_users(self):
        """测试两个用户协作"""
        logger.info("🧪 测试两个用户协作...")
        
        # 获取token
        token = await self.get_token()
        if not token:
            logger.error("❌ 无法获取token，测试终止")
            return
        
        # 连接两个用户
        await self.connect_user(1, 12, token)
        await self.connect_user(2, 12, token)
        
        # 等待连接消息
        await asyncio.sleep(1)
        
        # 用户1发送操作
        operation = {
            "type": "insert",
            "position": 0,
            "content": "Hello from user 1!"
        }
        await self.send_operation(1, operation)
        
        # 等待消息传递
        await asyncio.sleep(1)
        
        # 检查用户2是否收到操作
        messages = await self.listen_messages(2, timeout=2.0)
        operation_received = any(
            msg.get('type') == 'operation' and msg.get('operation', {}).get('content') == "Hello from user 1!"
            for msg in messages
        )
        
        if operation_received:
            logger.info("✅ 操作同步成功！")
        else:
            logger.error("❌ 操作同步失败！")
        
        # 关闭连接
        await self.close_connection(1)
        await self.close_connection(2)
    
    async def test_user_presence(self):
        """测试用户在线状态"""
        logger.info("🧪 测试用户在线状态...")
        
        # 获取token
        token = await self.get_token()
        if not token:
            logger.error("❌ 无法获取token，测试终止")
            return
        
        # 连接用户1
        await self.connect_user(1, 12, token)
        
        # 监听连接消息
        messages = await self.listen_messages(1, timeout=3.0)
        
        # 检查是否收到在线用户列表
        online_users_msg = next(
            (msg for msg in messages if msg.get('type') == 'online_users'),
            None
        )
        
        if online_users_msg:
            users = online_users_msg.get('users', [])
            logger.info(f"✅ 在线用户列表: {len(users)} 人")
            for user in users:
                logger.info(f"  - {user.get('username')} (ID: {user.get('id')})")
        else:
            logger.error("❌ 未收到在线用户列表")
        
        # 关闭连接
        await self.close_connection(1)

async def main():
    """主函数"""
    debugger = WebSocketDebugger()
    
    logger.info("🚀 开始WebSocket调试测试")
    logger.info("=" * 50)
    
    # 测试1: 基本连接
    await debugger.test_basic_connection()
    logger.info("-" * 30)
    
    # 测试2: 用户在线状态
    await debugger.test_user_presence()
    logger.info("-" * 30)
    
    # 测试3: 两个用户协作
    await debugger.test_two_users()
    logger.info("-" * 30)
    
    logger.info("🎉 调试测试完成")

if __name__ == "__main__":
    asyncio.run(main()) 