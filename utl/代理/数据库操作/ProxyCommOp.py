from fastapi接口.log.base_log import sql_log
from utl.代理.redisProxyRequest.GetProxyFromNet import get_proxy_methods
from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab
from fastapi接口.service.grpc_module.Utils.GrpcRedis import grpc_proxy_tools
from utl.代理.数据库操作.async_proxy_op_alchemy_mysql_ver import SQLHelper


async def get_available_proxy() -> ProxyTab | None:
    while 1:
        available_ip_status = await grpc_proxy_tools.get_rand_available_ip_status()
        proxy: ProxyTab | None = None
        if available_ip_status:
            proxy = await SQLHelper.get_proxy_by_ip(available_ip_status.ip)
        if not proxy:
            sql_log.debug(f'获取随机代理失败！正在尝试从全部的代理Redis中获取！')
            proxy = await SQLHelper.select_proxy('rand')
        if proxy:
            sql_log.debug(f'成功获取到代理{proxy.proxy}')
            return proxy
        sql_log.debug(f'获取随机代理失败！正在尝试重新获取！')
        await get_proxy_methods.get_proxy()
        await SQLHelper.check_redis_data()
