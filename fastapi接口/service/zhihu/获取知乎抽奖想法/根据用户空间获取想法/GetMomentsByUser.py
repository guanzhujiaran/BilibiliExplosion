# -*- coding: utf-8 -*-
import asyncio
import json
import os.path
import re
import time
import traceback
from enum import StrEnum

import aiofiles
import bs4
import pandas
import pandas as pd

from Bilibili_methods.all_methods import methods
from CONFIG import CONFIG
from fastapi接口.log.base_log import zhihu_api_logger
from fastapi接口.service.PlayWright.Operator import PlaywrightOperator

current_dir = os.path.abspath(os.path.dirname(__file__))


def get_file_p(file_relative_p: str):
    return os.path.join(current_dir, file_relative_p)


get_pin_ts_txt_p = get_file_p('get_pin_ts.txt')
uname_list_json_p = get_file_p('uname_list.json')


class PinDetailType(StrEnum):
    moment = 'moment'
    zhuanlan = 'zhuanlan'


class PinDetail:
    content: str  # 内容
    created: int  # 创作时间
    like_count: int  # 点赞数
    id: int  # 源pinId
    repin_count: int  # 转发数
    comment_count: int  # 评论数
    author: str  # 创作者用户名
    user_type: str  # 创作者类型
    follower_count: int  # 关注者数量
    gender: int  # 性别
    from_user: str  # 来自哪个用户
    type: PinDetailType

    def __init__(self, content: str, created: int, like_count: int, id__: int, repin_count: int, comment_count: int,
                 author: str, user_type: str, follower_count: int, gender: int, from_user: str, type: PinDetailType):
        '''

        :param content: 内容
        :param created: 创作时间
        :param like_count: 点赞数
        :param id__: 源pinId
        :param repin_count: 转发数
        :param comment_count: 评论数
        '''
        self.content = content
        self.like_count = like_count
        self.id = id__
        self.repin_count = repin_count
        self.comment_count = comment_count
        self.created = created
        self.author = author
        self.user_type = user_type
        self.follower_count = follower_count
        self.gender = gender
        self.from_user = from_user
        self.type = type


class LotScrapy:
    def __init__(self, *, headless: bool = False):
        self._headless = headless
        self.get_pin_ts = 0
        self.is_getting_dyn_flag = False
        self.log = zhihu_api_logger
        self.log.bind(user='lotScrapy')
        self.lot_set_time = 7 * 3600 * 24  # 规定的天数，默认一个礼拜
        self.oldest_lot_time = 15 * 3600 * 24
        self.uname_list: list[str] = [  # 抽奖用户的名称
            # 'tao-guang-yang-hui-1-50',
            '7-67-73-83',
            # '7-62-98-25',
            # 'guo-hao-38-25',
            # 'haleke',
            # 'yu-ying-run-22',
            # '73-25-12-59',
            # 'xiao-yu-ying-32',
            # 'momo-55-43-94',
            # 'shang-tiao-dang-ma-95',
            # 'xiaomomo-75',
            'shui-se-11-28-29',
            'hai-mian-bao-bao-feng-fei-fei-95',
            'hui-mou-63-13',
            # 'bai-ge-38-73',
            'momo-84-70-39',
            'tan-suo-zhe-75-81-94',
            'nice-93-1-9',
            # 'hua-hua-ran-37',

        ]
        self.use_proxy_flag = False  # 使用代理获取请求
        self.recorded_users_pins = dict()  # {"xxx":[1,2,3,4,5,6,7,8,9,10]} 最后一次获取的动态
        self.lot_pin_details: list[PinDetail] = []  # 抽奖的pin详情
        self.non_lot_pin_details: list[PinDetail] = []
        self.all_pins: list[int] = []
        self.BM = methods()
        self.playwright = PlaywrightOperator(
            CONFIG.playwright_user_dir.zhihu.value,
            headless=self._headless,
        )

    async def init(self):
        await self.playwright.launch()
        await self._var_init()
        await self._file_init()

    async def _var_init(self):
        if os.path.exists(get_pin_ts_txt_p):
            async with aiofiles.open(get_pin_ts_txt_p, 'r', encoding='utf-8') as f:
                file_content = await f.read()
                self.get_pin_ts: int = int(file_content) if file_content else 0
                if not isinstance(self.get_pin_ts, int):
                    self.get_pin_ts: int = 0
        else:
            self.get_pin_ts: int = 0
        try:
            if os.path.exists(uname_list_json_p):
                async with aiofiles.open(uname_list_json_p, 'r', encoding='utf-8') as f:
                    file_content = await f.read()
                    self.uname_list: list[int] = json.loads(file_content).get('uname_list', self.uname_list)
            else:
                async with aiofiles.open(uname_list_json_p, 'w', encoding='utf-8') as f:
                    await f.writelines(json.dumps({'uname_list': self.uname_list}, ensure_ascii=False, indent=4))

                pass
        except Exception:
            traceback.print_exc()
        self.recorded_users_pins = dict()  # {"xxx":[1,2,3,4,5,6,7,8,9,10]} 最后一次获取的动态
        self.lot_pin_details: list[PinDetail] = []
        self.non_lot_pin_details: list[PinDetail] = []
        self.all_pins: list[int] = []

    async def _file_init(self):
        '''
        文件和属性初始化
        :return:
        '''
        if not os.path.exists(get_file_p('zhuhu_result')):
            os.makedirs(get_file_p('zhuhu_result'))
        if not os.path.exists(get_file_p('records')):
            os.makedirs(get_file_p('records'))
        if not os.path.exists(get_file_p('zhuhu_result/log')):
            os.makedirs(get_file_p('zhuhu_result/log'))
        if os.path.exists(get_file_p('records/获取过pins的知乎用户.json')):
            async with aiofiles.open(get_file_p('records/获取过pins的知乎用户.json')) as f:
                self.recorded_users_pins = json.loads(await f.read())
        if os.path.exists(get_file_p('records/获取过的pins.txt')):
            async with aiofiles.open(get_file_p('records/获取过的pins.txt'), 'r', encoding='utf-8') as f:
                for _ in await f.readlines():
                    for p in _.split(','):
                        if p.strip():
                            self.all_pins.append(int(p.strip()))

    def resolve_moment_pins(self, moment_pins_resp_json, from_user: str) -> list[PinDetail]:
        ret_list = []
        for da in moment_pins_resp_json.get('data'):
            if da.get('origin_pin'):
                origin_pin = da.get('origin_pin')
                raw_contents = origin_pin.get('content')
                html = bs4.BeautifulSoup(raw_contents[0].get('content'), 'html.parser')
                content = raw_contents[0].get('title') + html.text
                comment_count = origin_pin.get('comment_count')
                repin_count = origin_pin.get('repin_count')
                like_count = origin_pin.get('like_count')
                created = origin_pin.get('created')
                __id = origin_pin.get('id')
                author = origin_pin.get('author').get('name')
                user_type = origin_pin.get('author').get('user_type')
                follower_count = origin_pin.get('author').get('follower_count')
                gender = origin_pin.get('author').get('gender')

                origin_pinDetail = PinDetail(id__=int(__id),
                                             content=content,
                                             comment_count=comment_count,
                                             repin_count=repin_count,
                                             like_count=like_count,
                                             created=created,
                                             author=author,
                                             user_type=user_type,
                                             follower_count=follower_count,
                                             gender=gender,
                                             from_user=from_user,
                                             type=PinDetailType.moment)
                ret_list.append(origin_pinDetail)
                try:
                    pin_id_in_origin_pin_ids = re.findall(r'https://www.zhihu.com/pin/(\d+)',
                                                          raw_contents[0].get("content"))
                    for pin_id in list(set(pin_id_in_origin_pin_ids)):
                        origin_pin_content_pinDetail = PinDetail(
                            id__=int(pin_id), content=content, comment_count=comment_count,
                            repin_count=repin_count,
                            like_count=like_count, created=created, author=author, user_type=user_type,
                            follower_count=follower_count, gender=gender, from_user=from_user,
                            type=PinDetailType.moment
                        )
                        ret_list.append(origin_pin_content_pinDetail)

                    zhuanlan_pid_in_origin_pin_ids = re.findall(r'https://zhuanlan.zhihu.com/p/(\d+)',
                                                                raw_contents[0].get("content"))
                    for pin_id in list(set(zhuanlan_pid_in_origin_pin_ids)):
                        origin_pin_content_pinDetail = PinDetail(
                            id__=int(pin_id), content=content, comment_count=comment_count,
                            repin_count=repin_count,
                            like_count=like_count, created=created, author=author, user_type=user_type,
                            follower_count=follower_count, gender=gender, from_user=from_user,
                            type=PinDetailType.zhuanlan
                        )
                        ret_list.append(origin_pin_content_pinDetail)
                except Exception as e:
                    self.log.exception(e)
        return ret_list

    async def get_all_pins(self, uname):
        offset = 0
        __limit = 20
        last_created_time = 0
        encountered_flag = False
        newest_pins: list[int] = self.recorded_users_pins.get(uname) if self.recorded_users_pins.get(uname) else []
        first_round = True
        async with await self.playwright.expect_response(
                f'https://www.zhihu.com/api/v4/v2/pins/*/moments?*') as response_info:
            await self.playwright.goto(
                f'https://www.zhihu.com/people/{uname}/pins'
            )
        resp = await response_info.value
        moment_pins_resp_json = await resp.json()
        while 1:
            if moment_pins_resp_json.get('data'):
                offset += __limit
                origin_pin_details = self.resolve_moment_pins(moment_pins_resp_json, from_user=uname)

                if len(origin_pin_details) > 0:
                    for __pd in origin_pin_details:
                        if first_round:
                            if __pd.id not in newest_pins:
                                newest_pins.append(__pd.id)
                        if __pd.created < last_created_time or last_created_time == 0:
                            last_created_time = __pd.created
                        if self.recorded_users_pins.get(uname):
                            if __pd.id in self.recorded_users_pins.get(uname):
                                encountered_flag = True
                        if __pd.id not in self.all_pins:
                            self.all_pins.append(__pd.id)
                            if not self.BM.choujiangxinxipanduan(__pd.content):
                                self.lot_pin_details.append(__pd)
                            else:
                                self.non_lot_pin_details.append(__pd)
                first_round = False
                # 判断退出条件
                if encountered_flag:
                    self.log.debug(f'遇到获取过的pin，结束当前用户：{uname}\nhttps://www.zhihu.com/people/{uname}/pins')
                    break
                if int(time.time()) - last_created_time >= self.lot_set_time:  # 如果超出了规定的天数就退出
                    self.log.debug(
                        f'超出了规定的天数就退出，结束当前用户：{uname}\nhttps://www.zhihu.com/people/{uname}/pins')
                    break
                if moment_pins_resp_json.get('paging').get('is_end'):
                    self.log.debug(f'用户没有更多pin，结束当前用户：{uname}\nhttps://www.zhihu.com/people/{uname}/pins')
                    break
            else:
                self.log.error(moment_pins_resp_json)
                await asyncio.sleep(10)
                if moment_pins_resp_json.get(
                        'code') == 10003:  # {'error': {'message': '请求参数异常，请升级客户端后重试。', 'code': 10003}}
                    raise ValueError(f'用户{uname}的请求参数异常\t{moment_pins_resp_json}')
                if moment_pins_resp_json.get('code') is not None:
                    raise ValueError(f'用户{uname}的请求参数异常\t{moment_pins_resp_json}')
                raise ValueError(f'未知错误:{moment_pins_resp_json}')

            async with await self.playwright.expect_response(
                    f'https://www.zhihu.com/api/v4/v2/pins/*/moments?*') as response_info:
                await self.playwright.scroll_to_bottom()
            resp = await response_info.value
            moment_pins_resp_json = await resp.json()
        self.recorded_users_pins.update({uname: newest_pins[-20:]})  # 更新最新获取的空间信息

    async def end_write(self):
        if len(self.all_pins) >= 10000:
            self.all_pins = self.all_pins[2000:-1]
        async with aiofiles.open(get_file_p('records/获取过的pins.txt'), 'w', encoding='utf-8') as f:
            await f.writelines(','.join(list(map(str, self.all_pins))) + ',')

        async with aiofiles.open(get_file_p('records/获取过pins的知乎用户.json'), "w", encoding='utf-8') as f:
            await f.write(json.dumps(self.recorded_users_pins, indent=4))
        async with aiofiles.open(get_file_p('uname_list.json'), 'w', encoding='utf-8') as f:
            await f.writelines(json.dumps({'uname_list': self.uname_list}))

        def vars_(el):
            ret = vars(el)
            ret.update({'content': repr(ret['content'])})
            return ret

        self.lot_pin_details.sort(key=lambda x: x.id, reverse=True)

        DF = pandas.DataFrame(map(vars_, self.lot_pin_details))
        DF.to_csv(get_file_p('zhuhu_result/更新的抽奖内容.csv'), index=False, sep='\t', header=True)
        DF.to_csv(get_file_p('zhuhu_result/log/所有的抽奖内容.csv')
                  , mode='a+', index=False, sep='\t',
                  header=False)

        DF2 = pandas.DataFrame(map(vars_, self.non_lot_pin_details))
        DF2.to_csv(get_file_p('zhuhu_result/非抽奖内容.csv'), mode='a+', index=False, sep='\t',
                   header=False)

    async def main(self):
        await self.init()
        # self.log.info(f'获取过的所有{len(self.all_pins)}条pin:{self.all_pins}')
        for u in self.uname_list:
            await self.get_all_pins(u)
        await self.playwright.close()
        await self.end_write()

    async def save_now_get_pin_ts(self, ts: int):
        async with aiofiles.open(get_file_p('get_pin_ts.txt'), 'w', encoding='utf-8') as f:
            self.get_pin_ts = ts
            await f.writelines(f'{ts}')

    async def api_get_all_pins(self) -> list[str]:
        while self.is_getting_dyn_flag:
            self.log.debug('正在获取用户空间，请稍等...')
            await asyncio.sleep(30)
        if os.path.exists(get_file_p('get_pin_ts.txt')):
            async with aiofiles.open(get_file_p('get_pin_ts.txt'), 'r', encoding='utf-8') as f:
                file_content = await f.read()
                self.get_pin_ts: int = int(file_content) if file_content else 0
                if not isinstance(self.get_pin_ts, int):
                    self.get_pin_ts: int = 0
        else:
            self.get_pin_ts: int = 0

        if int(time.time()) - self.get_pin_ts >= 0.8 * 24 * 3600:
            start_ts = int(time.time())
            self.is_getting_dyn_flag = True
            await self._var_init()
            await self.main()
            await self.save_now_get_pin_ts(start_ts)
            self.is_getting_dyn_flag = False
        return self.solve_lot_csv()

    def solve_lot_csv(self):
        def filter_lot(lot_df: pd.DataFrame) -> list:
            ret_pins_id_list = []
            for index, row in lot_df.iterrows():
                if int(time.time()) - int(row['created']) > self.oldest_lot_time:
                    continue
                pin_id = row['id']
                if row.get('type') == PinDetailType.zhuanlan:
                    ret_pins_id_list.append(f'https://zhuanlan.zhihu.com/p/{pin_id}')
                elif row.get('type') == PinDetailType.moment:
                    ret_pins_id_list.append(f'https://www.zhihu.com/pin/{pin_id}')
                else:
                    self.log.error(f'未知的pin类型:{row.get("type")}，使用默认moment(想法)处理')
                    ret_pins_id_list.append(f'https://www.zhihu.com/pin/{pin_id}')
            return ret_pins_id_list

        try:
            df = pd.read_csv(get_file_p('zhuhu_result/更新的抽奖内容.csv'), encoding='utf-8', sep='\t')
            all_lot_det = filter_lot(df)
            all_lot_det.sort(reverse=True)  # 按照降序排序
            self.log.info(f'发送了{len(all_lot_det)}条pin')
            return [str(x) for x in all_lot_det]
        except pd.errors.EmptyDataError:
            return []
        except Exception:
            raise ValueError('数据为空')

    async def _login(self):
        await self.playwright.launch()
        await self.playwright.goto("https://www.browserscan.net/zh/bot-detection")

        await asyncio.get_running_loop().create_future()

    async def _test_robot_tech(self):
        await self.playwright.launch()
        # "https://kaliiiiiiiiii.github.io/brotector/"
        # "https://www.browserscan.net/zh/bot-detection"
        await self.playwright.goto("https://www.xiaohongshu.com")
        await asyncio.sleep(5)
        await self.playwright.page.screenshot(path='./1.pdf', full_page=True)


zhihu_lotScrapy = LotScrapy(headless=False)

if __name__ == "__main__":
    asyncio.run(zhihu_lotScrapy._test_robot_tech())
