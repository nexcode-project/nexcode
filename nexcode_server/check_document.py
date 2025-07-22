#!/usr/bin/env python3
"""
检查文档是否存在
"""

import requests
import json

def check_document():
    """检查文档是否存在"""
    
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
    
    # 检查文档列表
    print("\n📄 检查文档列表...")
    try:
        headers = {"Authorization": f"Bearer {session_token}"}
        response = requests.get("http://localhost:8000/v1/documents/", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])
            print(f"✅ 找到 {len(documents)} 个文档")
            
            for doc in documents:
                print(f"  - ID: {doc.get('id')}, 标题: {doc.get('title')}")
                
            # 检查是否有ID为12的文档
            doc_12 = next((doc for doc in documents if doc.get('id') == 12), None)
            if doc_12:
                print(f"✅ 找到文档12: {doc_12.get('title')}")
            else:
                print("❌ 没有找到文档12")
        else:
            print(f"❌ 获取文档列表失败: {response.status_code}")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 检查文档失败: {e}")

if __name__ == "__main__":
    check_document() 