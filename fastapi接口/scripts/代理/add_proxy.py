import asyncio

from utl.代理.redisProxyRequest.GetProxyFromNet import get_proxy_methods

async def upsert_proxy():
    results , _ = await get_proxy_methods.get_proxy_from_fyvri_fresh_proxy_list_socks5()
    await asyncio.gather(*[get_proxy_methods._check_ip_by_bili_zone(proxy=result) for result in results])
if __name__ == "__main__":
    asyncio.run(upsert_proxy())