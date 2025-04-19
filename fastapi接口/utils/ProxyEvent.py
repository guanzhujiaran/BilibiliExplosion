import time

from fastapi接口.log.base_log import httpx_logger
from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab
from utl.代理.数据库操作.comm import get_scheme_ip_port_form_proxy_dict
import fastapi接口.service.grpc_module.Utils.GrpcRedis as GrpcRedis
import fastapi接口.service.MQ.base.MQClient.BiliLotDataPublisher as BiliLotDataPublisher

async def _check_ip_status(proxy_tab:ProxyTab):
    return await GrpcRedis.grpc_proxy_tools.get_ip_status_by_ip(
        get_scheme_ip_port_form_proxy_dict(proxy_tab.proxy)
    )

async def handle_proxy_succ(proxy_tab: ProxyTab|None):
    if not proxy_tab: return
    proxy_tab.status = 0
    ip_status = await _check_ip_status(proxy_tab)
    ip_status.available = True
    ip_status.code = 0
    await BiliLotDataPublisher.BiliLotDataPublisher.pub_upsert_proxy_info(
        ip_status=ip_status,
        proxy_tab=proxy_tab,
        change_score_num=10
    )


async def handle_proxy_request_fail(proxy_tab: ProxyTab|None):
    if not proxy_tab: return
    proxy_tab.status = -412
    ip_status = await _check_ip_status(proxy_tab)
    ip_status.available = False
    ip_status.code = -412
    await BiliLotDataPublisher.BiliLotDataPublisher.pub_upsert_proxy_info(
        ip_status=ip_status,
        proxy_tab=proxy_tab,
        change_score_num=-10
    )


async def handle_proxy_352(proxy_tab: ProxyTab|None):
    if not proxy_tab:return
    httpx_logger.error(f'代理：{proxy_tab.proxy}发生-352状况！')
    proxy_tab.status = -412
    ip_status = await _check_ip_status(proxy_tab)
    ip_status.code = -352
    ip_status.available = True
    ip_status.latest_352_ts = int(time.time())
    await BiliLotDataPublisher.BiliLotDataPublisher.pub_upsert_proxy_info(
        ip_status=ip_status,
        proxy_tab=proxy_tab,
        change_score_num=10
    )


async def handle_proxy_412(proxy_tab: ProxyTab|None):
    if not proxy_tab: return
    proxy_tab.status = -412
    ip_status = await _check_ip_status(proxy_tab)
    ip_status.code = -412
    ip_status.available = True
    await BiliLotDataPublisher.BiliLotDataPublisher.pub_upsert_proxy_info(
        ip_status=ip_status,
        proxy_tab=proxy_tab,
        change_score_num=10
    )


async def handle_proxy_unknown_err(proxy_tab: ProxyTab|None):
    if not proxy_tab: return
    ip_status = await _check_ip_status(proxy_tab)
    ip_status.code = -412
    ip_status.available = False
    proxy_tab.status = -412
    await BiliLotDataPublisher.BiliLotDataPublisher.pub_upsert_proxy_info(
        ip_status=ip_status,
        proxy_tab=proxy_tab,
        change_score_num=-10
    )
