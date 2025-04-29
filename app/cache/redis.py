# import json
# import pickle
# from typing import Any, Optional, Union
# import redis.asyncio as redis

# from app.core.config import settings

# class MemcachedClient:
    
#     def __init__(self):
#         self.redis = redis.Redis(
#             host=settings.REDIS_HOST,
#             port=settings.REDIS_PORT,
#             db=settings.REDIS_DB,
#             password=settings.REDIS_PASSWORD,
#             decode_responses=False
#         )
        
#     async def get(self, key: str) -> Optional[Any]:
#         data = await self.redis.get(key)
        
#         if not data:
#             return None
            
#         try:
#             return pickle.loads(data)
#         except Exception:
#             return None
    
#     async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
#         try:
#             pickled_value = pickle.dumps(value)
#             return await self.redis.set(key, pickled_value, ex=expire)
#         except Exception:
#             return False
    
#     async def delete(self, key: str) -> bool:
#         return await self.redis.delete(key) > 0
    
#     async def get_hash(self, name: str, key: str) -> Optional[Any]:
#         data = await self.redis.hget(name, key)
        
#         if not data:
#             return None
            
#         try:
#             return pickle.loads(data)
#         except Exception:
#             return None
    
#     async def set_hash(self, name: str, key: str, value: Any) -> bool:
#         try:
#             pickled_value = pickle.dumps(value)
#             return await self.redis.hset(name, key, pickled_value) > 0
#         except Exception:
#             return False



from aiocache import SimpleMemoryCache
import pickle
from typing import Any, Optional

class MemcachedClient:
    
    def __init__(self):
        self.cache = SimpleMemoryCache()
        
    async def get(self, key: str) -> Optional[Any]:
        data = await self.cache.get(key)
        if data is None:
            return None
        try:
            return pickle.loads(data)
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        try:
            pickled_value = pickle.dumps(value)
            await self.cache.set(key, pickled_value, ttl=expire)
            return True
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            await self.cache.delete(key)
            return True
        except Exception:
            return False

    async def get_hash(self, name: str, key: str) -> Optional[Any]:
        full_key = f"{name}:{key}"
        return await self.get(full_key)
    
    async def set_hash(self, name: str, key: str, value: Any) -> bool:
        full_key = f"{name}:{key}"
        return await self.set(full_key, value)

