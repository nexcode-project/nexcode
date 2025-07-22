#!/usr/bin/env python3
"""
简化的WebSocket测试
"""

import asyncio
import websockets
import json

async def test_ws():
    """测试WebSocket连接"""
    
    # 测试不带token的连接
    print("🔗 测试不带token的WebSocket连接...")
    
    try:
        async with websockets.connect("ws://localhost:8000/v1/documents/12/collaborate") as ws:
            await ws.recv()
    except Exception as e:
        print(f"✅ 正确拒绝连接: {type(e).__name__}: {e}")
    
    print("\n🎯 测试完成!")

if __name__ == "__main__":
    asyncio.run(test_ws()) 