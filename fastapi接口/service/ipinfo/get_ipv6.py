import asyncio
import base64
import random
import time
import requests
from fastapi接口.dao.IpInfoRedisObj import ip_info_redis
from fastapi接口.log.base_log import ipv6_monitor_logger

async def get_ipv6_from_redis() -> str:
    """
    返回类似2409:8a1e:2e94:e320::/60这种cidr格式的ipv6地址
    :param get_from_redis:
    :return:
    """
    ipv6_addr = await ip_info_redis.get_ip_addr()
    if ipv6_addr is None:
        return ""
    return ipv6_addr


async def set_ipv6_to_redis(ip_addr):
    await ip_info_redis.set_ip_addr(ip_addr)


if __name__ == "__main__":
    result = asyncio.run(get_ipv6_from_redis())
    print(result)
