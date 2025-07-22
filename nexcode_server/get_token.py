#!/usr/bin/env python3
"""
获取session token的脚本
"""

import requests
import json

def get_session_token():
    """获取session token"""
    
    base_url = "http://localhost:8000"
    
    # 登录获取token
    login_data = {
        "username": "demo",
        "password": "demo123"
    }
    
    try:
        print("🔐 尝试登录...")
        response = requests.post(f"{base_url}/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            session_token = data.get("session_token")
            if session_token:
                print(f"✅ 登录成功!")
                print(f"📝 Session Token: {session_token}")
                return session_token
            else:
                print("❌ 响应中没有session_token")
                print(f"响应内容: {data}")
        else:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    return None

if __name__ == "__main__":
    token = get_session_token()
    if token:
        print(f"\n🎯 使用以下token进行WebSocket测试:")
        print(f"Token: {token}")
    else:
        print("\n❌ 无法获取token") 