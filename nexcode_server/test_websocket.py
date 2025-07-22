#!/usr/bin/env python3
"""
WebSocket连接测试脚本
"""

import asyncio
import websockets
import json
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_websocket_connection():
    """测试WebSocket连接"""
    
    # 测试参数
    base_url = "ws://localhost:8000"
    document_id = 12  # 使用你提到的文档ID
    
    print(f"🔗 测试WebSocket连接到文档 {document_id}")
    
    # 测试1: 不带token的连接（应该被拒绝）
    print("\n1️⃣ 测试不带token的连接...")
    try:
        async with websockets.connect(f"{base_url}/v1/documents/{document_id}/collaborate") as websocket:
            await websocket.recv()
    except Exception as e:
        print(f"✅ 正确拒绝连接: {e}")
    
    # 测试2: 带无效token的连接
    print("\n2️⃣ 测试带无效token的连接...")
    try:
        async with websockets.connect(f"{base_url}/v1/documents/{document_id}/collaborate?token=invalid_token") as websocket:
            await websocket.recv()
    except Exception as e:
        print(f"✅ 正确拒绝无效token: {e}")
    
    # 测试3: 带有效token的连接
    print("\n3️⃣ 测试带有效token的连接...")
    
    # 这里需要先获取有效的token
    # 你可以手动提供一个有效的session_token
    valid_token = input("请输入有效的session_token (或按回车跳过): ").strip()
    
    if valid_token:
        try:
            async with websockets.connect(f"{base_url}/v1/documents/{document_id}/collaborate?token={valid_token}") as websocket:
                print("✅ 连接成功!")
                
                # 接收连接消息
                message = await websocket.recv()
                print(f"📨 收到消息: {message}")
                
                # 发送测试操作
                test_operation = {
                    "type": "operation",
                    "operation": {
                        "type": "insert",
                        "position": 0,
                        "content": "测试内容"
                    }
                }
                await websocket.send(json.dumps(test_operation))
                print("📤 发送测试操作")
                
                # 等待响应
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"📨 收到响应: {response}")
                except asyncio.TimeoutError:
                    print("⏰ 等待响应超时")
                
                # 发送心跳
                await websocket.send(json.dumps({"type": "ping"}))
                print("💓 发送心跳")
                
                try:
                    pong = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"💓 收到心跳响应: {pong}")
                except asyncio.TimeoutError:
                    print("⏰ 心跳响应超时")
                    
        except Exception as e:
            print(f"❌ 连接失败: {e}")
    else:
        print("⏭️  跳过有效token测试")
    
    print("\n🎯 测试完成!")

async def test_multiple_connections():
    """测试多个连接"""
    print("\n🔗 测试多个WebSocket连接...")
    
    base_url = "ws://localhost:8000"
    document_id = 12
    valid_token = input("请输入有效的session_token (或按回车跳过): ").strip()
    
    if not valid_token:
        print("⏭️  跳过多连接测试")
        return
    
    connections = []
    
    try:
        # 创建3个连接
        for i in range(3):
            print(f"🔗 创建连接 {i+1}...")
            websocket = await websockets.connect(f"{base_url}/v1/documents/{document_id}/collaborate?token={valid_token}")
            connections.append(websocket)
            
            # 接收连接消息
            message = await websocket.recv()
            print(f"📨 连接 {i+1} 收到: {message}")
        
        print(f"✅ 成功创建 {len(connections)} 个连接")
        
        # 从第一个连接发送操作
        test_operation = {
            "type": "operation",
            "operation": {
                "type": "insert",
                "position": 0,
                "content": f"来自连接1的测试内容 - {asyncio.get_event_loop().time()}"
            }
        }
        
        await connections[0].send(json.dumps(test_operation))
        print("📤 从连接1发送操作")
        
        # 等待其他连接接收
        for i in range(1, len(connections)):
            try:
                response = await asyncio.wait_for(connections[i].recv(), timeout=5.0)
                print(f"📨 连接 {i+1} 收到: {response}")
            except asyncio.TimeoutError:
                print(f"⏰ 连接 {i+1} 接收超时")
        
        # 等待一段时间观察在线用户
        print("⏳ 等待5秒观察在线用户...")
        await asyncio.sleep(5)
        
    except Exception as e:
        print(f"❌ 多连接测试失败: {e}")
    finally:
        # 关闭所有连接
        for i, websocket in enumerate(connections):
            try:
                await websocket.close()
                print(f"🔒 关闭连接 {i+1}")
            except:
                pass

if __name__ == "__main__":
    print("🚀 WebSocket连接测试")
    print("=" * 50)
    
    # 运行测试
    asyncio.run(test_websocket_connection())
    asyncio.run(test_multiple_connections())
    
    print("\n🎉 所有测试完成!") 