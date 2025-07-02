"""
API模块
统一管理后端API接口和客户端
"""

from .client import NexCodeAPIClient, api_client
from .endpoints import ENDPOINTS

__all__ = ['NexCodeAPIClient', 'api_client', 'ENDPOINTS'] 