# -*- coding: utf-8 -*-
"""
发布抽奖专栏
"""
import datetime
import random
import time
from typing import Literal, List

from fastapi接口.service.opus新版官方抽奖.Base.generate_cv import GenerateCvBase
from fastapi接口.service.opus新版官方抽奖.Model.GenerateCvModel import CvContent, CvContentOps, CvContentAttr, CutOff, \
    Color
from fastapi接口.service.opus新版官方抽奖.Model.OfficialLotModel import LotDetail


class GenerateOfficialLotCv(GenerateCvBase):
    def __init__(self, cookie, ua, csrf, buvid, abstract: str = ''):
        super().__init__(cookie, ua, csrf, buvid)
        self.post_flag = True  # 是否直接发布
        self.abstract = abstract

    def zhuanlan_format(self, zhuanlan_dict: dict[str, list[LotDetail]], blank_space: int = 0,
                        inline_sep_str: str = ' ') -> (CvContent, int):
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
            # 'code', 'message', 'ttl', 'sid', 'name', 'total', 'stime', 'etime',
            # 'isFollow', 'state', 'oid', 'type', 'upmid', 'reserveRecordCtime',
            # 'livePlanStartTime', 'upActVisible', 'lotteryType', 'text', 'jumpUrl',
            # 'dynamicId', 'reserveTotalShowLimit', 'desc', 'start_show_time', 'hide',
            # 'subType', 'productIdPrice', 'ids', 'reserve_products' , 'etime_str'
        for lottery_end_date, __lot_detail_list in zhuanlan_dict.items():
            selected_color_class_key = random.choice(list(Color))
            rand_color_ops = CvContentAttr(color=selected_color_class_key)
            ret.ops.append(handle_lot_detail_ops(
                show_str=lottery_end_date,
                attr_type=CvContentAttr(color=selected_color_class_key)
            ))
            ret.ops.append(change_line_ops)  # 日期换行
            for __lot_detail in __lot_detail_list:
                ops_list = []
                if not __lot_detail.article_pub_record:
                    _str = '【新】' + inline_sep_str
                else:
                    _str = '【\u3000】' + inline_sep_str
                ops_list.append(
                    handle_lot_detail_ops(
                        show_str=_str,
                        attr_type=rand_color_ops
                    )
                )
                if __lot_detail.dynamic_id:
                    _str = '动态链接' + inline_sep_str
                    ops_list.append(
                        handle_lot_detail_ops(
                            show_str=_str,
                            attr_type=CvContentAttr(
                                link=f"https://t.bilibili.com/{__lot_detail.dynamic_id}?tab=1",
                            )
                        )
                    )
                    _str = 'opus链接' + inline_sep_str
                    ops_list.append(
                        handle_lot_detail_ops(
                            show_str=_str,
                            attr_type=CvContentAttr(
                                link=f"https://www.bilibili.com/opus/{__lot_detail.dynamic_id}",
                            )
                        )
                    )
                else:
                    _str = '链接迷路了喵' + inline_sep_str
                    ops_list.append(
                        handle_lot_detail_ops(
                            show_str=_str,
                            attr_type=CvContentAttr(
                                color=selected_color_class_key
                            )
                        )
                    )
                _str = f"{__lot_detail.first_prize_cmt} * {__lot_detail.first_prize}{inline_sep_str}"
                ops_list.append(
                    handle_lot_detail_ops(
                        show_str=_str,
                        attr_type=rand_color_ops
                    )
                )
                if __lot_detail.second_prize_cmt:
                    _str = f"{__lot_detail.second_prize_cmt} * {__lot_detail.second_prize}{inline_sep_str}"
                    ops_list.append(
                        handle_lot_detail_ops(
                            show_str=_str,
                            attr_type=rand_color_ops
                        )
                    )
                if __lot_detail.third_prize_cmt:
                    _str = f"{__lot_detail.third_prize_cmt} * {__lot_detail.third_prize}{inline_sep_str}"
                    ops_list.append(
                        handle_lot_detail_ops(
                            show_str=_str,
                            attr_type=rand_color_ops
                        )
                    )
                _str = f"概率:{__lot_detail.chance}{inline_sep_str}"
                ops_list.append(
                    handle_lot_detail_ops(
                        show_str=_str,
                        attr_type=rand_color_ops
                    )
                )
                _str = __lot_detail.__dict__.get('etime_str')
                ops_list.append(
                    handle_lot_detail_ops(
                        show_str=_str,
                        attr_type=rand_color_ops
                    )
                )

                ret.ops.extend(ops_list)
                ret.ops.append(change_line_ops)  # 单条数据换行
            ret.ops.append(change_line_ops)  # 下个日期换行
        return ret, words

    def zhuanlan_date_sort(self, zhuanlan_data_order_by_date: [LotDetail], limit_date_switch: bool = False,
                           limit_date: int = 10) -> dict[str, list[LotDetail]]:
        '''
        为字典添加了etime_str的日期文字格式
        :param zhuanlan_data_order_by_date: 必须将这个数据按照日期排序先
        :param limit_date_switch:
        :param limit_date:
        :return: {'日期':[lot_detail...]}
        '''
        zhuanlan_data_order_by_date.sort(key=lambda x: x.lottery_time)
        oneDayList = {}  # 放入同一天的抽奖内容{'日期':[lot_detail...]}
        today = datetime.datetime.today()
        next_day = today + datetime.timedelta(days=1)
        for lottery_data in zhuanlan_data_order_by_date:
            lottery_end_date = datetime.datetime.strptime(
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(lottery_data.lottery_time))), '%Y-%m-%d %H:%M:%S')
            only_date = lottery_end_date.date()
            if limit_date_switch:
                if (only_date - next_day.date()).days > limit_date:  # 大于指定天数的抽奖不放进去
                    continue
            if int(lottery_data.lottery_time) < time.time():
                # 如果过期了进入下一条
                continue
            lottery_data.__dict__.update({'etime_str': lottery_end_date.strftime('%m-%d %H:%M')})  # 修改原始时间格式
            if oneDayList.get(str(lottery_end_date.date())):  # 如果存在当前抽奖日期，则直接append上去
                chongfu_Flag = False  # False表示没有重复
                for __ in oneDayList.get(str(lottery_end_date.date())):
                    if __.dynamic_id == lottery_data.dynamic_id:
                        chongfu_Flag = True
                if not chongfu_Flag:
                    oneDayList.get(str(lottery_end_date.date())).append(lottery_data)
            else:
                oneDayList.update({str(lottery_end_date.date()): [lottery_data]})  # 如果不存在就新建一个key把它存进去
        ret_List = {}  # 去重
        for k, v in oneDayList.items():  # {'日期':[lot_detail...]}
            ret_List.update({k: sorted(v, key=lambda x: x.lottery_time)})  # 每一个日期里面的排序
        return ret_List

    def zhuanlan_data_sort_by_date(self, zhuanlan_data: list) -> list:
        '''
        将所有专栏抽奖数据按开奖日期日期排序
        :return:
        '''
        return sorted(zhuanlan_data, key=lambda x: x['etime'])

    async def main(self,
                   all_official_lot_detail: List[LotDetail],
                   lot_type: Literal["官方抽奖", "充电抽奖"],
                   pub_cv: bool = True,
                   save_to_local_file: bool = True
                   ) -> CvContent:
        '''
        :return:
        '''
        all_official_lot_detail.sort(key=lambda x: x.lottery_time, reverse=True)  # 降序
        zhuanlan_data = self.zhuanlan_date_sort(all_official_lot_detail)
        cv_content, words = self.zhuanlan_format(zhuanlan_data)
        today = datetime.datetime.today()
        _ = datetime.timedelta(days=1)
        next_day = today + _
        title = f'【{next_day.date().month}.{next_day.date().day}】{lot_type}'
        return await self.pub_cv(
            title=title,
            abstract=self.abstract,
            cv_content=cv_content,
            words=words,
            pub_cv=pub_cv,
            save_to_local_file=save_to_local_file
        )
