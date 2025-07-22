#!/usr/bin/env python3
"""
WebSocket调试脚本
"""

import asyncio
import websockets
import json
import requests

async def debug_websocket():
    """调试WebSocket连接"""
    
    # 1. 获取token
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
    
    # 2. 测试单个连接
    print("\n🔗 测试WebSocket连接...")
    
    try:
        async with websockets.connect(
            f"ws://localhost:8000/v1/documents/12/collaborate?token={session_token}"
        ) as websocket:
            print("✅ WebSocket连接建立")
            
            # 等待连接消息
            print("⏳ 等待连接消息...")
            message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            data = json.loads(message)
            print(f"📨 收到消息: {data}")
            
            # 发送测试操作
            test_op = {
                "type": "operation",
                "operation": {
                    "type": "insert",
                    "position": 0,
                    "content": "测试内容"
                }
            }
            await websocket.send(json.dumps(test_op))
            print("📤 发送测试操作")
            
            # 等待响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📨 收到响应: {data}")
            except asyncio.TimeoutError:
                print("⏰ 没有收到响应")
            
            # 发送心跳
            await websocket.send(json.dumps({"type": "ping"}))
            print("💓 发送心跳")
            
            try:
                pong = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(pong)
                print(f"💓 心跳响应: {data}")
            except asyncio.TimeoutError:
                print("⏰ 心跳超时")
                
    except Exception as e:
        print(f"❌ WebSocket错误: {e}")
    
    print("\n🎯 调试完成!")

if __name__ == "__main__":
    asyncio.run(debug_websocket()) 