#!/usr/bin/env python3
"""
简化的协作测试
"""

import asyncio
import websockets
import json
import requests

async def test_simple_collaboration():
    """简化的协作测试"""
    
    # 获取token
    print("🔐 获取token...")
    try:
        response = requests.post("http://localhost:8000/v1/auth/login", json={
            "username": "demo",
            "password": "demo123"
        })
        
        if response.status_code == 200:
            data = response.json()
            session_token = data.get("session_token")
            print(f"✅ Token: {session_token[:20]}...")
        else:
            print(f"❌ 登录失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 获取token失败: {e}")
        return
    
    document_id = 12
    
    print(f"\n🔗 创建单个连接测试...")
    
    try:
        # 创建连接
        websocket = await websockets.connect(
            f"ws://localhost:8000/v1/documents/{document_id}/collaborate?token={session_token}"
        )
        
        print("✅ WebSocket连接建立")
        
        # 接收连接消息
        print("⏳ 等待连接消息...")
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            data = json.loads(message)
            print(f"📨 收到消息: {data.get('type')} - {data}")
        except asyncio.TimeoutError:
            print("⏰ 等待消息超时")
            return
        
        # 发送心跳
        print("💓 发送心跳...")
        await websocket.send(json.dumps({"type": "ping"}))
        
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"💓 心跳响应: {data}")
        except asyncio.TimeoutError:
            print("⏰ 心跳超时")
        
        # 关闭连接
        await websocket.close()
        print("✅ 连接关闭")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
    
    print(f"\n🎉 简化测试完成!")

if __name__ == "__main__":
    asyncio.run(test_simple_collaboration()) 