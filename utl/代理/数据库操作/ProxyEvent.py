from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab
from utl.代理.数据库操作.async_proxy_op_alchemy_mysql_ver import SQLHelper
from utl.代理.数据库操作.available_proxy_sql_helper import \
    sql_helper  # Assuming sql_helper is an instance of AvailableProxySqlHelper
from fastapi接口.log.base_log import sql_log  # Ensure log is available


async def handle_proxy_succ(proxy_tab: ProxyTab | None):
    """Handles logic when a proxy successfully makes a request."""
    if not proxy_tab:
        sql_log.warning("handle_proxy_succ called with None proxy_tab.")
        return
    proxy_tab.status = 0
    await SQLHelper.update_to_proxy_list(proxy_tab, change_score_num=10)
    await sql_helper.update_available_proxy_details(
        proxy_tab=proxy_tab,
        available=True,
        resp_code=0
    )


async def handle_proxy_352(proxy_tab: ProxyTab | None):
    """Handles logic when a proxy returns a -352 response code."""
    if not proxy_tab:
        sql_log.warning("handle_proxy_352 called with None proxy_tab.")
        return

    proxy_tab.status = -352
    await SQLHelper.update_to_proxy_list(proxy_tab, change_score_num=10)
    await sql_helper.update_available_proxy_details(
        proxy_tab=proxy_tab,
        available=True,  # Assuming -352 is a temporary state/challenge, not a permanent death
        resp_code=-352
    )


async def handle_proxy_412(proxy_tab: ProxyTab | None):
    """Handles logic when a proxy returns a -412 response code."""
    if not proxy_tab:
        sql_log.warning("handle_proxy_412 called with None proxy_tab.")
        return
    proxy_tab.status = -412
    await SQLHelper.update_to_proxy_list(proxy_tab, change_score_num=10)
    await sql_helper.update_available_proxy_details(
        proxy_tab=proxy_tab,
        available=True,  # Assuming -412 is a temporary state/block, not a permanent death
        resp_code=-412
    )


async def handle_proxy_request_fail(proxy_tab: ProxyTab | None):
    """
    Handles logic when a proxy fails a general request (e.g., connection error, timeout).
    Treats this as a hard failure and removes from AvailableProxy.
    """
    if not proxy_tab:
        sql_log.warning("handle_proxy_request_fail called with None proxy_tab.")
        return
    proxy_tab.status = -412
    await SQLHelper.update_to_proxy_list(proxy_tab, change_score_num=-10)
    available_proxy = await sql_helper.get_available_proxy_by_proxy_id(proxy_tab.proxy_id)
    if available_proxy:
        await sql_helper.delete_proxy_by_pk(available_proxy.pk)


async def handle_proxy_unknown_err(proxy_tab: ProxyTab | None):
    """
    Handles logic when a proxy encounters an unknown error.
    Treats this as a hard failure and removes from AvailableProxy.
    """
    if not proxy_tab:
        sql_log.warning("handle_proxy_unknown_err called with None proxy_tab.")
        return
    proxy_tab.status = -412
    await SQLHelper.update_to_proxy_list(proxy_tab, change_score_num=-10)  # Unknown error means failure
    available_proxy = await sql_helper.get_available_proxy_by_proxy_id(proxy_tab.proxy_id)
    if available_proxy:
        await sql_helper.delete_proxy_by_pk(available_proxy.pk)
