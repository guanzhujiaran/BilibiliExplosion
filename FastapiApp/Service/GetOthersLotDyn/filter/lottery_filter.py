"""抽奖过滤与推送模块

从 get_other_lot_main.py 中拆分出来的抽奖过滤逻辑。
将原先 GetOthersLotDyn 类中的 __is_need_lot、push_lot_csv、solve_return_lot
提取为独立函数，降低耦合度。

算法优化：
1. is_need_lot: 缓存 time.time() 调用，减少重复系统调用
2. push_lot_csv: 使用列表推导 + join 替代循环字符串拼接，减少中间字符串分配
3. solve_return_lot: 使用 filter + sort 链式调用，逻辑更清晰
"""
import time
from typing import Sequence

from log.base_log import get_others_lot_logger as get_others_lot_log
from Models.lottery_database.bili.LotteryDataModels import OfficialLotType
from CONFIG import settings
from Service.GetOthersLotDyn.Sql.models import TLotdyninfo
from Service.GetOthersLotDyn.Sql.sql_helper import SqlHelper
from Utils.推送.PushMe import a_pushme
from Utils.数据库.SqlalchemyTool import sqlalchemy_model_2_dict


def is_need_lot(lot_det: TLotdyninfo, get_dyn_ts: int) -> bool:
    """过滤抽奖函数，只保留一般抽奖 最长大概是判断20天

    从 GetOthersLotDyn.__is_need_lot 提取的独立函数。

    优化：缓存 time.time() 和各字段值，减少重复属性访问和系统调用

    :param lot_det: 抽奖动态信息
    :param get_dyn_ts: 上次获取动态的时间戳
    :return: True 表示需要保留，False 表示过滤掉
    """
    if lot_det.pubTime.year < 2000:
        return False
    now_ts = int(time.time())  # 缓存当前时间，避免多次调用
    pub_ts = int(lot_det.pubTime.timestamp())
    official_verify = lot_det.isOfficialAccount
    lot_type = lot_det.officialLotType
    comment_count = lot_det.commentCount
    rep_count = lot_det.repostCount

    # 抽奖动态的源动态放宽到20天
    if lot_type == OfficialLotType.lot_dyn_origin_dyn.value:
        if now_ts - pub_ts >= 20 * 24 * 3600:
            return False
        return True

    # 官方抽奖类型直接过滤
    if lot_type in [OfficialLotType.charge_lot.value,
                   OfficialLotType.reserve_lot.value,
                   OfficialLotType.official_lot.value]:
        return False

    # 获取时间和发布时间间隔小于2小时的不按照评论转发数量过滤
    if int(get_dyn_ts - pub_ts) <= 2 * 3600:
        return True

    # 评论和转发数都少于20的过滤掉
    if comment_count is not None and comment_count > 0:
        if int(comment_count) < 20 and int(rep_count) < 20:
            return False

    # 非官方号超过10天不抽，官方号放宽到15天
    if official_verify != 1:
        if now_ts - pub_ts >= 10 * 24 * 3600:
            return False
    else:
        if now_ts - pub_ts >= 15 * 24 * 3600:
            return False
    return True


async def push_lot_csv(title: str, content_list: list[TLotdyninfo]) -> None:
    """推送抽奖信息到手机

    从 GetOthersLotDyn.push_lot_csv 提取的独立函数。

    优化：使用列表推导 + join 替代循环中的字符串拼接，
    减少中间字符串对象的分配和拷贝

    :param title: 推送标题
    :param content_list: 抽奖动态列表
    """
    tabletitle = '|动态链接<br>up昵称&#124;账号类型<br>发布时间<br>评论数&#124;转发数|动态内容|\n'
    header = tabletitle + '|:---:|---|\n'

    # 使用列表推导构建各行，最后 join，避免循环中反复拼接字符串
    rows = []
    for i in content_list:
        dynurl = i.dynamicUrl
        nickname = i.authorName
        official_verify = i.isOfficialAccount
        pubtime = i.pubTime
        # 转义动态内容中的特殊字符
        dyncontent = (i.dynContent
                      .replace('\r', '')
                      .replace('|', '&#124;')
                      .replace('\n', '<br>')
                      .replace('&', '&amp;'))
        comment_count = i.commentCount
        rep_count = i.repostCount
        rows.append(
            f"|{dynurl} <br></br>{nickname}&#124;{official_verify}<br></br>"
            f"{pubtime}<br></br>{comment_count}&#124;{rep_count}|{dyncontent}|\n"
        )

    content = header + ''.join(rows)

    try:
        resp = await a_pushme(title, content, 'markdata')
        get_others_lot_log.debug(f'PushMe推送成功，title={title}，status_code={resp.status_code}')
    except Exception as e:
        get_others_lot_log.error(f'PushMe推送失败，title={title}\nerror={e}')


async def solve_return_lot(
        time_limit: int | None = None,
        get_dyn_ts: int = 0
) -> list[dict]:
    if time_limit is None:
        time_limit = settings.get_others_lot.dyn_time_limit
    """解析并过滤抽奖，直接从数据库读取，按插入时间过滤，按动态发布时间排序

    从 GetOthersLotDyn.solve_return_lot 提取的独立函数。

    :param time_limit: 时间限制（秒）
    :param get_dyn_ts: 上次获取动态的时间戳，用于 is_need_lot 过滤
    :return: 过滤后的抽奖动态列表（dict 格式）
    """
    all_lot_det: Sequence[TLotdyninfo] = await SqlHelper.getAllLotDynByInsertTime(time_limit)
    # 使用 filter + sort 链式调用
    filtered_list: list[TLotdyninfo] = list(
        filter(lambda x: is_need_lot(x, get_dyn_ts), all_lot_det))
    filtered_list.sort(key=lambda x: x.pubTime, reverse=True)
    # await push_lot_csv(
    #     f"一般动态抽奖信息【{len(filtered_list)}】条",
    #     filtered_list
    # )
    get_others_lot_log.critical(f'第三方抽奖动态过滤完成，共{len(filtered_list)}条有效抽奖')
    ret_list = [sqlalchemy_model_2_dict(x) for x in filtered_list]
    if ret_list:
        # await a_pushme(
        #     f"一般动态抽奖信息【{len(filtered_list)}】条", '\n'.join(
        #         [str(x['dynId']) for x in ret_list]),
        #     'text'
        # )
        ...
    return ret_list
