#!/usr/bin/env python3
"""
协作功能测试脚本
"""

import asyncio
import websockets
import json
import requests
import time

async def test_collaboration():
    """测试协作功能"""
    
    base_url = "http://localhost:8000"
    ws_url = "ws://localhost:8000"
    document_id = 12
    
    print("🚀 开始协作功能测试")
    print("=" * 50)
    
    # 1. 获取session token
    print("1️⃣ 获取session token...")
    try:
        response = requests.post(f"{base_url}/v1/auth/login", json={
            "username": "demo",
            "password": "demo123"
        })
        
        if response.status_code == 200:
            data = response.json()
            session_token = data.get("session_token")
            if session_token:
                print(f"✅ 获取token成功: {session_token[:20]}...")
            else:
                print("❌ 响应中没有session_token")
                return
        else:
            print(f"❌ 登录失败: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ 获取token失败: {e}")
        return
    
    # 2. 测试多个WebSocket连接
    print("\n2️⃣ 测试多个WebSocket连接...")
    
    connections = []
    try:
        # 创建3个连接
        for i in range(3):
            print(f"🔗 创建连接 {i+1}...")
            websocket = await websockets.connect(
                f"{ws_url}/v1/documents/{document_id}/collaborate?token={session_token}"
            )
            connections.append(websocket)
            
            # 接收连接消息
            message = await websocket.recv()
            data = json.loads(message)
            print(f"📨 连接 {i+1} 收到: {data.get('type')} - {data.get('message')}")
            
            # 检查是否收到在线用户列表
            if data.get('type') == 'connected':
                print(f"✅ 连接 {i+1} 成功建立")
        
        print(f"✅ 成功创建 {len(connections)} 个连接")
        
        # 3. 测试消息同步
        print("\n3️⃣ 测试消息同步...")
        
        # 从第一个连接发送操作
        test_operation = {
            "type": "operation",
            "operation": {
                "type": "insert",
                "position": 0,
                "content": f"来自连接1的测试内容 - {time.time()}"
            }
        }
        
        await connections[0].send(json.dumps(test_operation))
        print("📤 从连接1发送操作")
        
        # 等待其他连接接收
        for i in range(1, len(connections)):
            try:
                response = await asyncio.wait_for(connections[i].recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📨 连接 {i+1} 收到操作: {data.get('type')}")
                if data.get('type') == 'operation':
                    operation = data.get('operation', {})
                    print(f"   操作内容: {operation.get('content', 'N/A')}")
            except asyncio.TimeoutError:
                print(f"⏰ 连接 {i+1} 接收超时")
        
        # 4. 测试在线用户识别
        print("\n4️⃣ 测试在线用户识别...")
        
        # 等待一段时间让系统处理用户加入消息
        await asyncio.sleep(2)
        
        # 从第二个连接发送操作，触发在线用户广播
        test_operation2 = {
            "type": "operation",
            "operation": {
                "type": "insert",
                "position": 10,
                "content": f"来自连接2的测试内容 - {time.time()}"
            }
        }
        
        await connections[1].send(json.dumps(test_operation2))
        print("📤 从连接2发送操作")
        
        # 检查所有连接是否都收到了操作
        for i in range(len(connections)):
            if i != 1:  # 跳过发送者
                try:
                    response = await asyncio.wait_for(connections[i].recv(), timeout=5.0)
                    data = json.loads(response)
                    print(f"📨 连接 {i+1} 收到操作: {data.get('type')}")
                except asyncio.TimeoutError:
                    print(f"⏰ 连接 {i+1} 接收超时")
        
        # 5. 测试心跳
        print("\n5️⃣ 测试心跳...")
        
        for i, websocket in enumerate(connections):
            try:
                await websocket.send(json.dumps({"type": "ping"}))
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                if data.get('type') == 'pong':
                    print(f"💓 连接 {i+1} 心跳正常")
                else:
                    print(f"❓ 连接 {i+1} 收到非心跳响应: {data.get('type')}")
            except asyncio.TimeoutError:
                print(f"⏰ 连接 {i+1} 心跳超时")
        
        # 6. 测试用户离开
        print("\n6️⃣ 测试用户离开...")
        
        # 关闭第一个连接
        await connections[0].close()
        print("🔒 关闭连接1")
        
        # 等待其他连接收到用户离开消息
        await asyncio.sleep(2)
        
        # 检查其他连接是否收到用户离开消息
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
        print("\n🔒 清理连接...")
        for i, websocket in enumerate(connections):
            try:
                await websocket.close()
                print(f"✅ 关闭连接 {i+1}")
            except:
                pass
    
    print("\n🎉 协作功能测试完成!")

if __name__ == "__main__":
    asyncio.run(test_collaboration()) 