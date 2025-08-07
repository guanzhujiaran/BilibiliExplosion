import asyncio

from fastapi接口.utils.Common import asyncio_gather
from utl.代理.redisProxyRequest.GetProxyFromNet import get_proxy_methods
async def upsert_proxy():
    get_proxy_methods.get_proxy_page=10
    results , _ = await get_proxy_methods.get_proxy_from_saisuiu_Lionkings_Http_Proxys_Proxies()
    print(results)
    for result in results:
        await get_proxy_methods._check_ip_by_bili_zone(proxy=result)
if __name__ == "__main__":
    asyncio.run(upsert_proxy())