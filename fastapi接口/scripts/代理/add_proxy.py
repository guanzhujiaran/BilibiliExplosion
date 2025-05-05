import asyncio

from utl.代理.redisProxyRequest.GetProxyFromNet import get_proxy_methods
async def upsert_proxy():
    get_proxy_methods.get_proxy_page=146
    results , _ = await get_proxy_methods.get_proxy_from_ihuan()
    await asyncio.gather(*[get_proxy_methods._check_ip_by_bili_zone(proxy=result) for result in results])
if __name__ == "__main__":
    asyncio.run(upsert_proxy())