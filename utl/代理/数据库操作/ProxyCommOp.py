import asyncio
import time
from typing import Optional

from fastapi接口.log.base_log import sql_log
from utl.代理.redisProxyRequest.GetProxyFromNet import get_proxy_methods
from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab, AvailableProxy
from utl.代理.数据库操作.async_proxy_op_alchemy_mysql_ver import SQLHelper
from utl.代理.数据库操作.available_proxy_sql_helper import sql_helper

__available_proxy_num: int = 0
__latest_sync_ts: int = 0
__lock = asyncio.Lock()


async def get_available_proxy(
        is_use_available_proxy: bool = False,
        initial_retry_delay_seconds: int = 10  # Base delay between retries when no proxy is found
) -> tuple[ProxyTab, bool]:
    """
    Continuously attempts to get a usable proxy from the database.
    If none is found, triggers proxy acquisition and waits before retrying.
    This function is designed to block/wait indefinitely until a proxy
    is successfully retrieved and returned.

    :param is_use_available_proxy: Whether to prioritize using proxies from the AvailableProxy table.
    :param initial_retry_delay_seconds: The base delay in seconds before retrying after acquisition fails or finds no new proxies.
    :return: A ProxyTab object. This function will not return None.
    """
    global __available_proxy_num, __latest_sync_ts
    attempt = -1  # Keep track of attempts for logging and backoff
    used_available_proxy = False
    if __available_proxy_num == 0 or __latest_sync_ts < int(time.time()) - 1 * 3600:
        async with __lock:
            if __available_proxy_num == 0 or __latest_sync_ts < int(time.time()) - 1 * 3600:
                __available_proxy_num = await sql_helper.get_num(is_available=True)
                __latest_sync_ts = int(time.time())
    while attempt <= 3:  # Loop indefinitely until a proxy is found
        attempt += 1
        proxy_tab: Optional[ProxyTab] = None
        # --- Attempt 1: Use AvailableProxy table (if requested) ---
        if is_use_available_proxy or __available_proxy_num > 300:  # 1千个以上随便用
            try:
                # This function now selects AND updates the chosen AvailableProxy
                available_proxy: Optional[AvailableProxy]
                available_proxy, __available_proxy_num = await sql_helper.get_rand_available_proxy_sql()
                if available_proxy and available_proxy.proxy_tab:
                    # Successfully got an AvailableProxy and its associated ProxyTab is loaded
                    proxy_tab = available_proxy.proxy_tab
                    used_available_proxy = True
            except Exception as e:
                sql_log.exception(f"Attempt {attempt}: Error getting from AvailableProxy: {e}")

        # --- Attempt 2: Fallback to general ProxyTab table ---
        if not proxy_tab:  # Only if Attempt 1 failed or wasn't requested
            try:
                # Assuming select_proxy tries to get a potentially usable one from the general pool
                proxy_tab = await SQLHelper.select_proxy("rand")  # Or 'rand_potentially_good' if you adapt it
            except Exception as e:
                sql_log.exception(f"Attempt {attempt}: Error getting from ProxyTab: {e}")

        # --- Check Result ---
        if proxy_tab:
            # Found a proxy, exit the infinite loop and return it
            return proxy_tab, used_available_proxy
        else:
            try:
                await get_proxy_methods.get_proxy()  # Fetch new proxies (likely puts into Redis)
                await SQLHelper.check_redis_data()
            except Exception as e:
                sql_log.exception(f"Attempt {attempt}: Error during proxy acquisition process: {e}")
            await asyncio.sleep(initial_retry_delay_seconds)
    proxy_tab = await SQLHelper.select_proxy("rand")
    return proxy_tab, used_available_proxy
    # The while True loop ensures this point is never reached if a proxy is eventually found.
    # If acquisition *never* yields a proxy, this function will wait forever.
