import redis.asyncio as redis
from app.core.config import settings


class RedisClient:
    def __init__(self):
        self.redis = redis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )

    async def set_document_lock(self, document_id: int, user_id: int, ttl: int = 300):
        """设置文档锁"""
        key = f"doc_lock:{document_id}"
        return await self.redis.setex(key, ttl, user_id)

    async def get_document_lock(self, document_id: int):
        """获取文档锁"""
        key = f"doc_lock:{document_id}"
        return await self.redis.get(key)

    async def add_online_user(self, document_id: int, user_id: int):
        """添加在线用户"""
        key = f"online_users:{document_id}"
        await self.redis.sadd(key, user_id)
        await self.redis.expire(key, 3600)  # 1小时过期

    async def remove_online_user(self, document_id: int, user_id: int):
        """移除在线用户"""
        key = f"online_users:{document_id}"
        await self.redis.srem(key, user_id)

    async def get_online_users(self, document_id: int):
        """获取在线用户列表"""
        key = f"online_users:{document_id}"
        return await self.redis.smembers(key)


redis_client = RedisClient()
