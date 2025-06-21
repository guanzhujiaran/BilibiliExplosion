# -*- coding: utf-8 -*-
import copy
import datetime
import json
import os
import random
import time
from typing import List, Sequence
from bs4 import BeautifulSoup
from fastapi接口.log.base_log import topic_lot_logger
from fastapi接口.utils.Common import asyncio_gather
import b站cookie.globalvar as gl
from CONFIG import CONFIG
from fastapi接口.service.opus新版官方抽奖.Base.generate_cv import GenerateCvBase
from fastapi接口.service.opus新版官方抽奖.Model.GenerateCvModel import CvItem, LotType, CvContent, Color, CvContentOps, \
    CvContentAttr, CutOff
from fastapi接口.service.opus新版官方抽奖.活动抽奖.话题抽奖.SqlHelper import topic_sqlhelper
from fastapi接口.service.opus新版官方抽奖.活动抽奖.话题抽奖.db.models import TTrafficCard
from fastapi接口.service.opus新版官方抽奖.活动抽奖.model.EraBlackBoard import EraTask, EraLotteryConfig, \
    EraVideoSourceCONFIG, \
    H5ActivityLottery, H5ActivityLotteryGiftSource, MatchLotteryTask, MatchLottery, EvaContainerTruck
from utl.pushme.pushme import pushme
import asyncio
from utl.代理.SealedRequests import my_async_httpx
from py_mini_racer import MiniRacer

class GenerateTopicLotCv(GenerateCvBase):

    def __init__(self, cookie, ua, csrf, buvid, abstract: str = ''):
        super().__init__(cookie, ua, csrf, buvid)
        self.post_flag = True  # 是否直接发布
        self.sql = topic_sqlhelper
        self.abstract = abstract  # 只会添加在手动发布的里面，自动的太麻烦了

    def zhuanlan_format(self, lottery_infos: dict[str, List[CvItem]],
                        blank_space: int = 1, sep_str: str = ' ') -> (CvContent, int):
        """

        :param sep_str: 行间分隔符
        :param lottery_infos:
        :param blank_space: 开头空几行
        :return:
        {"ops":[{"attributes":{"color":"#017001"},"insert":"2024-09-22 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/activity-DOSZAhGE1R.html"},"insert":"动感潮玩迎新会"},{"attributes":{"color":"#017001"},"insert":"  未知"},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#b41700"},"insert":"2024-08-31 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/activity-iAdZHSzJDJ.html"},"insert":"带着平板去写生"},{"attributes":{"color":"#b41700"},"insert":"  h5转盘抽奖 小米加湿器|小爱音箱Play |舒客 声波电动牙刷T2新款|舒客 声波电动牙刷T2新款|倍思 苹果磁吸充电宝|华为长续航蓝牙耳机|华为MatePad SE平板|雷蛇炼狱蝰蛇电竞游戏鼠标"},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#18e7cf"},"insert":"2024-09-01 00:00截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/activity-7wGYoF1pjb.html"},"insert":"我在漫展跳宅舞-夏日活动"},{"attributes":{"color":"#18e7cf"},"insert":" 未知"},{"attributes":{"list":"ordered"},"insert":"\n"}]}
        """

        ret: CvContent = CvContent(ops=[])
        words = 0
        for key_name, section in lottery_infos.items():
            selected_color_class_key = random.choice(list(Color))
            ops_list = []
            ops = CvContentOps(
                insert=key_name,
                attributes=CvContentAttr(color=selected_color_class_key)
            )
            words += len(key_name)
            ops_list.append(ops)
            ret.ops.extend(ops_list)
            ret.ops.append(
                CvContentOps(
                    insert="\n"
                )
            )
            for cv_item in section:
                selected_color_class_key = random.choice(list(Color))
                ops_list = []
                _str = cv_item.end_date_str + sep_str
                ops = CvContentOps(
                    insert=_str,
                    attributes=CvContentAttr(color=selected_color_class_key)
                )
                words += len(_str)
                ops_list.append(ops)
                _str = cv_item.title + sep_str
                ops = CvContentOps(
                    insert=_str,
                    attributes=CvContentAttr(link=cv_item.jumpUrl)
                )
                words += len(_str)
                ops_list.append(ops)
                _str = sep_str
                ops = CvContentOps(
                    insert=_str,
                )
                ops_list.append(ops)
                if cv_item.lot_type_list:
                    _str = '|'.join([x.value for x in cv_item.lot_type_list]) + sep_str
                    ops = CvContentOps(
                        insert=_str,
                        attributes=CvContentAttr(color=selected_color_class_key)
                    )
                    words += len(_str)
                    ops_list.append(ops)
                if cv_item.lottery_pool:
                    _str = '|'.join([x for x in cv_item.lottery_pool[0:3]]) + sep_str
                    ops = CvContentOps(
                        insert=_str,
                        attributes=CvContentAttr(color=selected_color_class_key)
                    )
                    words += len(_str)
                    ops_list.append(ops)
                if cv_item.lottery_sid:
                    _str = cv_item.lottery_sid + sep_str
                    ops = CvContentOps(
                        insert=_str,
                        attributes=CvContentAttr(link=cv_item.jumpUrl)
                    )
                    words += len(_str)
                    ops_list.append(ops)
                ops = CvContentOps(
                    insert="\n",
                    attributes=CvContentAttr(list="ordered")
                )
                words += 1
                ops_list.append(ops)
                ret.ops.extend(ops_list)
            for _ in range(blank_space):
                cut_off_ops = CvContentOps(
                    attributes=CvContentAttr(**{"class": "cut-off"}),
                    insert=CutOff.cut_off_5.value
                )
                ret.ops.append(cut_off_ops)
        ret.ops.append(
            CvContentOps(
                insert="\n"
            )
        )
        return ret, words

    def zhuanlan_date_sort(self, cv_items: List[CvItem]) -> (List[CvItem], List[CvItem], List[CvItem], List[CvItem]):
        activity = []
        dynamic = []
        era = []
        unknown = []
        for x in cv_items:
            if '/activity-' in x.jumpUrl:
                if LotType.unknown in x.lot_type_list:
                    activity.append(x)
                else:
                    activity.insert(0, x)
            elif 'dynamic/' in x.jumpUrl:
                if LotType.unknown in x.lot_type_list:
                    dynamic.append(x)
                else:
                    dynamic.insert(0, x)
            elif 'era/' in x.jumpUrl:
                if LotType.unknown in x.lot_type_list:
                    era.append(x)
                else:
                    era.insert(0, x)
            else:
                unknown.append(x)
        activity.sort(key=lambda x: len(x.lot_type_list), reverse=True)
        dynamic.sort(key=lambda x: len(x.lot_type_list), reverse=True)
        era.sort(key=lambda x: len(x.lot_type_list), reverse=True)
        unknown.sort(key=lambda x: len(x.lot_type_list), reverse=True)
        return activity, dynamic, era, unknown

    @staticmethod
    def gen_cv_item(x: TTrafficCard) -> CvItem:
        cv_item = CvItem(
            jumpUrl=x.jump_url,
            title=x.name,
            end_date_str=x.card_desc
        )
        try:
            if x.t_activity_lottery:
                cv_item.lot_type_list.append(LotType.activity_lottery)
                cv_item.lottery_sid = ' | '.join(
                    [t_activity_lottery.lotteryId for t_activity_lottery in x.t_activity_lottery])
                for t_activity_lottery in x.t_activity_lottery:
                    cv_item.lottery_pool.extend([json.loads(y).get('name', '') for y in t_activity_lottery.list])
                    cv_item.lottery_sid += t_activity_lottery.lotteryId
            if x.t_activity_match_lottery:
                cv_item.lot_type_list.append(LotType.activity_match_lottery)
            if x.t_activity_match_task:
                cv_item.lot_type_list.append(LotType.activity_match_task)
            if x.t_era_jika:
                cv_item.lot_type_list.append(LotType.era_jika)
            if x.t_era_lottery:
                cv_item.lot_type_list.append(LotType.era_lottery)
                cv_item.lottery_sid = ' | '.join([t_era_lottery.activity_id for t_era_lottery in x.t_era_lottery])
                for t_era_lottery in x.t_era_lottery:
                    cv_item.lottery_pool.extend([json.loads(y).get('name', '') for y in t_era_lottery.gifts])
            if x.t_era_task:
                cv_item.lot_type_list.append(LotType.era_task)
            if x.t_era_video:
                for t_era_video in x.t_era_video:
                    if t_era_video.poolList:
                        cv_item.lot_type_list.append(LotType.era_video)
            if not cv_item.lot_type_list:
                cv_item.lot_type_list.append(LotType.unknown)

        except Exception as e:
            topic_lot_logger.exception(f'解析话题失败！{e}')
        return cv_item

    async def get_topic_lottery(self) -> List[CvItem]:

        all_traffic_card = await self.sql.get_all_available_traffic_info()
        ret_list = []
        for __x in all_traffic_card:
            ret_list.append(GenerateTopicLotCv.gen_cv_item(__x))
        return ret_list

    async def main(self, pub_cv: bool = True):
        """

        :param pub_cv: 是否直接发布专栏
        :return:
        """
        topic_lottery_list = await self.get_topic_lottery()
        activity, dynamic, era, unknown = self.zhuanlan_date_sort(topic_lottery_list)
        cv_content, words = self.zhuanlan_format({'activity网址': activity,
                                                  'dynamic网址': dynamic,
                                                  'era网址': era,
                                                  '未知网址': unknown
                                                  })
        today = datetime.datetime.today()
        _ = datetime.timedelta(days=1)
        next_day = today + _
        title = f'【{next_day.date().month}.{next_day.date().day}】话题抽奖信息'
        if pub_cv:
            local_title = title + '_需要提交'
        else:
            local_title = title
        self.save_article_to_local(local_title + '_api_ver', cv_content.rawContent)
        self.save_article_to_local(local_title + '_手动专栏_ver', self.abstract + cv_content.manualSubmitContent)
        aid = 0
        if pub_cv:
            aid = await self.article_creative_draft_addupdate(
                title=title,
                banner_url="",
                article_content=cv_content,
                words=words,
            )
        if aid and pub_cv:
            await self.dynamic_feed_create_opus(draft_id_str=aid, title=title, article_content=cv_content)


class ExtractTopicLottery:
    """
    话题抽奖信息不设置更新内容，因为本来就比较少，直接显示截止日期就行了
    """

    def __init__(self):
        self.__dir = os.path.dirname(os.path.abspath(__file__))
        self.log_path = os.path.join(self.__dir, 'log')
        self.result_path = os.path.join(self.__dir, 'result')
        if not os.path.exists(self.log_path):
            os.mkdir(self.log_path)
        if not os.path.exists(self.result_path):
            os.mkdir(self.result_path)
        self.sql = topic_sqlhelper
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "max-age=0",
            "priority": "u=0, i",
            "sec-ch-ua": "\"Chromium\";v=\"128\", \"Not;A=Brand\";v=\"24\", \"Microsoft Edge\";v=\"128\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
        }

    def _timeshift(self, timestamp):
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    async def get_resp(self, url: str):
        proxy = CONFIG.my_ipv6_addr
        while 1:
            try:
                headers = copy.deepcopy(self.headers)
                headers.update({
                    'referer': url,
                    "user-agent": CONFIG.rand_ua
                })
                resp = await my_async_httpx.get(url=url, headers=headers, proxies={
                    'http': proxy,
                    'https': proxy
                })
                assert resp.status_code == 200 or resp.status_code == 404, resp.text
                return resp
            except Exception as e:
                topic_lot_logger.exception(f"获取{url}请求失败！{e}")
                await asyncio.sleep(10)
                proxy = None

    async def handle_topic_lottery_url(self, url: str, traffic_card_id: int) -> int:
        """

        :param url:
        :param traffic_card_id:
        :return:

        0：未查询活动
        1：已成功查询
        2：查询了，但获取到的活动为空，也就是未知的活动
        3：查询出错了，去日志里查原因

        """
        resp = await self.get_resp(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 查找包含 window.__initialState 的脚本标签
        script_tags = soup.find_all('script')
        # region era活动（url里面带有era
        if 'era/' in url:
            era_tasks = []
            era_lottery_configs = []
            era_video_configs = []
            era_jika = []
            data = {}
            for tag in script_tags:
                if '__initialState' in tag.text:
                    # 尝试从字符串中提取 JSON 数据
                    js_env = MiniRacer()
                    js_env.eval('let window = {};' + tag.string)
                    # 将字符串转换为字典
                    data = js_env.execute('window.__initialState')
                    for x in data.get('EraTasklist', data.get('EraTasklistPc', [])):
                        for y in x.get('tasklist', []):
                            era_tasks.append(EraTask.model_validate(y))
                    era_lottery_configs = [EraLotteryConfig.model_validate(x['config']) for x in
                                           data.get('EraLottery', data.get('EraLotteryPc', [])) if x.get('config')]
                    era_video_configs = [EraVideoSourceCONFIG.model_validate(x['config']) for x in
                                         data.get('EraVideoSource', data.get("EraVideoSourcePc", [])) if
                                         x.get('config')]
                    era_jika = [EvaContainerTruck(
                        activityUrl=x.get('cardGeneralBigDispositionProps').get('cardQrcodePanel').get('activityUrl'),
                        jikaId=x.get('config').get('selected'),
                        topId=x.get('cardShareMessage').get('topId'),
                        topName=x.get('cardShareMessage').get('topName')
                    ) for x in data.get('EvaContainerTrucksH5', [])
                    ]
                    break
            await asyncio_gather(*[self.sql.add_era_task(
                traffic_card_id,
                awardName=x.awardName,
                taskDes=x.taskDes,
                taskId=x.taskId,
                taskName=x.taskName,
                taskType=x.taskType,
                topicID=x.topicID,
                topicName=x.topicName
            ) for x in era_tasks
            ], log=topic_lot_logger)
            await asyncio_gather(*[
                self.sql.add_era_lottery(
                    traffic_card_id,
                    x.activity_id,
                    [y.model_dump_json() for y in x.gifts],
                    x.icon,
                    x.lottery_id,
                    x.lottery_type,
                    x.per_time,
                    x.point_name) for x in era_lottery_configs
            ], log=topic_lot_logger)
            await asyncio_gather(*[self.sql.add_era_video(
                traffic_card_id,
                [y.model_dump_json() for y in x.poolList],
                x.topic_id,
                x.topic_name,
                x.videoSource_id
            ) for x in era_video_configs
            ], log=topic_lot_logger)
            await asyncio_gather(*[self.sql.add_era_jika(
                traffic_card_id,
                x.activityUrl,
                x.jikaId,
                x.topId,
                x.topName
            ) for x in era_jika
            ], log=topic_lot_logger)
            topic_lot_logger.info(f'{url}\t抽奖任务：{era_tasks}')
            topic_lot_logger.info(f'{url}\t抽奖内容：{era_lottery_configs}')
            topic_lot_logger.info(f'{url}\t视频活动：{era_video_configs}')
            topic_lot_logger.info(f'{url}\t集卡活动：{era_jika}')
            if len(era_tasks) + len(era_lottery_configs) + len(era_video_configs) + len(era_jika) == 0:
                topic_lot_logger.exception(f'{url}\t获取活动信息为空！\n{data}')
                return 2
            return 1
        # endregion
        # region h5转盘抽奖
        elif '/activity-' in url:
            h5_lottery = []
            match_task: List[MatchLotteryTask] = []
            match_lottery = []
            data = {}
            for tag in script_tags:
                if '__initialState' in tag.text:
                    # 尝试从字符串中提取 JSON 数据
                    js_env = MiniRacer()
                    js_env.eval('let window = {};' + tag.string)
                    # 将字符串转换为字典
                    data = js_env.execute('window.__initialState')
                    if lottery_v3 := data.get('h5-lottery-v3', data.get('pc-lottery-v3', [])):
                        h5_lottery = [H5ActivityLottery(
                            lotteryId=x.get('lotteryId'),
                            continueTimes=x.get('continueTimes'),
                            list=[H5ActivityLotteryGiftSource.model_validate(y) for y in x.get('list').get('source')],
                        ) for x in lottery_v3]
                    if match_lottery_task_data := data.get('match-lottery-task-pc'):
                        for x in match_lottery_task_data:
                            for y in x.get('tasks', []):
                                match_task.append(MatchLotteryTask.model_validate(y))
                    match_lottery = [MatchLottery(
                        activity_id=x.get('activity_id'),
                        lottery_id=x.get('lottery_id'),
                    ) for x in data.get('match-lottery-pc', [])]
                    break
            await asyncio_gather(*[self.sql.add_activity_lottery(
                traffic_card_id,
                x.lotteryId,
                x.continueTimes,
                [y.model_dump_json() for y in x.list]
            ) for x in h5_lottery
            ],log=topic_lot_logger)
            await asyncio_gather(*[self.sql.add_activity_match_task(
                traffic_card_id,
                x.task_desc,
                x.interact_type,
                x.task_group_id,
                x.task_name,
                x.url
            ) for x in match_task
            ],log=topic_lot_logger)
            await asyncio_gather(*[self.sql.add_activity_match_lottery(
                traffic_card_id,
                x.lottery_id,
                x.activity_id
            ) for x in match_lottery
            ],log=topic_lot_logger)

            topic_lot_logger.info(f'{url}\th5抽奖任务：{h5_lottery}')
            topic_lot_logger.info(f'{url}\t活动抽奖任务：{match_task}')
            topic_lot_logger.info(f'{url}\t活动抽奖：{match_lottery}')
            if len(h5_lottery) + len(match_task) + len(match_lottery) == 0:
                topic_lot_logger.error(f'{url}\t获取活动信息为空！\n{data}')
                return 2
            return 1

        # endregion
        elif 'dynamic/' in url:
            native_page_dynamic_index_api = 'https://api.bilibili.com/x/native_page/dynamic/index?page_id=344929&jsonp=jsonp'
            native_page_resp = await self.get_resp(native_page_dynamic_index_api)
            native_page_resp_dict = native_page_resp.json()
            pc_url = native_page_resp_dict.get('data').get('pc_url')
            if pc_url:
                return await self.handle_topic_lottery_url(pc_url, traffic_card_id)
            topic_lot_logger.error(f'{url}\t获取动态页面信息失败！\n{native_page_resp_dict}')
            return 3
        else:
            jump_urls = []
            data = {}
            for tag in script_tags:
                if '__initialState' in tag.text:
                    # 尝试从字符串中提取 JSON 数据
                    js_env = MiniRacer()
                    js_env.eval('let window = {};' + tag.string)
                    # 将字符串转换为字典
                    data = js_env.execute('window.__initialState')
                    jump_urls = list(
                        set([x.get('button_jump_url') for x in data.get('h5-button', data.get('button', [])) if
                             'blackboard' in x.get('button_jump_url', '')]))
            if jump_urls:
                for x in jump_urls:
                    await self.handle_topic_lottery_url(x, traffic_card_id)
                return 1
            topic_lot_logger.error(f'{url}\t未知话题类型！\n{data}')
            return 3

    async def spider_all_unread_traffic_card(self, status_list: list = None) -> (bool, int, Sequence[TTrafficCard]):
        """
        获取所有未读的traffic_card，解析活动类型
        :return: 是否有新增的
        """
        if status_list is None:
            status_list = [0, None]
        all_unread_traffic_card = [item for l in
                                   [await self.sql.get_all_available_traffic_info_by_status(status=x) for x in
                                    status_list] for item in l
                                   ]
        if all_unread_traffic_card:
            for x in all_unread_traffic_card:
                try:
                    jump_url = copy.deepcopy(x.jump_url)
                    _id = copy.deepcopy(x.id)
                    result = await self.handle_topic_lottery_url(jump_url, _id)
                except Exception as e:
                    topic_lot_logger.exception(f'{x.jump_url}\n{x.id}ErrorError！！！处理话题抽奖信息失败！\n{e}')
                    pushme('处理话题抽奖信息失败！', f'ErrorError！！！处理话题抽奖信息失败！\n{e}')
                    result = 3
                topic_lot_logger.info(f'{x.jump_url}\t当前traffic_card:{x.id}，状态：{result}')
                await self.sql.update_traffic_card_status(result, x.id)
            return True, len(all_unread_traffic_card), all_unread_traffic_card
        return False, len(all_unread_traffic_card), all_unread_traffic_card

    async def main(self, force_push=False):
        """
         函数入口 修改成如果有新增的则推送
        :return:
        """
        is_need_post, num, all_unread_traffic_card = await self.spider_all_unread_traffic_card()
        ua3 = gl.get_value('ua3')
        csrf3 = gl.get_value('csrf3')  # 填入自己的csrf
        cookie3 = gl.get_value('cookie3')
        buvid3 = gl.get_value('buvid3_3')
        gc = GenerateTopicLotCv(cookie3, ua3, csrf3, buvid3)
        # gc.post_flag = False  # 不直接发布
        await gc.main(pub_cv=is_need_post)
        topic_lot_logger.error('话题抽奖已更新')
        pushme('话题抽奖已更新', f'话题抽奖：更新{num}条数据\n{[x.__dict__ for x in all_unread_traffic_card]}')


async def _test():
    _a = ExtractTopicLottery()
    print(await _a.spider_all_unread_traffic_card([0, 3, None]))


async def _test_generate_cv():
    gc = GenerateTopicLotCv(
        # cookie="buvid3=434282F4-E364-7403-51C6-038E401B27F052974infoc; b_nut=1716813352; _uuid=5AC6FF4A-855E-55ED-51042-7E37D8753E2B57600infoc; enable_web_push=DISABLE; buvid4=68D497D9-DFB7-2DD5-EFBD-2640CA8327F167277-024052712-bkFP%2BfBKxK1jqmu4RNRApvMLVSVZSoxPLJw6dSJ1uURlMto45X0VJk1NHJXI5NTX; DedeUserID=4237378; DedeUserID__ckMd5=94093e21fe6687f9; hit-dyn-v2=1; rpdid=0zbfAHGGaN|BL7JC6EG|1za|3w1SbA29; buvid_fp_plain=undefined; header_theme_version=CLOSE; LIVE_BUVID=AUTO5417169088699210; CURRENT_BLACKGAP=0; PVID=1; home_feed_column=5; fingerprint=3c0395c5734f117c8547ff054c538ef7; CURRENT_FNVAL=4048; CURRENT_QUALITY=116; browser_resolution=1463-754; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MjUyNDU3OTcsImlhdCI6MTcyNDk4NjUzNywicGx0IjotMX0.v7ZUi1Cj18rBWbYy6hsDFjI09ny1nd8SZWZ1iDuKc-w; bili_ticket_expires=1725245737; b_lsid=F5B37A103_191A38FEF3E; SESSDATA=213503be%2C1740578775%2C2cfb8%2A82CjBBtuR1OtNFGOyuCaOPH5WDmz4WVtQvqPXzTUdeZGLHUFxcj53LLZfP77LdfBWMo9YSVjcwTzlReGw4d2lKQVpnRzdJNFdHSm02SERyWENSUlVTbDg4azRVajlVVlNnWk9BOU9IQllxNEU3TXZlSlEyT0VySEVWa0ptWFRsalhxWFdpMEtwODR3IIEC; bili_jct=38d76480d1837d76e6c7c84d86511d06; sid=6w71b423; buvid_fp=3c0395c5734f117c8547ff054c538ef7; bp_t_offset_4237378=971489059387998208",
        cookie="",
        ua=CONFIG.rand_ua,
        csrf='38d76480d1837d76e6c7c84d86511d06',
        buvid="434282F4-E364-7403-51C6-038E401B27F052974infoc"
    )
    await gc.main()


if __name__ == "__main__":
    asyncio.run(_test())
