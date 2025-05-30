# -*- coding: utf-8 -*-
import asyncio
import traceback
import pandas as pd
import json
import os.path
import time
import bs4
from fastapi接口.log.base_log import zhihu_api_logger
import fastapi接口.service.zhihu.zhihu_src.zhihu_utl as zhihu_utl
from Bilibili_methods.all_methods import methods

current_dir = os.path.abspath(__file__)


def get_file_p(file_relative_p: str):
    return os.path.join(current_dir, '../', file_relative_p)


get_pin_ts_txt_p = get_file_p('get_pin_ts.txt')
uname_list_json_p = get_file_p('uname_list.json')


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

    def __init__(self, content: str, created: int, like_count: int, id__: int, repin_count: int, comment_count: int,
                 author: str, user_type: str, follower_count: int, gender: int):
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


class LotScrapy:
    def __init__(self, ):
        self.get_pin_ts = 0
        self.is_getting_dyn_flag = False
        self.log = zhihu_api_logger
        self.log.bind(user='lotScrapy')
        self.lot_set_time = 7 * 3600 * 24  # 规定的天数，默认一个礼拜
        self.oldest_lot_time = 15 * 3600 * 24
        self.uname_list: list[str] = [  # 抽奖用户的名称
            'tao-guang-yang-hui-1-50',
            '7-67-73-83',
            '7-62-98-25',
            'guo-hao-38-25',
            'haleke',
            'yu-ying-run-22',
            '73-25-12-59',
            'xiao-yu-ying-32',
            'momo-55-43-94',
            'shang-tiao-dang-ma-95',
            'xiaomomo-75',
            'shui-se-11-28-29',
            'hai-mian-bao-bao-feng-fei-fei-95',
            'hui-mou-63-13',
            'bai-ge-38-73',
            'momo-84-70-39',
            'tan-suo-zhe-75-81-94',
            'nice-93-1-9',
            'hua-hua-ran-37',

        ]
        self.z = zhihu_utl.zhihu_method()  # 实例化一下
        self.use_proxy_flag = False  # 使用代理获取请求
        self.recorded_users_pins = dict()  # {"xxx":[1,2,3,4,5,6,7,8,9,10]} 最后一次获取的动态
        self.lot_pin_details: list[PinDetail] = []  # 抽奖的pin详情
        self.non_lot_pin_details: list[PinDetail] = []
        self.all_pins: list[int] = []
        self.file_init()
        self.BM = methods()
        self.var_init()

    def var_init(self):
        if os.path.exists(get_pin_ts_txt_p):
            with open(get_pin_ts_txt_p, 'r', encoding='utf-8') as f:
                file_content = f.read()
                self.get_pin_ts: int = int(file_content) if file_content else 0
                if not isinstance(self.get_pin_ts, int):
                    self.get_pin_ts: int = 0
        else:
            self.get_pin_ts: int = 0
        try:
            if os.path.exists(uname_list_json_p):
                with open(uname_list_json_p, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    self.uname_list: list[int] = json.loads(file_content).get('uname_list', self.uname_list)
            else:
                with open(uname_list_json_p, 'w', encoding='utf-8') as f:
                    json.dump({'uname_list': self.uname_list}, f, ensure_ascii=False, indent=4)
                pass
        except Exception:
            traceback.print_exc()
        self.recorded_users_pins = dict()  # {"xxx":[1,2,3,4,5,6,7,8,9,10]} 最后一次获取的动态
        self.lot_pin_details: list[PinDetail] = []
        self.non_lot_pin_details: list[PinDetail] = []
        self.all_pins: list[int] = []
        self.file_init()

    def file_init(self):
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
            with open(get_file_p('records/获取过pins的知乎用户.json')) as f:
                self.recorded_users_pins = json.load(f)
        if os.path.exists(get_file_p('records/获取过的pins.txt')):
            with open(get_file_p('records/获取过的pins.txt'), 'r', encoding='utf-8') as f:
                for _ in f.readlines():
                    for p in _.split(','):
                        if p.strip():
                            self.all_pins.append(int(p.strip()))

    def resolve_moment_pins(self, moment_pins_resp_json) -> list[PinDetail]:
        ret_list = []
        for da in moment_pins_resp_json.get('data'):
            if da.get('origin_pin'):
                origin_pin = da.get('origin_pin')
                html = bs4.BeautifulSoup(origin_pin.get('content')[0].get('content'), 'html.parser')
                content = origin_pin.get('content')[0].get('title') + html.text
                comment_count = origin_pin.get('comment_count')
                repin_count = origin_pin.get('repin_count')
                like_count = origin_pin.get('like_count')
                created = origin_pin.get('created')
                __id = origin_pin.get('id')
                author = origin_pin.get('author').get('name')
                user_type = origin_pin.get('author').get('user_type')
                follower_count = origin_pin.get('author').get('follower_count')
                gender = origin_pin.get('author').get('gender')

                origin_pinDetail = PinDetail(id__=int(__id), content=content, comment_count=comment_count,
                                             repin_count=repin_count,
                                             like_count=like_count, created=created, author=author, user_type=user_type,
                                             follower_count=follower_count, gender=gender)
                ret_list.append(origin_pinDetail)
        return ret_list

    async def get_all_pins(self, uname):
        offset = 0
        __limit = 20
        last_created_time = 0
        encountered_flag = False
        newest_pins: list[int] = self.recorded_users_pins.get(uname) if self.recorded_users_pins.get(uname) else []
        first_round = True
        while 1:
            moment_pins_resp_json = await self.z.get_moments_pin_by_user_id(uname, offset, __limit,
                                                                            proxy_flag=self.use_proxy_flag)
            if moment_pins_resp_json.get('data'):
                offset += __limit
                origin_pin_details = self.resolve_moment_pins(moment_pins_resp_json)

                if len(origin_pin_details) > 0:
                    for __pd in origin_pin_details:
                        if first_round:
                            if __pd.id not in newest_pins:
                                newest_pins.append(__pd.id)
                        if __pd.created < last_created_time or last_created_time == 0:
                            last_created_time = __pd.created
                        if int(time.time()) - last_created_time >= self.lot_set_time:  # 如果超出了规定的天数就退出
                            self.log.debug(
                                f'超出了规定的天数就退出，结束当前用户：{uname}\nhttps://www.zhihu.com/people/{uname}/pins')
                            break
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
                if moment_pins_resp_json.get(
                        'code') == 10003:  # {'error': {'message': '请求参数异常，请升级客户端后重试。', 'code': 10003}}
                    raise ValueError(f'用户{uname}的请求参数异常\t{moment_pins_resp_json}')
                if moment_pins_resp_json.get('code') is not None:
                    raise ValueError(f'用户{uname}的请求参数异常\t{moment_pins_resp_json}')
                raise ValueError(f'未知错误:{moment_pins_resp_json}')
        self.recorded_users_pins.update({uname: newest_pins[-20:]})  # 更新最新获取的空间信息

    def end_write(self):
        import pandas
        if len(self.all_pins) >= 10000:
            self.all_pins = self.all_pins[2000:-1]
        with open(get_file_p('records/获取过的pins.txt'), 'w', encoding='utf-8') as f:
            f.writelines(','.join(list(map(str, self.all_pins))) + ',')

        with open(get_file_p('records/获取过pins的知乎用户.json'), "w", encoding='utf-8') as f:
            json.dump(self.recorded_users_pins, f, indent=4)

        with open(get_file_p('uname_list.json'), 'w', encoding='utf-8') as f:
            f.writelines(json.dumps({'uname_list': self.uname_list}))

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
        # self.log.info(f'获取过的所有{len(self.all_pins)}条pin:{self.all_pins}')
        await asyncio.gather(*[asyncio.create_task(self.get_all_pins(u)) for u in self.uname_list])
        self.end_write()

    async def save_now_get_pin_ts(self, ts: int):

        with open(get_file_p('get_pin_ts.txt'), 'w', encoding='utf-8') as f:
            self.get_pin_ts = ts
            f.writelines(f'{ts}')

    async def api_get_all_pins(self)->list[str]:
        self.log.critical(f'api加密有变化，正在修复中，暂时不使用')
        return []
        while self.is_getting_dyn_flag:
            self.log.debug('正在获取用户空间，请稍等...')
            await asyncio.sleep(30)
        if os.path.exists(get_file_p('get_pin_ts.txt')):
            with open(get_file_p('get_pin_ts.txt'), 'r', encoding='utf-8') as f:
                file_content = f.read()
                self.get_pin_ts: int = int(file_content) if file_content else 0
                if not isinstance(self.get_pin_ts, int):
                    self.get_pin_ts: int = 0
        else:
            self.get_pin_ts: int = 0

        if int(time.time()) - self.get_pin_ts >= 0.8 * 24 * 3600:
            start_ts = int(time.time())
            self.is_getting_dyn_flag = True
            self.var_init()
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
                ret_pins_id_list.append(row['id'])
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


zhihu_lotScrapy = LotScrapy()

if __name__ == "__main__":
    asyncio.run(zhihu_lotScrapy.api_get_all_pins())
