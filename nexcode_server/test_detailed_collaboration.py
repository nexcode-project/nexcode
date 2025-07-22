#!/usr/bin/env python3
"""
详细的多连接协作测试
"""

import asyncio
import websockets
import json
import requests
import time

async def test_detailed_collaboration():
    """详细的多连接协作测试"""
    
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
        
        print("✅ 连接1建立")
        
        # 接收连接1的所有消息
        print("⏳ 等待连接1的消息...")
        messages1 = []
        for i in range(5):
            try:
                message = await asyncio.wait_for(websocket1.recv(), timeout=3.0)
                data = json.loads(message)
                messages1.append(data)
                print(f"📨 连接1消息 {i+1}: {data.get('type')}")
            except asyncio.TimeoutError:
                break
        
        print(f"✅ 连接1收到 {len(messages1)} 条消息")
        
        # 等待一段时间
        await asyncio.sleep(1)
        
        # 创建第二个连接
        print(f"\n🔗 创建第二个连接...")
        websocket2 = await websockets.connect(
            f"ws://localhost:8000/v1/documents/{document_id}/collaborate?token={session_token}"
        )
        
        print("✅ 连接2建立")
        
        # 接收连接2的所有消息
        print("⏳ 等待连接2的消息...")
        messages2 = []
        for i in range(5):
            try:
                message = await asyncio.wait_for(websocket2.recv(), timeout=3.0)
                data = json.loads(message)
                messages2.append(data)
                print(f"📨 连接2消息 {i+1}: {data.get('type')}")
            except asyncio.TimeoutError:
                break
        
        print(f"✅ 连接2收到 {len(messages2)} 条消息")
        
        # 检查连接1是否收到用户加入消息
        print(f"\n🔍 检查连接1是否收到用户加入消息...")
        try:
            message = await asyncio.wait_for(websocket1.recv(), timeout=3.0)
            data = json.loads(message)
            print(f"📨 连接1收到: {data.get('type')}")
            if data.get('type') == 'user_joined':
                print(f"✅ 连接1收到用户加入消息: {data.get('user', {}).get('username')}")
            else:
                print(f"❓ 连接1收到其他消息: {data}")
        except asyncio.TimeoutError:
            print("⏰ 连接1没有收到用户加入消息")
        
        # 从连接1发送操作
        print(f"\n📤 从连接1发送操作...")
        test_operation = {
            "type": "operation",
            "operation": {
                "type": "insert",
                "position": 0,
                "content": f"来自连接1的测试内容 - {time.time()}"
            }
        }
        
        await websocket1.send(json.dumps(test_operation))
        print("✅ 操作已发送")
        
        # 等待连接2接收操作
        print("⏳ 等待连接2接收操作...")
        try:
            response = await asyncio.wait_for(websocket2.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"📨 连接2收到: {data.get('type')}")
            if data.get('type') == 'operation':
                operation = data.get('operation', {})
                print(f"✅ 连接2收到操作: {operation.get('content', 'N/A')}")
            else:
                print(f"❓ 连接2收到其他消息: {data}")
        except asyncio.TimeoutError:
            print("⏰ 连接2没有收到操作")
        
        # 关闭连接1
        print(f"\n🔒 关闭连接1...")
        await websocket1.close()
        
        # 等待连接2收到用户离开消息
        print("⏳ 等待连接2收到用户离开消息...")
        try:
            response = await asyncio.wait_for(websocket2.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"📨 连接2收到: {data.get('type')}")
            if data.get('type') == 'user_left':
                print(f"✅ 连接2收到用户离开消息: {data.get('user_id')}")
            else:
                print(f"❓ 连接2收到其他消息: {data}")
        except asyncio.TimeoutError:
            print("⏰ 连接2没有收到用户离开消息")
        
        # 关闭连接2
        await websocket2.close()
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
    
    print(f"\n🎉 详细测试完成!")

if __name__ == "__main__":
    asyncio.run(test_detailed_collaboration()) 