#!/usr/bin/env python3
"""
NexCode OpenAI 兼容 API 使用示例
"""

import openai
import json

# 方法1：使用标准的 OpenAI Python 库
def test_with_openai_library():
    """使用标准的 OpenAI Python 库"""
    print("=== 使用 OpenAI Python 库 ===")
    
    # 配置客户端指向 NexCode 服务器
    client = openai.OpenAI(
        api_key="your-openai-api-key",  # 你的 OpenAI API key
        base_url="http://localhost:8000/v1"  # NexCode 服务器地址
    )
    
    # Chat Completions 示例
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的代码助手。"},
                {"role": "user", "content": "请解释什么是Git分支？"}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        print("Chat Completions 响应:")
        print(response.choices[0].message.content)
        print(f"使用的 tokens: {response.usage.total_tokens}")
        
    except Exception as e:
        print(f"错误: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Text Completions 示例
    try:
        response = client.completions.create(
            model="gpt-3.5-turbo",
            prompt="Git 的三个主要组成部分是：",
            max_tokens=200,
            temperature=0.5
        )
        
        print("Text Completions 响应:")
        print(response.choices[0].text)
        print(f"使用的 tokens: {response.usage.total_tokens}")
        
    except Exception as e:
        print(f"错误: {e}")

# 方法2：使用 requests 直接调用 API
def test_with_requests():
    """使用 requests 直接调用 API"""
    import requests
    
    print("=== 使用 requests 直接调用 ===")
    
    base_url = "http://localhost:8000/v1"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer your-openai-api-key"  # 你的 OpenAI API key
    }
    
    # Chat Completions
    chat_data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "你是一个专业的代码助手。"},
            {"role": "user", "content": "请简单介绍一下Python的优势？"}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }
    
    try:
        response = requests.post(f"{base_url}/chat/completions", 
                               headers=headers, 
                               json=chat_data)
        
        if response.status_code == 200:
            result = response.json()
            print("Chat Completions 响应:")
            print(result["choices"][0]["message"]["content"])
            print(f"使用的 tokens: {result['usage']['total_tokens']}")
        else:
            print(f"请求失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"错误: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Text Completions
    completion_data = {
        "model": "gpt-3.5-turbo",
        "prompt": "Python 的主要特点包括：",
        "max_tokens": 200,
        "temperature": 0.5
    }
    
    try:
        response = requests.post(f"{base_url}/completions", 
                               headers=headers, 
                               json=completion_data)
        
        if response.status_code == 200:
            result = response.json()
            print("Text Completions 响应:")
            print(result["choices"][0]["text"])
            print(f"使用的 tokens: {result['usage']['total_tokens']}")
        else:
            print(f"请求失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"错误: {e}")

# 方法3：测试不同的参数
def test_different_parameters():
    """测试不同的 OpenAI 参数"""
    print("=== 测试不同参数 ===")
    
    client = openai.OpenAI(
        api_key="your-openai-api-key",
        base_url="http://localhost:8000/v1"
    )
    
    # 测试不同的 temperature
    temperatures = [0.1, 0.7, 1.0]
    
    for temp in temperatures:
        print(f"\n--- Temperature: {temp} ---")
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "用一句话描述Python语言"}
                ],
                temperature=temp,
                max_tokens=100
            )
            
            print(response.choices[0].message.content)
            
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    print("NexCode OpenAI 兼容 API 测试\n")
    
    # 注意：请确保 NexCode 服务器正在运行在 http://localhost:8000
    # 并且替换 "your-openai-api-key" 为你的实际 OpenAI API key
    
    test_with_openai_library()
    
    print("\n" + "="*60 + "\n")
    
    test_with_requests()
    
    print("\n" + "="*60 + "\n")
    
    test_different_parameters() 