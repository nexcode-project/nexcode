#!/usr/bin/env python3
"""
测试debug功能的示例文件
"""

def hello_world():
    """
    打印问候语的函数
    """
    print("Hello, World!")
    return "功能已实现"

def add_numbers(a, b):
    """
    添加两个数字的函数
    """
    result = a + b
    print(f"计算结果: {a} + {b} = {result}")
    return result

if __name__ == "__main__":
    hello_world()
    add_numbers(5, 3) 