#!/usr/bin/env python3
"""
详细调试协作功能
"""

import asyncio
import websockets
import json
import requests
import time

async def debug_collaboration():
    """详细调试协作功能"""
    
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
    
    print(f"\n🔗 创建第一个连接...")
    
    try:
        # 创建第一个连接
        websocket1 = await websockets.connect(
            f"ws://localhost:8000/v1/documents/{document_id}/collaborate?token={session_token}"
        )
        
        # 接收所有消息
        print("⏳ 等待连接消息...")
        messages = []
        for i in range(5):  # 最多等待5条消息
            try:
                message = await asyncio.wait_for(websocket1.recv(), timeout=3.0)
                data = json.loads(message)
                messages.append(data)
                print(f"📨 消息 {i+1}: {data.get('type')} - {data}")
            except asyncio.TimeoutError:
                break
        
        print(f"✅ 收到 {len(messages)} 条消息")
        
        # 发送操作
        print(f"\n📤 发送操作...")
        test_operation = {
            "type": "operation",
            "operation": {
                "type": "insert",
                "position": 0,
                "content": f"测试内容 - {time.time()}"
            }
        }
        
        await websocket1.send(json.dumps(test_operation))
        print("✅ 操作已发送")
        
        # 等待响应
        print("⏳ 等待操作响应...")
        try:
            response = await asyncio.wait_for(websocket1.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"📨 收到响应: {data}")
        except asyncio.TimeoutError:
            print("⏰ 没有收到操作响应")
        
        # 创建第二个连接
        print(f"\n🔗 创建第二个连接...")
        websocket2 = await websockets.connect(
            f"ws://localhost:8000/v1/documents/{document_id}/collaborate?token={session_token}"
        )
        
        # 接收第二个连接的消息
        print("⏳ 等待第二个连接的消息...")
        messages2 = []
        for i in range(5):
            try:
                message = await asyncio.wait_for(websocket2.recv(), timeout=3.0)
                data = json.loads(message)
                messages2.append(data)
                print(f"📨 连接2消息 {i+1}: {data.get('type')} - {data}")
            except asyncio.TimeoutError:
                break
        
        print(f"✅ 连接2收到 {len(messages2)} 条消息")
        
        # 从第一个连接发送操作
        print(f"\n📤 从连接1发送操作...")
        test_operation2 = {
            "type": "operation",
            "operation": {
                "type": "insert",
                "position": 10,
                "content": f"来自连接1的操作 - {time.time()}"
            }
        }
        
        await websocket1.send(json.dumps(test_operation2))
        print("✅ 操作已发送")
        
        # 等待连接2接收
        print("⏳ 等待连接2接收操作...")
        try:
            response = await asyncio.wait_for(websocket2.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"📨 连接2收到: {data}")
        except asyncio.TimeoutError:
            print("⏰ 连接2没有收到操作")
        
        # 测试心跳
        print(f"\n💓 测试心跳...")
        await websocket1.send(json.dumps({"type": "ping"}))
        try:
            response = await asyncio.wait_for(websocket1.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"💓 心跳响应: {data}")
        except asyncio.TimeoutError:
            print("⏰ 心跳超时")
        
        # 关闭第一个连接
        print(f"\n🔒 关闭连接1...")
        await websocket1.close()
        
        # 等待连接2收到用户离开消息
        print("⏳ 等待连接2收到用户离开消息...")
        try:
            response = await asyncio.wait_for(websocket2.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"📨 连接2收到: {data}")
        except asyncio.TimeoutError:
            print("⏰ 连接2没有收到用户离开消息")
        
        # 关闭第二个连接
        await websocket2.close()
        
    except Exception as e:
        print(f"❌ 调试过程中出错: {e}")
    
    print(f"\n🎉 调试完成!")

if __name__ == "__main__":
    asyncio.run(debug_collaboration()) 