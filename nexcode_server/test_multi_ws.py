#!/usr/bin/env python3
"""
多连接WebSocket测试
"""

import asyncio
import websockets
import json
import requests
import time

async def test_multi_connections():
    """测试多个WebSocket连接"""
    
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
    
    # 创建多个连接
    connections = []
    document_id = 12
    
    print(f"\n🔗 创建多个WebSocket连接...")
    
    try:
        # 创建3个连接
        for i in range(3):
            print(f"🔗 创建连接 {i+1}...")
            websocket = await websockets.connect(
                f"ws://localhost:8000/v1/documents/{document_id}/collaborate?token={session_token}"
            )
            connections.append(websocket)
            
            # 接收连接消息
            message = await websocket.recv()
            data = json.loads(message)
            print(f"📨 连接 {i+1} 收到: {data.get('type')}")
            
            # 等待在线用户列表
            message2 = await websocket.recv()
            data2 = json.loads(message2)
            print(f"📨 连接 {i+1} 在线用户: {data2.get('type')} - {len(data2.get('users', []))} 人")
        
        print(f"✅ 成功创建 {len(connections)} 个连接")
        
        # 等待一段时间让所有连接稳定
        await asyncio.sleep(2)
        
        # 从第一个连接发送操作
        print(f"\n📤 从连接1发送操作...")
        test_operation = {
            "type": "operation",
            "operation": {
                "type": "insert",
                "position": 0,
                "content": f"来自连接1的测试内容 - {time.time()}"
            }
        }
        
        await connections[0].send(json.dumps(test_operation))
        
        # 等待其他连接接收
        print(f"⏳ 等待其他连接接收操作...")
        for i in range(1, len(connections)):
            try:
                response = await asyncio.wait_for(connections[i].recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📨 连接 {i+1} 收到: {data.get('type')}")
                if data.get('type') == 'operation':
                    operation = data.get('operation', {})
                    print(f"   操作内容: {operation.get('content', 'N/A')}")
            except asyncio.TimeoutError:
                print(f"⏰ 连接 {i+1} 接收超时")
        
        # 测试心跳
        print(f"\n💓 测试心跳...")
        for i, websocket in enumerate(connections):
            try:
                await websocket.send(json.dumps({"type": "ping"}))
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                if data.get('type') == 'pong':
                    print(f"✅ 连接 {i+1} 心跳正常")
                else:
                    print(f"❓ 连接 {i+1} 收到: {data.get('type')}")
            except asyncio.TimeoutError:
                print(f"⏰ 连接 {i+1} 心跳超时")
        
        # 测试用户离开
        print(f"\n🔒 测试用户离开...")
        await connections[0].close()
        print("✅ 关闭连接1")
        
        # 等待其他连接收到用户离开消息
        await asyncio.sleep(2)
        
        for i in range(1, len(connections)):
            try:
                response = await asyncio.wait_for(connections[i].recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📨 连接 {i+1} 收到: {data.get('type')}")
            except asyncio.TimeoutError:
                print(f"⏰ 连接 {i+1} 没有收到用户离开消息")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
    finally:
        # 关闭所有连接
        print(f"\n🔒 清理连接...")
        for i, websocket in enumerate(connections):
            try:
                await websocket.close()
                print(f"✅ 关闭连接 {i+1}")
            except:
                pass
    
    print(f"\n🎉 多连接测试完成!")

if __name__ == "__main__":
    asyncio.run(test_multi_connections()) 