import asyncio
import datetime
import random
import time
from typing import Dict

from fastapi接口.service.opus新版官方抽奖.Base.generate_cv import GenerateCvBase
from fastapi接口.service.opus新版官方抽奖.Model.GenerateCvModel import CvContentOps, CvContentAttr, CvContent, CutOff, \
    Color
from fastapi接口.service.opus新版官方抽奖.预约抽奖.db.models import TUpReserveRelationInfo, TReserveRoundInfo
from fastapi接口.service.opus新版官方抽奖.预约抽奖.db.sqlHelper import bili_reserve_sqlhelper
from fastapi接口.service.opus新版官方抽奖.预约抽奖.etc.scrapyReserveJsonData import ReserveScrapyRobot


class GenerateReserveLotCv(GenerateCvBase):
    def __init__(self, cookie, ua, csrf, buvid, abstract: str = ''):
        super().__init__(cookie, ua, csrf, buvid)
        self.target_timeformat = '%m-%d %H:%M'  # 专栏的最终时间格式
        self.post_flag = True  # 是否直接发布
        self.sqlhelper = bili_reserve_sqlhelper
        self.abstract = abstract

    def zhuanlan_format(self,
                        zhuanlan_dict: Dict[str, list[TUpReserveRelationInfo]],
                        last_round: TReserveRoundInfo,
                        *,
                        blank_space: int = 0,
                        inline_sep_str: str = '\t'
                        ) -> (CvContent, int):
        """

        :param zhuanlan_dict:
        :param blank_space: 开头空几行
        :return:
        """

        def handle_lot_detail_ops(show_str: str, attr_type: CvContentAttr) -> CvContentOps:
            nonlocal words
            ops = CvContentOps(
                insert=show_str,
                attributes=attr_type
            )
            words += len(show_str)
            return ops

        ret: CvContent = CvContent(ops=[])
        words = 0
        change_line_ops = CvContentOps(
            insert="\n"
        )
        for _ in range(blank_space):
            cut_off_ops = CvContentOps(  # 分隔符不占用文字长度，不需要计算
                attributes=CvContentAttr(**{"class": "cut-off"}),
                insert=CutOff.cut_off_5.value
            )
            ret.ops.append(cut_off_ops)
        for lottery_end_date, reserve_info_list in zhuanlan_dict.items():
            selected_color_class_key = random.choice(list(Color))
            rand_color_ops = CvContentAttr(color=selected_color_class_key)
            ret.ops.append(handle_lot_detail_ops(
                show_str=lottery_end_date,
                attr_type=CvContentAttr(color=selected_color_class_key)
            ))
            ret.ops.append(change_line_ops)  # 日期换行
            for i in reserve_info_list:
                selected_color_class_key = random.choice(list(Color))
                ops_list = []
                if i.reserve_round_id >= last_round.round_id - 1:
                    _str = '【新】' + inline_sep_str
                else:
                    _str = '【\u3000】' + inline_sep_str
                ops_list.append(
                    handle_lot_detail_ops(
                        show_str=_str,
                        attr_type=rand_color_ops
                    )
                )
                if i.dynamicId:
                    _str = '动态链接' + inline_sep_str
                    ops_list.append(
                        handle_lot_detail_ops(
                            show_str=_str,
                            attr_type=CvContentAttr(
                                link=f"https://t.bilibili.com/{i.dynamicId}?tab=2",
                            )
                        )
                    )
                else:
                    _str = '链接迷路了喵' + inline_sep_str
                    ops_list.append(
                        handle_lot_detail_ops(
                            show_str=_str,
                            attr_type=CvContentAttr(color=selected_color_class_key)
                        )
                    )
                _str = '发布者空间' + inline_sep_str
                ops_list.append(
                    handle_lot_detail_ops(
                        show_str=_str,
                        attr_type=CvContentAttr(
                            link=f"https://space.bilibili.com/{i.upmid}/dynamic",
                        )
                    )
                )
                _str = f'{i.text[5:]}{inline_sep_str}{datetime.datetime.fromtimestamp(i.etime).strftime(self.target_timeformat)}'
                ops_list.append(
                    handle_lot_detail_ops(
                        show_str=_str,
                        attr_type=CvContentAttr(
                            color=selected_color_class_key
                        )
                    )
                )

                ret.ops.extend(ops_list)
                ret.ops.append(change_line_ops)  # 单条数据换行
            ret.ops.append(change_line_ops)  # 下一个日期换行
        return ret, words

    def zhuanlan_date_sort(self, zhuanlan_data_order_by_date: list[TUpReserveRelationInfo],

                           limit_date_switch: bool = False,
                           limit_date: int = 10) -> Dict[str, list[TUpReserveRelationInfo]]:
        '''
        为字典添加了etime_str的日期文字格式
        :param zhuanlan_data_order_by_date:
        :param limit_date_switch:
        :param limit_date:
        :return:
        '''
        oneDayList = {}  # 放入同一天的抽奖内容{'日期':[抽奖文字1,抽奖文字2...]}
        today = datetime.datetime.today()
        next_day = today + datetime.timedelta(days=1)

        for reserve_info in zhuanlan_data_order_by_date:
            lottery_end_date = datetime.datetime.strptime(
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(reserve_info.etime))), '%Y-%m-%d %H:%M:%S')
            only_date = lottery_end_date.date()
            if limit_date_switch:
                if (only_date - next_day.date()).days > limit_date:  # 大于指定天数的抽奖不放进去
                    continue
            if int(reserve_info.etime) < time.time():
                # 如果过期了进入下一条
                continue
            if oneDayList.get(str(lottery_end_date.date())):  # 如果存在当前抽奖日期，则直接append上去
                oneDayList.get(str(lottery_end_date.date())).append(reserve_info)
            else:
                oneDayList.update({str(lottery_end_date.date()): [reserve_info]})  # 如果不存在就新建一个key把它存进去
        ret_List = {}
        for k, v in oneDayList.items():
            ret_List.update({k: sorted(v, key=lambda x: x.etime)})  # 每一个日期里面的数据按照开奖时间升序排列
        return ret_List

    def zhuanlan_data_sort_by_date(self, zhuanlan_data: list) -> list:
        '''
        将所有专栏抽奖数据按开奖日期日期排序
        :return:
        '''
        return sorted(zhuanlan_data, key=lambda x: x['etime'])

    async def main(self, is_api_update: bool = False,
                   pub_cv: bool = False,
                   save_to_local_file: bool = True
                   ) -> CvContent:
        '''
        state含义：
            -100 ：失效
            150 ：已经开奖
            -110 ：也是开奖了的
            100 ：未开
            -300 ：已经失效
        :return:
        '''
        last_round: TReserveRoundInfo = await self.sqlhelper.get_latest_reserve_round(readonly=True)
        zhuanlan_data: list[
            TUpReserveRelationInfo] = await self.sqlhelper.get_all_available_reserve_lotterys()  # 获取所有有效的预约抽奖 （按照etime升序排列
        if is_api_update:
            reserve_robot = ReserveScrapyRobot()
            await reserve_robot.refresh_not_drawn_lottery()
        zhuanlan_data_date_sort = self.zhuanlan_date_sort(zhuanlan_data)
        cv_content, words = self.zhuanlan_format(zhuanlan_data_date_sort, last_round)
        today = datetime.datetime.today()
        _ = datetime.timedelta(days=1)
        next_day = today + _
        title = f'【{next_day.date().month}.{next_day.date().day}】之后的预约抽奖'
        return await self.pub_cv(
            title=title,
            abstract=self.abstract,
            cv_content=cv_content,
            words=words,
            pub_cv=pub_cv,
            save_to_local_file=save_to_local_file
        )


if __name__ == '__main__':
    async def submit_reserve__lot_main(is_post=True):
        """
        提交专栏
        :param is_post:是否直接发布
        :return:
        """
        ua3 = ""
        csrf3 = ""  # 填入自己的csrf
        cookie3 = ""
        buvid3 = ""
        gc = GenerateReserveLotCv(cookie3, ua3, csrf3, buvid3)
        gc.post_flag = is_post
        result = await gc.main()
        print(result)

    asyncio.run(submit_reserve__lot_main(False))
