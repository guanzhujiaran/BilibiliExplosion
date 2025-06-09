import asyncio
import datetime
import json
import os.path
import time
from dataclasses import field, dataclass
from typing import Dict, Tuple
from loguru import logger
from Bilibili_methods.all_methods import methods as Bilimethods
from fastapi接口.service.toutiao.src.Tools.ApiTools.APIRespTool import FeedListApi, FeedData, CellType
from fastapi接口.service.toutiao.src.Tools.Common.ZlibToos import strToBlob
from fastapi接口.service.toutiao.src.Tools.ApiTools.API import ToutiaoAPI
from fastapi接口.service.toutiao.src.db.SqlHelper import SqlHelperSpaceFeedDataDb
from fastapi接口.service.toutiao.src.db.models import TFEEDDATA

current_dir = os.path.dirname(__file__)


def get_file_p(file_relative_path: str):
    return os.path.join(current_dir, file_relative_path)


def Singleton(cls):
    _instance = {}

    def _singleton(*args, **kargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
        return _instance[cls]

    return _singleton


@dataclass
class FileMapClass:
    spiderSetting: str = field(default_factory=lambda: get_file_p('../spiderSetting.json'))
    AllIdList: str = field(default_factory=lambda: get_file_p('AllIdList.txt'))
    AllLotIdList: str = field(default_factory=lambda: get_file_p('AllLotIdList.txt'))
    rsult_latest: str = field(default_factory=lambda: get_file_p('../../SpaceFeedLot/result/latest.csv'))
    log_all: str = field(default_factory=lambda: get_file_p('../../SpaceFeedLot/log/all.csv'))
    last_spider_user_id_recorder: str = field(
        default_factory=lambda: get_file_p('../../SpaceFeedLot/last_spider_user_id_recorder.json'))
    last_get_lot_id_timestamp: str = field(
        default_factory=lambda: get_file_p('../../FastApiReturns/SpaceFeedLotService/last_get_lot_id_timestamp.txt')
    )


FileMap = FileMapClass()


@dataclass
class LastIdResult:
    latest_id_list: list[int] = field(default_factory=list)
    update_num: int = 0
    max_behot_time: int = 0


@dataclass
class ScrapedDataContainer:
    '''
    存放爬虫数据，尽可能减少内存的使用
    '''
    FeedDataList: list[FeedData] = field(default_factory=list)
    AllIdList: list[int] = field(default_factory=list)
    AllLotIdList: list[int] = field(default_factory=list)


@dataclass
class LotDataInfo:
    id: int
    jumpUrl: str
    user_id: str
    name: str
    official_verify: str
    content: str
    publish_Date: str


@Singleton
class ToutiaoSpaceFeedSpider:
    def __init__(self):
        self.BAPI = Bilimethods()
        self.container_lock = asyncio.Lock()
        self.last_spider_user_id_recorder: Dict[str, LastIdResult] = dict()
        self.newest_spider_user_id_recorder: Dict[str, LastIdResult] = dict()
        self.API = ToutiaoAPI()
        self.SQLHelper = SqlHelperSpaceFeedDataDb()
        self.container = ScrapedDataContainer()
        self.load_config()
        self.load_last_spider_result()

    def load_config(self):
        self.user_id_list = [
            "MS4wLjABAAAAId3gSYI86COJ6zrfKfjPXzFU-DMsR5gFu1cpcNzG690",
            'MS4wLjABAAAAzPC55Y5v2l2OE-EHAwjyCUyQ_pP_1HFUoWe-28ttrkWJzr_AyONMq8fJs8SGGhYX',
            'MS4wLjABAAAAE5JRY_o4_nq1UReBY8p0VPDSt3XQ1FGO5cqVquWsUz4'
        ]
        self.max_sep_time = 7 * 24 * 3600
        with open(FileMap.spiderSetting, 'r', encoding='utf-8') as f:
            try:
                setting = json.load(f)
                if setting.get('max_sep_time'):
                    self.max_sep_time = setting.get('max_sep_time')
                if setting.get('user_id_list'):
                    self.user_id_list = setting.get('user_id_list')
            except Exception:
                logger.error(f'读取配置文件出错，请检查文件格式是否正确！')

    def load_last_spider_result(self):

        # region 获取上次的用户空间记录
        with open(FileMap.last_spider_user_id_recorder, 'r', encoding='utf-8') as f:
            self.last_spider_user_id_recorder: Dict[str, LastIdResult] = json.load(f)
        for k, v in self.last_spider_user_id_recorder.items():
            self.last_spider_user_id_recorder.update({
                k: LastIdResult(**v)
            })
        for i in self.user_id_list:
            if i not in list(self.last_spider_user_id_recorder.keys()):
                self.last_spider_user_id_recorder.update({
                    i: LastIdResult()
                })
        for i in list(self.last_spider_user_id_recorder.keys()):
            if i not in self.user_id_list:
                self.last_spider_user_id_recorder.pop(i)
        for k, v in self.last_spider_user_id_recorder.items():
            self.newest_spider_user_id_recorder.update({
                k: LastIdResult()
            })
        # endregion

        # region 读取文件中记录的所有获取过的id
        with open(FileMap.AllIdList, 'r', encoding='utf-8') as f:
            for i in f.readlines():
                for j in i.split(','):
                    if j.strip():
                        self.container.AllIdList.append(int(j.strip()))

        with open(FileMap.AllLotIdList, 'r', encoding='utf-8') as f:
            for i in f.readlines():
                for j in i.split(','):
                    if j.strip():
                        self.container.AllLotIdList.append(int(j.strip()))

        # endregion

    # region 获取单个用户的空间
    async def save_feed_data_to_db(self, f: FeedListApi):
        data_list = f.RespDict.get('data')
        for i in range(len(f.UsefulInfo.data)):
            da = f.UsefulInfo.data[i]
            if await self.SQLHelper.is_id_exists(da.id):
                pass
            else:
                FEED = TFEEDDATA(
                    id=da.id,
                    publish_time=da.publish_time,
                    zippedData=strToBlob(json.dumps(data_list[i]))
                )
                await self.SQLHelper.add_feed_data(FEED)

    def checkPreviousRoundIdEncountered(self, user_id, resp: FeedListApi) -> Tuple[
        bool, int, list[FeedData], list[int]]:
        '''
        是否遇到上一轮获取过的id
        :param user_id:
        :param resp:
        :return: 是否重复 重复的数量 未重复的内容FeedData ,所有的id
        '''
        id_list: list[int] = list(map(lambda x: x.id, resp.UsefulInfo.data))
        last_id_list: list[int] = self.last_spider_user_id_recorder[user_id].latest_id_list
        duplicatedIdDict = set(id_list) & set(last_id_list)
        uniqueFeedDataList = list(map(lambda x: x.id not in list(duplicatedIdDict), resp.UsefulInfo.data))
        if duplicatedIdDict:
            return True, len(duplicatedIdDict), uniqueFeedDataList, id_list
        return False, 0, uniqueFeedDataList, id_list

    async def add_FeedData_list_to_container(self, fd_list: list[FeedData]):
        async with self.container_lock:
            fd_id_list = list(map(lambda x: x.id, self.container.FeedDataList))
            for fd in fd_list:
                if fd.id in fd_id_list or fd.id in self.container.AllIdList:
                    pass
                else:
                    fd_id_list.append(fd.id)
                    self.container.FeedDataList.append(fd)
                    self.container.AllIdList.append(fd.id)

    async def getSpaceFeed(self, user_id: str):
        max_behot_time = 0
        update_num = 0
        first_round_flag = True
        has_more = True
        publish_time = int(time.time())
        while 1:
            resp = await self.API.getUserFeed(user_id, max_behot_time)
            await self.save_feed_data_to_db(resp)
            check_result = self.checkPreviousRoundIdEncountered(user_id, resp)
            update_num += len(resp.UsefulInfo.data) - check_result[1]
            if first_round_flag:
                self.newest_spider_user_id_recorder[user_id].latest_id_list = check_result[3]
                self.newest_spider_user_id_recorder[user_id].max_behot_time = max_behot_time
                first_round_flag = False
            max_behot_time = resp.UsefulInfo.max_behot_time
            await self.add_FeedData_list_to_container(resp.UsefulInfo.data)  # 添加进爬虫数据里面
            if resp.UsefulInfo.data:
                publish_time = resp.UsefulInfo.data[-1].publish_time
            has_more = resp.UsefulInfo.has_more

            # 终止条件
            if check_result[0]:
                logger.info(f'{user_id}：遇到上一轮有过的动态了！停止继续获取用户空间！')
                break
            if not has_more:
                logger.info(f'{user_id}：当前空间没有更多动态了！停止继续获取用户空间！')
                break
            if int(time.time()) - publish_time >= self.max_sep_time:
                logger.info(
                    f'{user_id}(总获取数目：{update_num}条)：{datetime.datetime.fromtimestamp(publish_time)}超过最长间隔时间{self.max_sep_time}秒！停止继续获取用户空间！')
                break
        self.newest_spider_user_id_recorder[user_id].update_num = update_num

    # endregion

    def round_end(self):
        lot_data_list = self.solve_all_FeedData()
        with open(FileMap.rsult_latest, 'w', encoding='utf-8') as f:
            for i in lot_data_list:
                f.writelines('\t'.join(list(map(str, i.__dict__.values()))) + '\n')
        if os.path.exists(FileMap.log_all):
            mode = 'a+'
        else:
            mode = 'w'
        with open(FileMap.log_all, mode, encoding='utf-8') as f:
            for i in lot_data_list:
                f.writelines('\t'.join(list(map(str, i.__dict__.values()))) + '\n')

        with open(FileMap.AllIdList, 'w', encoding='utf-8') as f:
            f.writelines(','.join(list(map(str, self.container.AllIdList[-10000000:]))))
        with open(FileMap.AllLotIdList, 'w', encoding='utf-8') as f:
            f.writelines(','.join(list(map(str, self.container.AllLotIdList[-10000000:]))))
        temp1 = {}
        for k, v in self.newest_spider_user_id_recorder.items():
            temp1.update({k: v.__dict__})
        with open(FileMap.last_spider_user_id_recorder, 'w', encoding='utf-8') as f:
            f.write(json.dumps(temp1, indent=4))

    def solve_all_FeedData(self) -> list[LotDataInfo]:
        lot_data_list: list[LotDataInfo] = []
        for fd in self.container.FeedDataList:
            if fd.cell_type == CellType.视频.value:
                continue
            elif fd.cell_type == CellType.文章.value:
                continue
            elif fd.cell_type == CellType.微头条.value:
                continue
            elif fd.cell_type == CellType.评论转发详情.value:
                origin_thread = fd.origin_thread
                if origin_thread:
                    if origin_thread.thread_id in self.container.AllLotIdList:
                        continue
                    self.container.AllLotIdList.append(origin_thread.thread_id)
                    content = origin_thread.content + origin_thread.title
                    jumpUrl = origin_thread.jumpUrl()
                    name = origin_thread.user.name
                    publish_time = origin_thread.publish_time
                    publish_Date = datetime.datetime.fromtimestamp(publish_time).strftime('%Y-%m-%d %H:%M:%S')
                    user_id = origin_thread.user.user_id
                    if self.BAPI.choujiangxinxipanduan(content):
                        logger.info(f'''
---------------------------------
【不是抽奖】
发布者：{name}  {origin_thread.user.jumpUrl()}
发布时间：{publish_Date}
{jumpUrl} 
内容：{content}
++++++++++++++++++++++++++++++++++
''')
                        continue
                    logger.debug(f'''
---------------------------------
【抽奖】
发布者：{name}  {origin_thread.user.jumpUrl()}
发布时间：{publish_Date}
{jumpUrl} 
内容：{content}
++++++++++++++++++++++++++++++++++
                    ''')
                    _id = origin_thread.thread_id
                    official_verify = origin_thread.user.verified_content
                    lot_data = LotDataInfo(
                        id=_id,
                        jumpUrl=jumpUrl,
                        user_id=user_id,
                        name=name,
                        official_verify=official_verify,
                        content=repr(content),
                        publish_Date=publish_Date
                    )
                    lot_data_list.append(lot_data)
        logger.info(
            f'最终结果：\n抽奖动态：{len(lot_data_list)}条\n全部动态：{len(self.container.FeedDataList)}条\n抽奖动态率：{round((len(lot_data_list) / (len(self.container.FeedDataList)) * 100 + 1), 2)}%')
        return lot_data_list

    async def main(self):
        task_list = []
        self.load_config()
        logger.info(f'开始获取{self.user_id_list}')
        for i in self.user_id_list:
            task = asyncio.create_task(self.getSpaceFeed(i))
            task_list.append(task)
        await asyncio.gather(*task_list, return_exceptions=False)
        self.round_end()


if __name__ == '__main__':
    print(FileMap.spiderSetting)
