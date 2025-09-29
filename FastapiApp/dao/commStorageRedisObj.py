from enum import Enum
from CONFIG import CONFIG
from Utils.redisTool.RedisManager import RedisManagerBase


class CommStorageRedisObj(RedisManagerBase):
    class RedisMap(str, Enum):
        reserve_scrapy_bot_rid_ls='reserve_scrapy_bot_rid_ls'

    def __init__(self):
        super().__init__(db=CONFIG.database.commStorageRedis.db,
                         host=CONFIG.database.commStorageRedis.host,
                         port=CONFIG.database.commStorageRedis.port, )
        self.redis_pref = self.__class__.__name__

    def to_redis_key(self, key_name: str | RedisMap):
        return f"{self.redis_pref}:{key_name}"

    async def set_val(self, key_name: RedisMap | str, val: str):
        await self._set(self.to_redis_key(key_name), val)

    async def get_val(self, key_name: RedisMap | str) -> str | None:
        return await self._get(self.to_redis_key(key_name))


comm_storage_redis_obj = CommStorageRedisObj()

if __name__ == "__main__":
    print(comm_storage_redis_obj.redis_pref)