from enum import Enum
from CONFIG import CONFIG
from utl.redisTool.RedisManager import RedisManagerBase


class IpInfoRedisObj(RedisManagerBase):
    class RedisMap(str, Enum):
        ipv6_addr = "ipv6_addr"

    def __init__(self):
        super().__init__(db=CONFIG.database.ipInfoRedisObj.db,
                         host=CONFIG.database.ipInfoRedisObj.host,
                         port=CONFIG.database.ipInfoRedisObj.port, )

    async def set_ip_addr(self, ip_addr: str):
        await self._set(self.RedisMap.ipv6_addr.value, ip_addr)

    async def get_ip_addr(self):
        return await self._get(self.RedisMap.ipv6_addr.value)


ip_info_redis = IpInfoRedisObj()
