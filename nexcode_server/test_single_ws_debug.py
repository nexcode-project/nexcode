#!/usr/bin/env python3
"""
简单的WebSocket调试测试
"""

import asyncio
import websockets
import json
import requests

async def test_single_ws_debug():
    """简单的WebSocket调试测试"""
    
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
    
    print(f"\n🔗 创建WebSocket连接...")
    
    try:
        # 创建连接
        websocket = await websockets.connect(
            f"ws://localhost:8000/v1/documents/{document_id}/collaborate?token={session_token}"
        )
        
        print("✅ WebSocket连接建立")
        
        # 等待一段时间，让服务器处理连接
        await asyncio.sleep(2)
        
        # 发送操作
        print("📤 发送操作...")
        test_operation = {
            "type": "operation",
            "operation": {
                "type": "insert",
                "position": 0,
                "content": "测试内容"
            }
        }
        
        await websocket.send(json.dumps(test_operation))
        print("✅ 操作已发送")
        
        # 等待一段时间
        await asyncio.sleep(2)
        
        # 关闭连接
        await websocket.close()
        print("✅ 连接关闭")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
    
    print(f"\n🎉 调试测试完成!")

if __name__ == "__main__":
    asyncio.run(test_single_ws_debug()) 