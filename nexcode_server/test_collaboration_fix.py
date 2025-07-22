#!/usr/bin/env python3
"""
修复后的协作测试脚本
使用不同的用户来测试操作同步
"""

import asyncio
import websockets
import json
import logging
import requests
from typing import Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CollaborationTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.connections = {}
        self.tokens = {}
        
    async def login_user(self, username: str, password: str) -> Optional[str]:
        """登录用户并获取token"""
        try:
            login_data = {
                "username": username,
                "password": password
            }
            
            response = requests.post(
                f"{self.base_url}/v1/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                logger.info(f"✅ 用户 {username} 登录成功: {token[:20]}...")
                return token
            else:
                logger.error(f"❌ 用户 {username} 登录失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 用户 {username} 登录失败: {e}")
            return None
    
    async def connect_user(self, username: str, document_id: int, token: str):
        """连接用户到文档"""
        ws_url = f"ws://localhost:8000/v1/documents/{document_id}/collaborate?token={token}"
        
        try:
            websocket = await websockets.connect(ws_url)
            self.connections[username] = websocket
            self.tokens[username] = token
            logger.info(f"✅ 用户 {username} 连接到文档 {document_id}")
            return websocket
        except Exception as e:
            logger.error(f"❌ 用户 {username} 连接失败: {e}")
            return None
    
    async def listen_messages(self, username: str, timeout: float = 5.0):
        """监听用户消息"""
        websocket = self.connections.get(username)
        if not websocket:
            logger.error(f"❌ 用户 {username} 未连接")
            return []
        
        messages = []
        try:
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                    messages.append(json.loads(message))
                    logger.info(f"📨 用户 {username} 收到消息: {message[:100]}...")
                except asyncio.TimeoutError:
                    break
        except Exception as e:
            logger.error(f"❌ 监听用户 {username} 消息失败: {e}")
        
        return messages
    
    async def send_operation(self, username: str, operation: dict):
        """发送操作"""
        websocket = self.connections.get(username)
        if not websocket:
            logger.error(f"❌ 用户 {username} 未连接")
            return False
        
        try:
            message = {
                "type": "operation",
                "operation": operation
            }
            await websocket.send(json.dumps(message))
            logger.info(f"📤 用户 {username} 发送操作: {operation}")
            return True
        except Exception as e:
            logger.error(f"❌ 用户 {username} 发送操作失败: {e}")
            return False
    
    async def close_connection(self, username: str):
        """关闭连接"""
        websocket = self.connections.get(username)
        if websocket:
            await websocket.close()
            del self.connections[username]
            logger.info(f"🔒 用户 {username} 连接已关闭")
    
    async def test_collaboration(self):
        """测试两个不同用户的协作"""
        logger.info("🧪 测试两个不同用户的协作...")
        
        # 登录两个不同的用户
        token1 = await self.login_user("demo", "demo123")
        token2 = await self.login_user("admin", "admin123")
        
        if not token1 or not token2:
            logger.error("❌ 无法获取用户token，测试终止")
            return
        
        # 连接两个用户到同一个文档
        await self.connect_user("demo", 12, token1)
        await self.connect_user("admin", 12, token2)
        
        # 等待连接建立
        await asyncio.sleep(2)
        
        # 监听两个用户的消息
        demo_messages = await self.listen_messages("demo", timeout=3.0)
        admin_messages = await self.listen_messages("admin", timeout=3.0)
        
        logger.info(f"📊 demo用户收到 {len(demo_messages)} 条消息")
        logger.info(f"📊 admin用户收到 {len(admin_messages)} 条消息")
        
        # demo用户发送操作
        operation = {
            "type": "insert",
            "position": 0,
            "content": "Hello from demo user!"
        }
        await self.send_operation("demo", operation)
        
        # 等待消息传递
        await asyncio.sleep(2)
        
        # 检查admin用户是否收到操作
        new_admin_messages = await self.listen_messages("admin", timeout=3.0)
        
        operation_received = any(
            msg.get('type') == 'operation' and 
            msg.get('operation', {}).get('content') == "Hello from demo user!"
            for msg in new_admin_messages
        )
        
        if operation_received:
            logger.info("✅ 操作同步成功！")
        else:
            logger.error("❌ 操作同步失败！")
            logger.info("收到的消息:")
            for i, msg in enumerate(new_admin_messages, 1):
                logger.info(f"  {i}. {msg}")
        
        # admin用户发送操作
        operation2 = {
            "type": "insert",
            "position": 0,
            "content": "Hello from admin user!"
        }
        await self.send_operation("admin", operation2)
        
        # 等待消息传递
        await asyncio.sleep(2)
        
        # 检查demo用户是否收到操作
        new_demo_messages = await self.listen_messages("demo", timeout=3.0)
        
        operation2_received = any(
            msg.get('type') == 'operation' and 
            msg.get('operation', {}).get('content') == "Hello from admin user!"
            for msg in new_demo_messages
        )
        
        if operation2_received:
            logger.info("✅ 反向操作同步也成功！")
        else:
            logger.error("❌ 反向操作同步失败！")
        
        # 关闭连接
        await self.close_connection("demo")
        await self.close_connection("admin")

async def main():
    """主函数"""
    tester = CollaborationTester()
    
    logger.info("🚀 开始协作功能测试")
    logger.info("=" * 50)
    
    await tester.test_collaboration()
    
    logger.info("🎉 测试完成")

if __name__ == "__main__":
    asyncio.run(main()) 