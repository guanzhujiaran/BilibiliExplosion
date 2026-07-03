import asyncio
import datetime
import time
from typing import Sequence

from log.base_log import get_others_lot_logger as get_others_lot_log
from CONFIG import settings
from Service.GetOthersLotDyn.core.robot import GetOthersLotDynRobot
from Service.GetOthersLotDyn.filter.lottery_filter import is_need_lot, solve_return_lot
from Service.GetOthersLotDyn.Sql.models import TLotmaininfo
from Service.GetOthersLotDyn.Sql.sql_helper import SqlHelper, TargetUserItem, get_other_lot_redis_manager
from Service.GrpcModule.Grpc.Bapi.BiliApi import get_reply_main
from Service.GrpcModule.GrpcSrc.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
from Service.GrpcModule.GrpcSrc.SQLObject.models import Lotdata
from Service.opus新版官方抽奖.预约抽奖.db.models import TUpReserveRelationInfo
from Service.opus新版官方抽奖.预约抽奖.db.sqlHelper import bili_reserve_sqlhelper as mysq
from Utils.推送.PushMe import a_pushme
from Utils.代理.mdoel.RequestConf import RequestConf


class GetOthersLotDyn:
    """
        获取更新的抽奖，如果时间在1天之内，那么直接读取文件获取结果，将结果返回回去
    """

    def __init__(self):
        self.is_getting_dyn_flag_lock = asyncio.Lock()
        self.is_getting_dyn_flag = False
        self.robot: GetOthersLotDynRobot | None = None
        self.get_dyn_ts = 0

    async def get_get_dyn_ts(self):
        get_dyn_ts = await get_other_lot_redis_manager.get_get_dyn_ts()
        if not get_dyn_ts:
            latest_round: TLotmaininfo | None = await SqlHelper.getLatestFinishedRound()
            if latest_round and latest_round.updated_at:
                return int(latest_round.updated_at.timestamp())
        return get_dyn_ts

    # region 主函数 （包括获取普通新抽奖，推送官方抽奖，推送大奖，推送预约抽奖）
    async def get_new_dyn(self) -> list[dict]:
        """
        主函数，获取一般最新的抽奖
        采集完成后自动管理用户列表并推送总结
        """
        while 1:
            async with self.is_getting_dyn_flag_lock:
                if self.is_getting_dyn_flag:
                    await asyncio.sleep(30)
                    continue
                else:
                    self.is_getting_dyn_flag = True
                    break
        self.get_dyn_ts = await self.get_get_dyn_ts()
        get_others_lot_log.info(
            f'上次获取第三方抽奖动态时间：{datetime.datetime.fromtimestamp(self.get_dyn_ts)}')
        if int(time.time()) - self.get_dyn_ts >= settings.get_others_lot.get_dyn_interval:
            self.robot = None
            self.robot = GetOthersLotDynRobot()
            await self.robot.main()
            await get_other_lot_redis_manager.set_get_dyn_ts(int(time.time()))
            # 数据采集完成后立即查库充实用户列表
            summary = await self._manage_user_list()
            # 推送本轮总结
            await self._push_round_summary(summary)
        self.is_getting_dyn_flag = False
        return await self.solve_return_lot()

    async def _get_users_from_latest_lot_dyn_comment(
        self, pick_count: int = 5, exclude_uids: set[int] | None = None
    ) -> list[TargetUserItem]:
        """从近期高互动抽奖动态的评论区挖掘潜在抽奖用户。
        按互动量排序，逐页翻评论直到数量够或没更多评论，自动跳过 exclude_uids 中的已存在用户。
        每个评论回复自带 member.uname，无需额外查库。

        :param pick_count: 目标用户数量
        :param exclude_uids: 已存在的 uid 集合，这些 uid 会被跳过
        :return: TargetUserItem 列表（uid + uname 已填充）
        """
        hot_dyn_days = settings.get_others_lot.hot_lot_dyn_days
        hot_dyn_count = settings.get_others_lot.hot_lot_dyn_count

        hot_dyns = await SqlHelper.getRecentHotLotDyns(
            days=hot_dyn_days, top_n=hot_dyn_count
        )
        if not hot_dyns:
            get_others_lot_log.warning('数据库中未找到近期高互动抽奖动态记录，无法从评论中获取用户')
            return []

        result: list[TargetUserItem] = []
        seen: set[int] = set(exclude_uids) if exclude_uids else set()

        for dyn in hot_dyns:
            dyn_id = str(dyn.dynId)
            # 从 rawJsonStr 解析 rid 与 type
            rid = None
            _type = None
            raw_json = dyn.rawJsonStr
            if raw_json:
                basic = raw_json.get('basic') or {}
                rid = basic.get('comment_id_str')
                comment_type = str(basic.get('comment_type', ''))
                _type = {
                    '17': '4', '1': '8', '11': '2', '12': '64',
                }.get(comment_type, '8')
            if not rid or not _type:
                get_others_lot_log.debug(
                    f'动态 dynamic_id={dyn_id} 的 rawJsonStr 中缺少 rid/type，跳过'
                )
                continue

            # 逐页翻评论，数量够了或没更多评论就停止
            pn = 1
            dyn_added = 0
            while len(result) < pick_count:
                try:
                    reply = await get_reply_main(
                        dyn_id, rid, pn, str(_type), mode=2,
                        request_conf=RequestConf(is_use_available_proxy=True)
                    )
                    if not reply or reply.get('code') != 0:
                        break
                    replies = reply.get('data', {}).get('replies', [])
                    if not replies:
                        break
                    for c in replies:
                        mid = c.get('mid')
                        if mid and int(mid) not in seen:
                            member = c.get('member') or {}
                            uname = member.get('uname', '')
                            result.append(TargetUserItem(uid=int(mid), uname=uname))
                            seen.add(int(mid))
                            dyn_added += 1
                            if len(result) >= pick_count:
                                break
                    pn += 1
                except Exception as e:
                    get_others_lot_log.debug(
                        f'获取动态 dynamic_id={dyn_id} 第{pn}页评论失败：{e}'
                    )
                    break

            if dyn_added > 0:
                get_others_lot_log.debug(
                    f'从动态 dynamic_id={dyn_id} ({dyn.commentCount}评{dyn.repostCount}转) '
                    f'{pn - 1}页评论中收集到{dyn_added}个新用户'
                )

            if len(result) >= pick_count:
                break

        if not result:
            get_others_lot_log.warning('所有近期高互动抽奖动态均未收集到评论用户')
            return []

        get_others_lot_log.info(
            f'从{hot_dyn_days}天内高互动抽奖动态的评论中收集到{len(result)}个用户: '
            f'{[f"{u.uid}({u.uname})" for u in result]}'
        )
        return result

    async def _supplement_users(self) -> dict:
        """补充阶段：从评论区挖掘新用户 + 从数据库充实用户信息。
        建议在数据采集完成后调用，给新用户留出采集窗口。

        :return: 补充摘要 {before_count, after_count, added, round_*, active_14d}
        """
        uid_list: list[TargetUserItem] = await get_other_lot_redis_manager.get_target_uid_list()
        summary = {
            'before_count': len(uid_list),
            'after_count': 0,
            'added': [],
            'round_id': None,
            'round_all': 0,
            'round_lot': 0,
            'round_useless': 0,
        }
        get_others_lot_log.info(f'[补充阶段] 当前列表: {summary["before_count"]}个用户')

        # 轮次信息
        latest_round = await SqlHelper.getLatestFinishedRound()
        if latest_round:
            summary['round_id'] = latest_round.lotRound_id
            summary['round_all'] = latest_round.allNum or 0
            summary['round_lot'] = latest_round.lotNum or 0
            summary['round_useless'] = latest_round.uselessNum or 0

        # --- 补充新用户 ---
        need_count = settings.get_others_lot.max_user_list_size - len(uid_list)
        if need_count > 0:
            existing = {item.uid for item in uid_list}
            new_users = await self._get_users_from_latest_lot_dyn_comment(
                pick_count=need_count, exclude_uids=existing
            )
            for user in new_users:
                uid_list.append(user)
                summary['added'].append(user.uid)

        # 兜底：如果列表仍为空，使用内置默认用户列表
        if not uid_list:
            defaults = settings.get_others_lot.default_user_uids
            get_others_lot_log.warning(
                f'[补充阶段] 评论区未收集到用户，使用默认用户列表 ({len(defaults)}个)')
            uid_list = [TargetUserItem(uid=uid) for uid in defaults]
            summary['added'] = defaults

        # --- 充实用户信息 ---
        uids = [item.uid for item in uid_list]
        last_round_id = latest_round.lotRound_id if latest_round else None

        latest_dyns = await SqlHelper.getLatestLotDynInfoByUidList(uids)
        latest_dyn_map: dict[int, tuple[int, datetime | None, str]] = {}
        for d in latest_dyns:
            if d.pubTime:
                latest_dyn_map[int(d.up_uid)] = (
                    int(d.pubTime.timestamp()),
                    d.pubTime,
                    d.authorName or "",
                )

        user_info_map = await SqlHelper.getLotUserInfoByUidList(uids)

        round_stats: dict[int, dict] = {}
        if last_round_id:
            round_stats = await SqlHelper.getUserLotStatsByRound(uids, last_round_id)

        no_uname_uids: list[int] = []
        for item in uid_list:
            uid = item.uid
            if not item.uname:
                dyn_info = latest_dyn_map.get(uid)
                if dyn_info:
                    item.uname = dyn_info[2] or ""
                if not item.uname and user_info_map.get(uid):
                    item.uname = user_info_map[uid].uname or ""

            dyn_info = latest_dyn_map.get(uid)
            if dyn_info:
                item.last_dyn_pub_ts = dyn_info[0]
                item.last_dyn_pub_datetime = dyn_info[1]

            if not item.uname:
                no_uname_uids.append(uid)

            stats = round_stats.get(uid, {})
            item.last_round_lot_count = int(stats.get('lot_count', 0))
            item.last_round_total_count = int(stats.get('total', 0))

        if no_uname_uids:
            get_others_lot_log.warning(
                f'[补充阶段] {len(no_uname_uids)}个用户未能获取到用户名: {no_uname_uids}'
            )

        # 持久化
        await get_other_lot_redis_manager.set_target_uid_list(uid_list)
        summary['after_count'] = len(uid_list)
        get_others_lot_log.info(
            f'[补充阶段] 完成: {summary["before_count"]} -> {summary["after_count"]}个用户 '
            f'(新增 {len(summary["added"])}个)'
        )
        return summary

    async def _cull_users(self) -> dict:
        """剔除阶段：按 N 天内有效抽奖数剔除低活跃用户。
        建议在补充之后调用，此时新用户已被爬虫采集过一轮数据。

        :return: 剔除摘要 {before_count, after_count, removed, active_14d}
        """
        uid_list: list[TargetUserItem] = await get_other_lot_redis_manager.get_target_uid_list()
        summary = {
            'before_count': len(uid_list),
            'after_count': 0,
            'removed': [],
            'active_14d': 0,
        }
        get_others_lot_log.info(f'[剔除阶段] 当前列表: {summary["before_count"]}个用户')

        if not uid_list:
            get_others_lot_log.warning('[剔除阶段] 列表为空，跳过')
            return summary

        uids = [item.uid for item in uid_list]
        counts_14d = await SqlHelper.countValidLotByUidInTimeRange(
            uids, days=settings.get_others_lot.remove_check_days
        )
        removed_items = [
            item for item in uid_list
            if counts_14d.get(item.uid, 0) <= settings.get_others_lot.min_valid_lot_threshold
        ]
        if removed_items:
            removed_uids = {item.uid for item in removed_items}
            summary['removed'] = [item.uid for item in removed_items]
            uid_list = [item for item in uid_list if item.uid not in removed_uids]
            get_others_lot_log.info(
                f'[剔除阶段] 按{settings.get_others_lot.remove_check_days}天内'
                f'阈值{settings.get_others_lot.min_valid_lot_threshold}剔除: {summary["removed"]}'
            )

        await get_other_lot_redis_manager.set_target_uid_list(uid_list)
        summary['after_count'] = len(uid_list)
        summary['active_14d'] = sum(
            1 for item in uid_list
            if counts_14d.get(item.uid, 0) > settings.get_others_lot.min_valid_lot_threshold
        )
        get_others_lot_log.info(
            f'[剔除阶段] 完成: {summary["before_count"]} -> {summary["after_count"]}个用户 '
            f'(活跃: {summary["active_14d"]})'
        )
        return summary

    async def _manage_user_list(self) -> dict:
        """管理用户列表：先剔除再补充，聚合两阶段摘要用于推送。"""
        cull = await self._cull_users()
        supp = await self._supplement_users()
        return {
            'before_count': supp['before_count'],
            'after_count': cull['after_count'],
            'added': supp['added'],
            'removed': cull['removed'],
            'active_14d': cull['active_14d'],
            'round_id': supp['round_id'],
            'round_all': supp['round_all'],
            'round_lot': supp['round_lot'],
            'round_useless': supp['round_useless'],
        }

    async def _push_round_summary(self, summary: dict):
        """推送本轮数据采集与用户管理的总结到 PushMe"""
        lines = [
            f"轮次ID: {summary['round_id']}",
            f"检查动态: {summary['round_all']}条 (有效抽奖 {summary['round_lot']}条, 无效 {summary['round_useless']}条)",
            f"用户列表: {summary['before_count']} -> {summary['after_count']}个",
        ]
        if summary['removed']:
            lines.append(f"剔除({settings.get_others_lot.remove_check_days}天活跃不足): {len(summary['removed'])}个 {summary['removed']}")
        if summary['added']:
            lines.append(f"新补充: {len(summary['added'])}个 {summary['added']}")
        lines.append(f"{settings.get_others_lot.remove_check_days}天活跃用户: {summary['active_14d']}个")

        title = f"第三方抽奖采集完成 - 轮次{summary['round_id']}"
        content = '\n'.join(lines)
        get_others_lot_log.info(f'推送总结: {title}\n{content}')
        await a_pushme(title, content, 'text')

    async def get_official_lot_dyn(self) -> list[str]:
        """
        返回官方抽奖信息，结尾是tab=1
        SVM 必抽判断通过独立批量查询 t_lot_extra_info 子表获取，与主表查询解耦
        :return:
        """
        recent_official_lot_data: Sequence[Lotdata] = await grpc_sql_helper.query_official_lottery_by_timelimit(
            time_limit=30 * 24 * 3600,
            order_by_ts_desc=False
        )
        # 批量查询 extra_info，一次 SQL 得到所有结果
        extra_map = await grpc_sql_helper.get_extra_info_map(
            [x.lottery_id for x in recent_official_lot_data]
        )
        ret_list = []
        for x in recent_official_lot_data:
            if x.lottery_id in extra_map and extra_map[x.lottery_id].is_grand_prize == 1:
                # 忽略两天以内的
                if x.lottery_time - int(time.time()) < 2 * 3600 * 24:
                    continue
                ret_list.append(
                    f'https://t.bilibili.com/{x.business_id}?tab=1')
        if ret_list:
            await a_pushme(
                f"必抽的官方抽奖【{len(ret_list)}】条", '\n'.join(ret_list),
                'text'
            )
        return ret_list

    async def get_unignore_Big_lot_dyn(
        self, time_limit: int | None = None
    ) -> list[str]:
        """
        获取必抽的大奖，SVM 判断结果从 t_lot_extra_info 子表读取
        :return:
        """
        all_lot = await SqlHelper.getAllLotDynByTimeLimit()
        all_lot = [x for x in all_lot if is_need_lot(x, self.get_dyn_ts)]
        if not all_lot:
            return []
        dyn_ids = [int(x.dynId) for x in all_lot]
        grand_prize_flags = await SqlHelper.get_extra_info_by_ref_ids(dyn_ids, "common")
        ret_list = []
        for x in all_lot:
            if grand_prize_flags.get(int(x.dynId), 0) == 1:
                ret_list.append(x.dynamicUrl)
        if ret_list:
            await a_pushme(
                f"必抽的大奖【{len(ret_list)}】条", '\n'.join(ret_list),
                'text'
            )
        return ret_list

    async def get_unignore_reserve_lot_space(self) -> list[TUpReserveRelationInfo]:
        all_lots = await mysq.get_all_available_reserve_lotterys()
        recent_lots: list[TUpReserveRelationInfo] = [x for x in all_lots if
                                                     x.etime and x.etime - int(time.time()) < 2 * 3600 * 24]
        ret_list = []
        ret_info_list = []
        for x in recent_lots:
            if x.is_grand_prize == 1:
                ret_info_list.append(
                    ' '.join([f'https://space.bilibili.com/{x.upmid}/dynamic', x.text]))
                ret_list.append(x)
        if ret_info_list:
            await a_pushme(
                f"必抽的预约抽奖【{len(ret_info_list)}】条", '\n'.join(ret_info_list),
                'text'
            )
        return ret_list

    # endregion

    # region 获取抽奖csv里的数据
    async def solve_return_lot(
        self, time_limit: int | None = None
    ) -> list[dict]:
        """
        解析并过滤抽奖，直接从数据库读取，按插入时间过滤，按动态发布时间排序
        委托给 lottery_filter.solve_return_lot 独立函数
        :return:
        """
        return await solve_return_lot(
            time_limit=time_limit or settings.get_others_lot.dyn_time_limit,
            get_dyn_ts=self.get_dyn_ts,
        )

    # endregion


get_others_lot_dyn = GetOthersLotDyn()

if __name__ == '__main__':
    async def _test_main():
        await get_others_lot_dyn.get_new_dyn()

    async def _test_supplement():
        summary = await get_others_lot_dyn._supplement_users()
        print(summary)

    async def _test_cull():
        summary = await get_others_lot_dyn._cull_users()
        print(summary)


    # asyncio.run(_test_supplement())
    # asyncio.run(_test_cull())
    asyncio.run(_test_supplement())
