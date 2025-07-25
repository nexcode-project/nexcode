#!/usr/bin/env python3
"""
测试认证修复的脚本
"""
import asyncio
import httpx
import json

async def test_auth():
    """测试认证功能"""
    base_url = "http://localhost:8000"
    
    # 测试登录
    print("1. 测试登录...")
    async with httpx.AsyncClient() as client:
        login_data = {
            "username": "admin@example.com",
            "password": "admin123"
        }
        
        try:
            response = await client.post(f"{base_url}/v1/auth/login", json=login_data)
            print(f"登录响应状态: {response.status_code}")
            
            if response.status_code == 200:
                login_result = response.json()
                session_token = login_result.get("session_token")
                print(f"获取到 session_token: {session_token[:20]}...")
                
                # 测试文档版本接口
                print("\n2. 测试文档版本接口...")
                headers = {"X-Session-Token": session_token}
                
                # 测试获取文档版本
                version_response = await client.get(
                    f"{base_url}/v1/documents/5/versions",
                    headers=headers
                )
                print(f"版本接口响应状态: {version_response.status_code}")
                if version_response.status_code == 200:
                    print("✅ 版本接口认证成功")
                else:
                    print(f"❌ 版本接口认证失败: {version_response.text}")
                
                # 测试 ShareDB 接口
                print("\n3. 测试 ShareDB 接口...")
                sharedb_response = await client.get(
                    f"{base_url}/v1/sharedb/documents/5",
                    headers=headers
                )
                print(f"ShareDB 接口响应状态: {sharedb_response.status_code}")
                if sharedb_response.status_code == 200:
                    print("✅ ShareDB 接口认证成功")
                else:
                    print(f"❌ ShareDB 接口认证失败: {sharedb_response.text}")
                
            else:
                print(f"❌ 登录失败: {response.text}")
                
        except Exception as e:
            print(f"❌ 测试过程中出错: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth()) 