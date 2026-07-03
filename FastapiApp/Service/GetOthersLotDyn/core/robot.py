import asyncio
from typing import Set

from log.base_log import get_others_lot_logger as get_others_lot_log
from Models.get_other_lot_dyn.dyn_robot_model import RobotScrapyInfo
from Service.GetOthersLotDyn.core.bili_dynamic_item import BiliDynamicItem
from Service.GetOthersLotDyn.fetcher.space_dynamic_fetcher import BiliSpaceUserItem
from CONFIG import settings
from Service.GetOthersLotDyn.Sql.models import TLotmaininfo
from Service.GetOthersLotDyn.Sql.sql_helper import SqlHelper, get_other_lot_redis_manager
from Service.opus新版官方抽奖.Model.BaseLotModel import ProgressCounter
from Utils.通用.Common import asyncio_gather
from Utils.数据库.SqlalchemyTool import sqlalchemy_model_2_dict


class GetOthersLotDynRobot:
    """
    获取其他人的抽奖动态
    """

    def __init__(self):
        self.isPreviousRoundFinished = False  # 上一轮抽奖是否结束
        self.nowRound: TLotmaininfo = TLotmaininfo()
        self.username = ''
        self.nonLotteryWords = ['分享视频', '分享动态']
        self.SpareTime = settings.get_others_lot.spare_time  # 多少时间以前的就不获取别人的动态了
        self.bili_space_user_items_set: Set[BiliSpaceUserItem] = set()
        self.bili_dynamic_items_set: Set[BiliDynamicItem] = set()
        self.scrapy_info = RobotScrapyInfo()
        self.space_succ_counter = ProgressCounter()
        self.dyn_succ_counter = ProgressCounter()
        self.goto_check_dynamic_item_set: Set[BiliDynamicItem] = set()

    # region 获取uidlist中的空间动态

    async def __do_space_task(self, __bili_space_user: BiliSpaceUserItem, isPubLotUser: bool):
        self.space_succ_counter.running_params.add(__bili_space_user.uid)
        await __bili_space_user.get_user_space_dynamic_id(
            isPubLotUser=isPubLotUser,
            SpareTime=self.SpareTime,
            succ_counter=self.space_succ_counter
        )
        self.space_succ_counter.running_params.discard(__bili_space_user.uid)
        self.space_succ_counter.succ_count += 1

    async def get_all_space_dyn_id(
            self,
            bili_space_user_items: Set[BiliSpaceUserItem],
            isPubLotUser=False
    ):
        self.space_succ_counter.total_num = len(bili_space_user_items)
        semaphore = asyncio.Semaphore(settings.get_others_lot.space_dyn_concurrency)

        async def _sem_task(item: BiliSpaceUserItem):
            async with semaphore:
                await self.__do_space_task(item, isPubLotUser)

        tasks = set()
        for i in bili_space_user_items:
            task = asyncio.create_task(
                _sem_task(i),
                name=f'{i.uid}'
            )
            tasks.add(task)
            task.add_done_callback(tasks.discard)
        await asyncio_gather(*tasks, log=get_others_lot_log)
        get_others_lot_log.info(f'完成{len(bili_space_user_items)}个用户的空间动态获取')
        self.space_succ_counter.is_running = False

    # endregion

    async def __init(self):
        async def init_round():
            latest_round = await SqlHelper.getLatestRound()
            if not latest_round:
                latest_round = TLotmaininfo(
                    lotRound_id=1,
                    allNum=0,
                    lotNum=0,
                    uselessNum=0,
                    isRoundFinished=False,
                )
                self.isPreviousRoundFinished = True
            elif latest_round.isRoundFinished:
                latest_round = TLotmaininfo(
                    lotRound_id=latest_round.lotRound_id + 1,
                    allNum=0,
                    lotNum=0,
                    uselessNum=0,
                    isRoundFinished=False,
                )
                self.isPreviousRoundFinished = True
            self.nowRound = latest_round
            get_others_lot_log.critical(
                f'当前抽奖获取轮次信息：{sqlalchemy_model_2_dict(latest_round)}')
            await SqlHelper.addLotMainInfo(latest_round)

        async def init_bili_space_user():
            if redis_data := await get_other_lot_redis_manager.get_target_uid_list():
                self.bili_space_user_items_set.update(
                    [BiliSpaceUserItem(
                        uid=x.uid, lot_round_id=self.nowRound.lotRound_id) for x in redis_data]
                )
            else:
                get_others_lot_log.critical('从Redis获取抽奖用户列表失败，使用内置默认用户列表')
                default_list = [
                    319857159,
                    14017844,
                    1234306704,
                    31497476,
                    2147319744,
                    410550169,
                    646686238,
                    71583520,
                    279262754,
                    275744172,
                    332793152,
                    1397970246,
                    3493092200024392,
                    386051299,
                    381282283,
                    20958956,
                    1869690859,
                    1183157743,
                    4586734,
                    1741486871,
                    266223923,
                    646327721,
                    1803790683,
                    8544035,
                    1123570168,
                    3494361237031878,
                    223712517,
                    480906586,
                    1040677577,
                    471565816,
                    343104186,
                    2204166,
                    290089137,
                    1855888816,
                    691536906,
                    6477408,
                    1586295950,
                    1369967146,
                    40809204,
                    1992326018,
                    649407876,
                    256316789,
                    143412922,
                    1278208248,
                    499023056,
                    565064296,
                    693445761,
                    7538278,
                    3546876406139528,
                    482187762
                ]
                self.bili_space_user_items_set.update(
                    [BiliSpaceUserItem(uid=x, lot_round_id=self.nowRound.lotRound_id) for x in default_list])

        await init_round()
        await init_bili_space_user()
        get_others_lot_log.info('机器人初始化完成')

    async def __judge_dynamic(self,
                              item: BiliDynamicItem,
                              lotRound_id: int,
                              ):
        """
        判断抽奖
        :param item:
        :param lotRound_id:
        :return:
        """
        self.dyn_succ_counter.running_params.add(self.__hash__())
        await item.judge_lottery(lotRound_id=lotRound_id)
        self.dyn_succ_counter.running_params.discard(self.__hash__())
        self.dyn_succ_counter.succ_count += 1
        return

    async def main(self):
        await self.__init()
        # 获取抽奖号的空间
        await self.get_all_space_dyn_id(self.bili_space_user_items_set, isPubLotUser=False)
        pub_lot_uid_set: Set[BiliSpaceUserItem] = set()
        for x in self.bili_space_user_items_set:
            pub_lot_uid_set.update(x.pub_lot_users)
        get_others_lot_log.critical(f'第一阶段完成，开始获取{len(pub_lot_uid_set)}个发起抽奖用户的空间动态')
        # 获取那些发起抽奖的人的空间
        await self.get_all_space_dyn_id(pub_lot_uid_set, isPubLotUser=True)
        total_lot_uid_set: Set[BiliSpaceUserItem] = set()
        total_lot_uid_set.update(self.bili_space_user_items_set)
        total_lot_uid_set.update(pub_lot_uid_set)
        get_others_lot_log.critical(f'第二阶段完成，共获取了{len(pub_lot_uid_set)}个发起抽奖用户的空间动态')
        for x in total_lot_uid_set:
            self.goto_check_dynamic_item_set.update(x.dynamic_infos)
            for y in x.pub_lot_users:
                self.goto_check_dynamic_item_set.update(y.dynamic_infos)

        get_others_lot_log.critical(
            f'共{len(self.goto_check_dynamic_item_set)}条动态待判断是否为抽奖')
        self.dyn_succ_counter.total_num = len(self.goto_check_dynamic_item_set)
        semaphore = asyncio.Semaphore(settings.get_others_lot.judge_dyn_concurrency)

        async def _sem_judge(item: BiliDynamicItem):
            async with semaphore:
                await self.__judge_dynamic(
                    item, self.nowRound.lotRound_id)

        tasks = set()
        for x in self.goto_check_dynamic_item_set:
            task = asyncio.create_task(
                _sem_judge(x),
                name=f'{x.dynamic_id} {x.dynamic_rid} {x.dynamic_type}'
            )
            tasks.add(task)
            task.add_done_callback(tasks.discard)
        await asyncio_gather(*tasks, log=get_others_lot_log)
        self.dyn_succ_counter.is_running = False
        await self._after_scrapy()
        self.nowRound.isRoundFinished = 1
        await SqlHelper.addLotMainInfo(self.nowRound)
        # 抽奖获取结束 尝试将这一轮获取到的非图片抽奖添加进数据库

    async def _after_scrapy(self):
        all_dyn_this_round = await SqlHelper.getAllLotDynInfoByRoundNum(self.nowRound.lotRound_id)
        all_t_lot_dyn_info = []
        all_useless_dyn_info = []
        for x in all_dyn_this_round:
            if x.isLot == 1:
                all_t_lot_dyn_info.append(x)
            else:
                all_useless_dyn_info.append(x)

        self.nowRound.allNum = len(all_dyn_this_round)
        self.nowRound.lotNum = len(all_t_lot_dyn_info)
        self.nowRound.uselessNum = len(all_useless_dyn_info)
        self.scrapy_info.all_lot_dyn_info_list = all_t_lot_dyn_info
        self.scrapy_info.all_useless_info_list = all_useless_dyn_info
