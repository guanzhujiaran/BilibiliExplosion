import asyncio
import datetime
import json
import os
import re
import time
from copy import deepcopy
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Union, List, Set, Sequence

from py_mini_racer import MiniRacer

import Bilibili_methods.all_methods
from fastapi接口.log.base_log import get_others_lot_logger as get_others_lot_log
from fastapi接口.models.get_other_lot_dyn.dyn_robot_model import RobotScrapyInfo
from fastapi接口.service.MQ.base.MQClient.BiliLotDataPublisher import BiliLotDataPublisher
from fastapi接口.service.common_utils.dynamic_id_caculate import dynamic_id_2_ts
from fastapi接口.service.get_others_lot_dyn.Sql.models import TLotmaininfo, TLotuserinfo, TLotuserspaceresp, TLotdyninfo
from fastapi接口.service.get_others_lot_dyn.Sql.sql_helper import SqlHelper, get_other_lot_redis_manager
from fastapi接口.service.get_others_lot_dyn.svmJudgeBigLot.judgeBigLot import big_lot_predict
from fastapi接口.service.get_others_lot_dyn.svmJudgeBigReserve.judgeReserveLot import big_reserve_predict
from fastapi接口.service.grpc_module.grpc.bapi.biliapi import get_space_dynamic_req_with_proxy, \
    get_polymer_web_dynamic_detail, get_reply_main
from fastapi接口.service.grpc_module.src.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
from fastapi接口.service.grpc_module.src.SQLObject.models import Lotdata
from fastapi接口.service.opus新版官方抽奖.Model.BaseLotModel import ProgressCounter
from fastapi接口.service.opus新版官方抽奖.预约抽奖.db.models import TUpReserveRelationInfo
from fastapi接口.service.opus新版官方抽奖.预约抽奖.db.sqlHelper import bili_reserve_sqlhelper as mysq
from fastapi接口.utils.Common import asyncio_gather
from fastapi接口.utils.SqlalchemyTool import sqlalchemy_model_2_dict
from utl.pushme.pushme import pushme

BAPI = Bilibili_methods.all_methods.methods()
ctx = MiniRacer()
manual_reply_judge = ctx.eval(r"""
        manual_reply_judge= function (dynamic_content) {
					//判断是否需要人工回复 返回true需要人工判断  返回null不需要人工判断
					//64和67用作判断是否能使用关键词回复
					let none_lottery_word1 = /.*测试.{0,5}gua/gim.test(
						dynamic_content
					);
					if (none_lottery_word1) {
						return true;
					}
					dynamic_content = dynamic_content.replaceAll(/「/gim, "【");
					dynamic_content = dynamic_content.replaceAll(/」/gim, "】");
					dynamic_content = dynamic_content.replaceAll(/〗/gim, "】");
					dynamic_content = dynamic_content.replaceAll(/】/gim, "【");
					dynamic_content = dynamic_content.replaceAll(/“/gim, '"');
					dynamic_content = dynamic_content.replaceAll(/”/gim, '"');
					dynamic_content = dynamic_content.replaceAll(/＠/gim, "@");
					dynamic_content = dynamic_content.replaceAll(
						/@.{0,8} /gim,
						""
					);
					dynamic_content = dynamic_content.replaceAll(
						/好友/gim,
						"朋友"
					);
					dynamic_content = dynamic_content.replaceAll(
						/伙伴/gim,
						"朋友"
					);
					dynamic_content = dynamic_content.replaceAll(
						/安利/gim,
						"分享"
					);
					dynamic_content = dynamic_content.replaceAll(
						/【关注】/gim,
						""
					);
					dynamic_content = dynamic_content.replaceAll(
						/添加话题/gim,
						"带话题"
					);
					dynamic_content = dynamic_content.replaceAll(/\?/gim, "？");
					dynamic_content = dynamic_content.replaceAll(/:/gim, "：");
					let manual_re1 =
						/.*评论.{0,20}告诉|.*有关的评论|.*告诉.{0,20}留言/gim.test(
							dynamic_content
						);
					let manual_re2 =
						/.*评论.{0,20}理由|.*参与投稿.{0,30}有机会获得/gim.test(
							dynamic_content
						);
					let manual_re3 = /.*评论.{0,10}对|.*造.{0,3}句子/gim.test(
						dynamic_content
					);
					let manual_re4 =
						/.*猜赢|.*猜对|.*答对|.*猜到.{0,5}答案/gim.test(
							dynamic_content
						);
					let manual_re5 =
						/.*说.{0,10}说|.*谈.{0,10}谈|.*夸.{0,10}夸|评论.{0,10}写.{0,10}写|.*写下.{0,5}假如.{0,5}是|.*讨论.{0,10}怎么.{0,10}？/gim.test(
							dynamic_content
						);
					let manual_re7 =
						/.*最先猜中|.*带文案|.*许.{0,5}愿望/gim.test(
							dynamic_content
						);
					let manual_re8 = /.*新衣回/gim.test(dynamic_content);
					let manual_re9 =
						/.*留言.{0,10}建议|.*评论.{0,10}答|.*一句话证明|.*留言.{0,10}得分|.*有趣.{0,3}留言|.*有趣.{0,3}评论|.*留言.{0,3}晒出|.*评论.{0,3}晒出/gim.test(
							dynamic_content
						);
					let manual_re11 =
						/.*评论.{0,10}祝福|.*评论.{0,10}意见|.*意见.{0,10}评论|.*留下.{0,10}意见|.*留下.{0,15}印象|.*意见.{0,10}留下/gim.test(
							dynamic_content
						);
					let manual_re12 =
						/.*评论.{0,10}讨论|.*话题.{0,10}讨论|.*参与.{0,5}讨论/gim.test(
							dynamic_content
						);
					let manual_re14 =
						/.*评论.{0,10}说出|,*留言.{0,5}身高/gim.test(
							dynamic_content
						);
					let manual_re15 =
						/.*评论.{0,20}分享|.*评论.{0,20}互动((?!抽奖|,|，|来).)*$|.*评论.{0,20}提问|.*想问.{0,20}评论|.*想说.{0,20}评论|.*想问.{0,20}留言|.*想说.{0,20}留言/gim.test(
							dynamic_content
						);
					let manual_re16 = /.*评论.{0,10}聊.{0,10}聊/gim.test(
						dynamic_content
					);
					let manual_re17 = /.*评.{0,10}接力/gim.test(
						dynamic_content
					);
					let manual_re18 = /.*聊.{0,10}聊/gim.test(dynamic_content);
					let manual_re19 =
						/.*评论.{0,10}扣|.*评论.{0,5}说.{0,3}下/gim.test(
							dynamic_content
						);
					let manual_re20 = /.*转发.{0,10}分享/gim.test(
						dynamic_content
					);
					let manual_re21 = /.*评论.{0,10}告诉/gim.test(
						dynamic_content
					);
					let manual_re22 = /.*评论.{0,10}唠.{0,10}唠/gim.test(
						dynamic_content
					);
					let manual_re23 =
						/.*今日.{0,5}话题|.*参与.{0,5}话题|.*参与.{0,5}答题/gim.test(
							dynamic_content
						);
					let manual_re24 = /.*说.*答案|.*评论.{0,15}答案/gim.test(
						dynamic_content
					);
					let manual_re25 = /.*说出/gim.test(dynamic_content);
					let manual_re26 = /.*为.{0,10}加油/gim.test(
						dynamic_content
					);
					let manual_re27 =
						/.*评论.{0,10}话|.*你中意的|.*评.{0,10}你.{0,5}的|.*写上.{0,10}你.{0,5}的|.*写下.{0,10}你.{0,5}的/gim.test(
							dynamic_content
						);
					let manual_re28 =
						/.*评论.{0,15}最想做7的事|.*评.{0,15}最喜欢|.*评.{0,15}最.{0,7}的事|.*最想定制的画面|最想.{0,20}\?|最想.{0,20}？/gim.test(
							dynamic_content
						);
					let manual_re29 =
						/.*分享.{0,20}经历|.*经历.{0,20}分享/gim.test(
							dynamic_content
						);
					let manual_re30 = /.*分享.{0,20}心情/gim.test(
						dynamic_content
					);
					let manual_re31 = /.*评论.{0,10}句|评论.{0,6}包含/gim.test(
						dynamic_content
					);
					let manual_re32 = /.*转关评下方视频/gim.test(
						dynamic_content
					);
					let manual_re33 =
						/.*分享.{0,10}美好|.*分享.{0,10}期待/gim.test(
							dynamic_content
						);
					let manual_re34 = /.*视频.{0,10}弹幕/gim.test(
						dynamic_content
					);
					let manual_re35 = /.*生日快乐/gim.test(dynamic_content);
					let manual_re36 = /.*一句话形容/gim.test(dynamic_content);
					let manual_re38 =
						/.*分享.{0,10}喜爱|.*分享.{0,10}最爱|.*推荐.{0,10}最爱|.*推荐.{0,10}喜爱/gim.test(
							dynamic_content
						);
					let manual_re39 =
						/.*分享((?!,|，).){0,10}最|.*评论((?!,|，).){0,10}最/gim.test(
							dynamic_content
						);
					let manual_re40 =
						/.*带话题.{0,15}晒|.*带话题.{0,15}讨论/gim.test(
							dynamic_content
						);
					let manual_re41 =
						/.*分享.{0,15}事|点赞.{0,3}数.{0,3}前/gim.test(
							dynamic_content
						);
					let manual_re42 = /.*送出.{0,15}祝福/gim.test(
						dynamic_content
					);
					let manual_re43 = /.*评论.{0,30}原因/gim.test(
						dynamic_content
					);
					let manual_re47 = /.*答案.{0,10}参与/gim.test(
						dynamic_content
					);
					let manual_re48 = /.*唠.{0,5}唠/gim.test(dynamic_content);
					let manual_re49 = /.*分享一下/gim.test(dynamic_content);
					let manual_re50 = /.*评论.{0,30}故事/gim.test(
						dynamic_content
					);
					let manual_re51 =
						/.*告诉.{0,30}什么|.*告诉.{0,30}最|有什么安排呀～/gim.test(
							dynamic_content
						);
					let manual_re53 = /.*发布.{0,20}图.{0,5}动态/gim.test(
						dynamic_content
					);
					let manual_re54 = /.*视频.{0,20}评论/gim.test(
						dynamic_content
					);
					let manual_re55 = /.*复zhi|.*长按/gim.test(dynamic_content);
					let manual_re56 = /.*多少.{0,10}合适/gim.test(
						dynamic_content
					);
					let manual_re57 = /.*喜欢.{0,5}哪/gim.test(dynamic_content);
					let manual_re58 =
						/.*多少.{0,15}？|.*多少.{0,15}\?|.*有没有.{0,15}？|.*有没有.{0,15}\?|.*是什么.{0,15}？|.*是什么.{0,15}\?/gim.test(
							dynamic_content
						);
					let manual_re61 = /.*看.{0,10}猜/gim.test(dynamic_content);
					let manual_re63 =
						/.*评论.{0,10}猜|.*评论.{0,15}预测/gim.test(
							dynamic_content
						);
					let manual_re65 = /.*老规矩你们懂的/gim.test(
						dynamic_content
					);
					let manual_re67 =
						/.*[评|带]((?!抽奖|,|，|来).){0,7}“|.*[评|带]((?!抽奖|,|，|来).){0,7}"|.*[评|带]((?!抽奖|,|，|来).){0,7}【|.*[评|带]((?!抽奖|,|，|来).){0,7}:|.*[评|带]((?!抽奖|,|，|来).){0,7}：|.*[评|带]((?!抽奖|,|，|来).){0,7}「|.*带关键词.{0,7}"|.*评论关键词[“”‘’"']|.*留言((?!抽奖|,|，|来).){0,7}“|.*对出.{0,10}下联.{0,5}横批|.*回答.{0,8}问题|.*留下.{0,10}祝福语|.*留下.{0,10}愿望|.*找到.{0,10}不同的.{0,10}留言|.*答案放在评论区|.*几.{0,5}呢？|.*有奖问答|.*想到.{0,19}关于.{0,20}告诉|.*麻烦大伙评论这个|报暗号【.{0,4}】|评论.{0,3}输入.{0,3}["“”:：]|.*评论.{0,7}暗号/gim.test(
							dynamic_content
						);
					let manual_re76 =
						/.*留言((?!抽奖|,|，|来).).{0,7}"|.*留下((?!抽奖|,|，|来).){0,5}“|.*留下((?!抽奖|,|，|来).){0,5}【|.*留下((?!抽奖|,|，|来).){0,5}:|.*留下((?!抽奖|,|，|来).){0,5}：|.*留下((?!抽奖|,|，|来).){0,5}「/gim.test(
							dynamic_content
						);
					let manual_re77 =
						/.*留言((?!抽奖|,|，|来).).{0,7}"|.*留言((?!抽奖|,|，|来).).{0,7}“|.*留言((?!抽奖|,|，|来).){0,7}【|.*留言((?!抽奖|,|，|来).){0,7}:|.*留言((?!抽奖|,|，|来).){0,7}：|.*留言((?!抽奖|,|，|来).){0,7}「/gim.test(
							dynamic_content
						);
					let manual_re64 =
						/和.{0,5}分享.{0,5}的|.*分享.{0,10}你的|.*正确回答|.*回答正确|.*评论.{0,10}计划|.*定.{0,10}目标.{0,5}？|.*定.{0,10}目标.{0,5}?|.*评论.{0,7}看的电影|.*如果.{0,20}觉得.{0,10}？|.*如果.{0,20}觉得.{0,10}\?|评论.{0,7}希望.{0,5}|.*竞猜[\s\S]{0,15}[答评]|.*把喜欢的.{0,10}评论|.*评论.{0,5}解.{0,5}密|.*这款.{0,10}怎么.{0,3}？|.*最喜欢.{0,5}的.*为什么？|.*留下.{0,15}的.{0,5}疑问|.*写下.{0,10}的.{0,5}问题/gim.test(
							dynamic_content
						);
					let manual_re6 =
						/.*@TA|.*@.{0,15}朋友|.*艾特|.*@.{0,3}你的|.*标记.{0,10}朋友|.*@{0,15}赞助商|.*发表你的新年愿望\+个人的昵称|.*抽奖规则请仔细看图片|.*带上用户名|.*活动详情请戳图片|.*@个人用户名|评论.{0,5}附带.{0,10}相关内容|回复.{0,5}视频.{0,10}相关内容|.*评论.{0,5}昵称/gim.test(
							dynamic_content
						);
					let manual_re62 =
						/.*评论.{0,10}#.*什么|.*转评.{0,3}#.*(?<=，)/gim.test(
							dynamic_content
						);
					let manual_re68 =
						/.*将.{0,10}内容.{0,10}评|.*打几分？/gim.test(
							dynamic_content
						);
					let manual_re70 =
						/.*会不会.{0,20}？|.*会不会.{0,20}\?|如何.{0,20}？|如何.{0,20}\?/gim.test(
							dynamic_content
						);
					let manual_re71 =
						/.*猜.{0,10}猜|.*猜.{0,10}比分|.*猜中.{0,10}获得|.*猜中.{0,10}送出/gim.test(
							dynamic_content
						);
					let manual_re72 = /.*生日|.*新年祝福/gim.test(
						dynamic_content
					);
					let manual_re73 =
						/.*知道.{0,15}什么.{0,15}？|.*知道.{0,15}什么.{0,15}\?|.*用什么|.*评.{0,10}收.{0,5}什么.{0.7}\?|.*评.{0,10}收.{0,5}什么.{0,7}？|.*抽奖口令.{0,3}：/gim.test(
							dynamic_content
						);
					let manual_re74 =
						/.*领.{0,10}红包.{0,5}大小|.*领.{0,10}多少.{0,10}红包|.*红包金额/gim.test(
							dynamic_content
						);
					let manual_re75 =
						/.*本周话题|.*互动话题|.*互动留言|.*互动时间|.*征集.{0,10}名字|.*投票.{0,5}选.{0,10}最.{0,5}的|.*一人说一个谐音梗|帮.{0,5}想想.{0,5}怎么|评论.{0,5}想给.{0,7}的/gim.test(
							dynamic_content
						);

					return (
						manual_re1 ||
						manual_re2 ||
						manual_re3 ||
						manual_re4 ||
						manual_re5 ||
						manual_re6 ||
						manual_re7 ||
						manual_re8 ||
						manual_re9 ||
						manual_re11 ||
						manual_re12 ||
						manual_re14 ||
						manual_re15 ||
						manual_re16 ||
						manual_re17 ||
						manual_re18 ||
						manual_re19 ||
						manual_re20 ||
						manual_re21 ||
						manual_re22 ||
						manual_re23 ||
						manual_re24 ||
						manual_re25 ||
						manual_re26 ||
						manual_re27 ||
						manual_re28 ||
						manual_re29 ||
						manual_re30 ||
						manual_re31 ||
						manual_re32 ||
						manual_re33 ||
						manual_re34 ||
						manual_re35 ||
						manual_re36 ||
						manual_re38 ||
						manual_re39 ||
						manual_re40 ||
						manual_re41 ||
						manual_re42 ||
						manual_re43 ||
						manual_re76 ||
						manual_re47 ||
						manual_re48 ||
						manual_re49 ||
						manual_re50 ||
						manual_re51 ||
						manual_re53 ||
						manual_re54 ||
						manual_re58 ||
						manual_re55 ||
						manual_re56 ||
						manual_re57 ||
						manual_re61 ||
						manual_re62 ||
						manual_re63 ||
						manual_re64 ||
						manual_re65 ||
						manual_re67 ||
						manual_re68 ||
						manual_re70 ||
						manual_re71 ||
						manual_re72 ||
						manual_re73 ||
						manual_re74 ||
						manual_re75 ||
						manual_re77 ||
						manual_re77
					);
				}
            """)
_is_use_available_proxy = True
GET_LOT_DYN_TIME_LIMIT = 20 * 3600 * 24
HighlightWordList = [
    'jd卡',
    '京东卡',
    '京东E卡',
    '红包',
    '主机',
    '显卡',
    '电脑',
    '天猫卡',
    '猫超卡',
    '现金',
    '见盘',
    '耳机',
    '鼠标',
    '手办',
    '景品',
    'ps5',
    '内存',
    '风扇',
    '散热',
    '水冷',
    '硬盘',
    '显示器',
    '主板',
    '电源',
    '机箱',
    'fgo',
    '折现',
    '樱瞳',
    '盈通',
    '🧧',
    '键盘',
    '游戏本',
    '御神子',
    '琉璃子',
    '固态',
    '手机',
    'GB',
    'TB',
    'tb',  # 可能是显存大小，硬盘容量，内存条容量等参数
    'switch',
    '冰箱'
]


class FileMap(StrEnum):
    current_file_path = os.path.dirname(os.path.abspath(__file__))
    github_bili_upload = os.path.join(current_file_path, '../../../github/bili_upload')


class OfficialLotType(StrEnum):
    reserve_lot = '预约抽奖'
    charge_lot = '充电抽奖'
    official_lot = '官方抽奖'
    lot_dyn_origin_dyn = '抽奖动态的源动态'


@dataclass
class BiliDynamicItemJudgeLotteryResult:
    cur_dynamic: TLotdyninfo | None = field(default=None)  # 如果是本来就判断过的，那么同样设置成None
    orig_dynamic: TLotdyninfo | None = field(default=None)
    attached_card: TLotdyninfo | None = field(default=None)


@dataclass
class BiliDynamicItem:
    dynamic_id: int | str = field(default=0, )  # 动态类型
    dynamic_type: int | str = field(default=2, )  # 动态类型
    dynamic_rid: int | str = field(default=0, )  # 动态rid
    dynamic_raw_resp: dict = field(default_factory=dict, )  # 返回的响应，带code和data的dict
    dynamic_raw_detail: dict = field(default_factory=dict)  # 放解析下来的请求的字典，不高兴搞成class了
    bili_judge_lottery_result: BiliDynamicItemJudgeLotteryResult = field(
        default_factory=BiliDynamicItemJudgeLotteryResult)
    is_lot_orig: bool = field(default=False)  # 是否是抽奖动态的原动态
    is_use_available_proxy: bool = field(default=_is_use_available_proxy)

    def __post_init__(self):
        if not self.dynamic_id and not (self.dynamic_rid and self.dynamic_type):
            get_others_lot_log.critical(f'没有有效的动态信息！')
            raise ValueError('没有有效的动态信息！')

    def __hash__(self):
        if self.dynamic_id:
            return hash(int(self.dynamic_id))
        return hash(- int(self.dynamic_type) - int(self.dynamic_rid))

    async def _init(self):
        if not self.dynamic_id and self.dynamic_rid and self.dynamic_type:
            self.dynamic_id = await SqlHelper.getDynIdByRidType(self.dynamic_rid, self.dynamic_type)

    # region 获取评论
    async def _get_topcomment_with_proxy(self, dynamicid, rid, pn, _type, mid):
        iner_replies = ''
        pinglunreq = await get_reply_main(dynamicid, rid, pn, _type, 3)
        try:
            pinglun_dict = pinglunreq
            pingluncode = pinglun_dict.get('code')
            if pingluncode != 0:
                message = pinglun_dict.get('message')
                if message != 'UP主已关闭评论区' and message != '啥都木有' and message != '评论区已关闭':
                    get_others_lot_log.error(f'【未知原因】获取置顶评论失败：{pinglun_dict}')
                    return ''
                else:
                    get_others_lot_log.debug(f'获取置顶评论失败：{pinglun_dict}')
                    return ''
            reps = pinglun_dict.get('data').get('replies')
            if reps is not None:
                for i in reps:
                    pinglun_mid = i.get('mid')
                    if pinglun_mid == mid:
                        iner_replies += i.get('content').get('message')
            data = pinglun_dict.get('data')
            topreplies = data.get('top_replies')
            topmsg = ''
            if topreplies is not None:
                for tprps in topreplies:
                    topmsg += tprps.get('content').get('message')
                    if tprps.get('replies'):
                        for tprpsrps in tprps.get('replies'):
                            if tprpsrps.get('mid') == mid:
                                iner_replies += tprpsrps.get('content').get('message')
                topmsg += iner_replies
                get_others_lot_log.info(f'https://t.bilibili.com/{dynamicid}\t置顶评论：{topmsg}')
            else:
                get_others_lot_log.info(f'https://t.bilibili.com/{dynamicid}\t无置顶评论')
                topmsg = '' + iner_replies
        except Exception as e:
            get_others_lot_log.exception(e)
            get_others_lot_log.info('获取置顶评论失败')
            pinglun_dict = pinglunreq
            data = pinglun_dict.get('data')
            get_others_lot_log.info(pinglun_dict)
            get_others_lot_log.info(data)
            topmsg = ''
            get_others_lot_log.info(BAPI.timeshift(int(time.time())))
            if data == '评论区已关闭':
                topmsg = data
        return topmsg

    # endregion

    async def __solve_dynamic_item_detail(self, dynamic_req: dict) -> dict:
        """
        使用代理获取动态详情，传入空间的动态响应前，需要先构建成单个动态的响应！！！
        :param dynamic_req: {code:4101131,data:{item:...} }
        :return:
        structure = {
            'dynamic_id': dynamic_id,
            'desc': desc,
            'type': dynamic_type,
            'rid': dynamic_rid,
            'relation': relation,
            'is_liked': is_liked,
            'author_uid': author_uid,
            'author_name': author_name,
            'comment_count': comment_count,
            'forward_count': forward_count,  # 转发数
            'like_count': like_count,
            'dynamic_content': dynamic_content,
            'pub_time': pub_time,
            'pub_ts': pub_ts,
            'official_verify_type': official_verify_type,
            'card_stype': card_stype,
            'top_dynamic': top_dynamic,
            'orig_dynamic_id': orig_dynamic_id,
            'orig_mid': orig_mid,
            'orig_name': orig_name,
            'orig_pub_ts': orig_pub_ts,
            'orig_official_verify': orig_official_verify,
            'orig_comment_count': orig_comment_count,
            'orig_forward_count': orig_forward_count,
            'orig_like_count': orig_like_count,
            'orig_dynamic_content': orig_dynamic_content,
            'orig_relation': orig_relation,
            'orig_desc': orig_desc
        }
        """
        get_others_lot_log.debug(f'正在解析动态详情：{self.dynamic_id}')
        try:
            if dynamic_req.get('code') == 4101131 or dynamic_req.get('data') is None:
                get_others_lot_log.info(f'动态内容不存在！{self.dynamic_id}\t{dynamic_req}')
                return {'rawJSON': None}
            # get_others_lot_log.info(f'获取成功header:{headers}')
            dynamic_dict = dynamic_req
            dynamic_data = dynamic_dict.get('data')
            dynamic_item = dynamic_data.get('item')
            comment_type = dynamic_item.get('basic').get('comment_type')
            dynamic_type = '8'
            if str(comment_type) == '17':
                dynamic_type = '4'
            elif str(comment_type) == '1':
                dynamic_type = '8'
            elif str(comment_type) == '11':
                dynamic_type = '2'
            elif str(comment_type) == '12':
                dynamic_type = '64'
            card_stype = dynamic_item.get('type')
            dynamic_data_dynamic_id = dynamic_item.get('id_str')
            if str(dynamic_type) == '2' and str(dynamic_data_dynamic_id) != str(self.dynamic_id):
                get_others_lot_log.critical(f"获取的动态信息与需要的动态不符合！！！重新获取\t{dynamic_data}")
                new_req = await self._get_dyn_detail_resp(force_api=True)
                return await self.__solve_dynamic_item_detail(new_req)
            dynamic_rid = dynamic_item.get('basic').get('comment_id_str')
            relation = dynamic_item.get('modules').get('module_author').get('following')
            author_uid = dynamic_item.get('modules').get('module_author').get('mid')
            author_name = dynamic_item.get('modules').get('module_author').get('name')
            # pub_time = dynamic_item.get('modules').get('module_author').get('pub_time') # 这个遇到一些电视剧，番剧之类的特殊响应会无法获取到
            pub_time = datetime.datetime.fromtimestamp(
                dynamic_id_2_ts(dynamic_data_dynamic_id)).strftime(
                '%Y年%m月%d日 %H:%M') if dynamic_data_dynamic_id else datetime.datetime.fromtimestamp(100000)
            pub_ts = dynamic_item.get('modules').get('module_author').get('pub_ts')
            self.dynamic_rid = dynamic_rid
            try:
                official_verify_type = dynamic_item.get('modules').get('module_author').get(
                    'official_verify').get('type')
                if type(official_verify_type) is str:
                    official_verify_type = 1
            except Exception as e:
                official_verify_type = -1
            try:
                comment_count = dynamic_item.get('modules').get('module_stat').get('comment').get('count')
                forward_count = dynamic_item.get('modules').get('module_stat').get('forward').get('count')
                like_count = dynamic_item.get('modules').get('module_stat').get('like').get('count')
            except Exception:
                comment_count = -2
                forward_count = -2
                like_count = -2
            dynamic_content1 = ''
            if dynamic_item.get('modules').get('module_dynamic').get('desc'):
                dynamic_content1 += dynamic_item.get('modules').get('module_dynamic').get('desc').get(
                    'text')
            dynamic_content2 = ''
            if dynamic_item.get('modules').get('module_dynamic').get('major'):
                if dynamic_item.get('modules').get('module_dynamic').get('major').get('archive'):
                    dynamic_content2 += dynamic_item.get('modules').get('module_dynamic').get('major').get(
                        'archive').get('desc') + dynamic_item.get('modules').get('module_dynamic').get(
                        'major').get(
                        'archive').get('title')
                if dynamic_item.get('modules').get('module_dynamic').get('major').get('article'):
                    dynamic_content2 += str(
                        dynamic_item.get('modules').get('module_dynamic').get('major').get(
                            'article').get('desc')) + dynamic_item.get('modules').get('module_dynamic').get(
                        'major').get(
                        'article').get('title')
                if dynamic_item.get('modules').get('module_dynamic').get('major').get('opus'):
                    dynamic_content2 += dynamic_item.get('modules').get('module_dynamic').get('major').get(
                        'opus').get('summary').get('text')
                    if dynamic_item.get('modules').get('module_dynamic').get('major').get('opus').get(
                            'title'):
                        dynamic_content2 += dynamic_item.get('modules').get('module_dynamic').get(
                            'major').get('opus').get('title')
            dynamic_content = dynamic_content1 + dynamic_content2
            desc = dynamic_item.get('modules').get(
                'module_dynamic').get(
                'desc')

            if relation:
                relation = 1
            else:
                relation = 0
            is_liked = 0
            if relation != 1:
                get_others_lot_log.info(
                    f'未关注的response\nhttps://space.bilibili.com/{author_uid}\n{dynamic_data_dynamic_id}')
        except Exception as e:
            get_others_lot_log.exception(
                f'解析动态失败！\tsolve_dynamic_item_detail\thttps://t.bilibili.com/{self.dynamic_id}\t{dynamic_req}\t{e}')
            if dynamic_req.get('code') == -412:
                get_others_lot_log.info('412风控')
                await asyncio.sleep(10)
                new_req = await self._get_dyn_detail_resp(force_api=True)
                return await self.__solve_dynamic_item_detail(new_req)
            elif dynamic_req.get('code') == 4101128:
                get_others_lot_log.info(dynamic_req.get('message'))
            elif dynamic_req.get('code') is None:
                new_req = await self._get_dyn_detail_resp(force_api=True)
                return await self.__solve_dynamic_item_detail(new_req)
            else:
                get_others_lot_log.critical(dynamic_req)
                await asyncio.sleep(10)
                new_req = await self._get_dyn_detail_resp(force_api=True)
                return await self.__solve_dynamic_item_detail(new_req)
            return {}

        top_dynamic = None
        try:
            module_tag = dynamic_item.get('modules').get('module_tag')
            if module_tag:
                module_tag_text = module_tag.get('text')
                if module_tag_text == "置顶":
                    top_dynamic = True
                else:
                    get_others_lot_log.critical(f'未知动态tag:{module_tag}')
            else:
                top_dynamic = False
        except Exception as e:
            top_dynamic = None

        orig_name = None
        orig_mid = None
        orig_official_verify = None
        orig_pub_ts = None
        orig_comment_count = None
        orig_forward_count = None
        orig_dynamic_content = None
        orig_like_count = None
        orig_relation = None
        orig_is_liked = None
        orig_dynamic_id = None
        orig_desc = None
        dynamic_orig = dynamic_item.get('orig')
        try:
            if dynamic_orig:
                orig_dynamic_id = dynamic_item.get('orig').get('id_str')
                orig_mid = dynamic_item.get('orig').get('modules').get('module_author').get('mid')
                orig_name = dynamic_item.get('orig').get('modules').get('module_author').get('name')
                orig_pub_ts = dynamic_item.get('orig').get('modules').get('module_author').get('pub_ts')
                if dynamic_item.get('orig').get('modules').get('module_author').get(
                        'official_verify'):
                    orig_official_verify = dynamic_item.get('orig').get('modules').get('module_author').get(
                        'official_verify').get('type')
                else:
                    orig_official_verify = dynamic_item.get('orig').get('modules').get('module_author').get(
                        'type')
                # orig_comment_count = dynamic_item.get('orig').get('modules').get('module_stat').get('comment').get(
                #     'count')
                # orig_forward_count = dynamic_item.get('orig').get('modules').get('module_stat').get('forward').get(
                #     'count')
                # orig_like_count = dynamic_item.get('orig').get('modules').get('module_stat').get('like').get('count')
                orig_dynamic_content1 = ''
                if dynamic_item.get('orig').get('modules').get('module_dynamic').get('desc'):
                    orig_dynamic_content1 = dynamic_item.get('orig').get('modules').get(
                        'module_dynamic').get(
                        'desc').get('text')
                orig_dynamic_content2 = ''
                if dynamic_item.get('orig').get('modules').get('module_dynamic').get('major'):
                    if dynamic_item.get('orig').get('modules').get('module_dynamic').get('major').get(
                            'archive'):
                        orig_dynamic_content2 += dynamic_item.get('orig').get('modules').get(
                            'module_dynamic').get('major').get('archive').get('desc')
                    if dynamic_item.get('orig').get('modules').get('module_dynamic').get('major').get(
                            'article'):
                        orig_dynamic_content2 += str(
                            dynamic_item.get('orig').get('modules').get('module_dynamic').get(
                                'major').get('article').get('desc')) + \
                                                 dynamic_item.get('orig').get('modules').get(
                                                     'module_dynamic').get('major').get('article').get('title')
                    if dynamic_item.get('orig').get('modules').get('module_dynamic').get('major').get(
                            'opus'):
                        orig_dynamic_content2 += dynamic_item.get('orig').get('modules').get(
                            'module_dynamic').get(
                            'major').get('opus').get('summary').get('text')
                orig_dynamic_content = orig_dynamic_content1 + orig_dynamic_content2
                orig_desc = dynamic_item.get('orig').get('modules').get(
                    'module_dynamic').get(
                    'desc')
                orig_relation = dynamic_item.get('orig').get('modules').get('module_author').get(
                    'following')
                if orig_relation:
                    orig_relation = 1
                else:
                    orig_relation = 0
                # orig_is_liked = dynamic_item.get('orig').get('modules').get('module_stat').get('like').get(
                #     'status')
                # if orig_is_liked:
                #     orig_is_liked = 1
                # else:
                #     orig_is_liked = 0
            else:
                get_others_lot_log.info('非转发动态，无原动态')
        except Exception as e:
            get_others_lot_log.exception(f"解析动态失败！\n{dynamic_req}\n{e}")
        if not self.dynamic_id:
            if self.dynamic_rid and self.dynamic_type:
                await SqlHelper.setDynIdByRidType(dynamic_data_dynamic_id, dynamic_rid, dynamic_type)
                self.dynamic_id = dynamic_data_dynamic_id
            else:
                get_others_lot_log.critical(f'动态解析失败！\n{dynamic_req}')
        structure = {
            'rawJSON': dynamic_item,  # 原始的item数据
            'dynamic_id': dynamic_data_dynamic_id,
            'dynamic_item': dynamic_item,
            'desc': desc,
            'type': dynamic_type,
            'rid': dynamic_rid,
            'relation': relation,
            'is_liked': is_liked,
            'author_uid': author_uid,
            'author_name': author_name,
            'comment_count': comment_count,
            'forward_count': forward_count,  # 转发数
            'like_count': like_count,
            'dynamic_content': dynamic_content,
            'pub_time': pub_time,
            'pub_ts': pub_ts,
            'official_verify_type': official_verify_type,
            'module_dynamic': dynamic_item.get('modules').get('module_dynamic'),  # 动态模块

            'card_stype': card_stype,
            'top_dynamic': top_dynamic,

            'orig_dynamic_id': orig_dynamic_id,
            'dynamic_orig': dynamic_orig,
            'orig_mid': orig_mid,
            'orig_name': orig_name,
            'orig_pub_ts': orig_pub_ts,
            'orig_official_verify': orig_official_verify,
            'orig_comment_count': orig_comment_count,
            'orig_forward_count': orig_forward_count,
            'orig_like_count': orig_like_count,
            'orig_dynamic_content': orig_dynamic_content,
            'orig_relation': orig_relation,
            'orig_desc': orig_desc
        }
        return structure

    async def _solve_dynamic_item_detail(self):
        if not self.dynamic_raw_resp:
            await self._get_dyn_detail_resp()
        dynamic_raw_detail = await self.__solve_dynamic_item_detail(self.dynamic_raw_resp)
        self.dynamic_raw_detail = dynamic_raw_detail
        return dynamic_raw_detail

    async def _get_dyn_detail_resp(self, force_api: bool = False) -> dict:
        """
        返回{
                        'code':0,
                        'data':{
                            "item":dynamic_req
                        }
                    }这样的dict
        :return:
        """
        await self._init()
        get_others_lot_log.debug(f'正在获取动态响应：{self.dynamic_id}')
        dynamic_req = None
        dynamic_detail_resp = None
        if self.dynamic_id and not force_api:
            is_dyn_exist = await SqlHelper.isExistDynInfoByDynId(self.dynamic_id)  # 看动态数据库里面有没有
            if is_dyn_exist:
                dynamic_detail_resp = is_dyn_exist.rawJsonStr
                if dynamic_detail_resp is not None:
                    get_others_lot_log.debug(f'动态【{self.dynamic_id}】在动态数据库中，使用数据库数据')
                    dynamic_req = {
                        'code': 0,
                        'data': {
                            "item": dynamic_detail_resp
                        }
                    }
                else:
                    get_others_lot_log.debug(
                        f'动态【{self.dynamic_id}】在动态数据库中，但是类型【{is_dyn_exist.officialLotType}】需要使用api获取')
            else:
                get_others_lot_log.warning(
                    f'动态【{self.dynamic_id}】不在动态数据库中，检查空间动态')

            if not bool(dynamic_detail_resp):  # 如果动态数据库里面的还是需要获取api，那就查看空间数据库的内容
                is_space_exist = await SqlHelper.isExistSpaceInfoByDynId(self.dynamic_id)  # 看空间里面有没有
                if is_space_exist:
                    # get_others_lot_log.critical(f'存在过的动态！！！{isDynExist.__dict__}')
                    dynamic_detail_resp = is_space_exist.spaceRespJson
                    if dynamic_detail_resp is not None:
                        get_others_lot_log.debug(f'动态【{self.dynamic_id}】在空间数据库中，使用数据库数据')
                        dynamic_req = {
                            'code': 0,
                            'data': {
                                "item": dynamic_detail_resp
                            }
                        }
                    else:
                        get_others_lot_log.warning(
                            f'动态【{self.dynamic_id}】在空间数据库中，但空间spaceRespJson为None，需要使用api获取')
                else:
                    get_others_lot_log.warning(
                        f'动态【{self.dynamic_id}】不在空间数据库中，需要使用api获取')

        force_api = not bool(dynamic_detail_resp)  # 查看是否缺少模块，缺少模块就强制重新获取
        try:
            if not dynamic_req or force_api:
                get_others_lot_log.debug(
                    f'动态【{self.dynamic_id}】使用api获取\n{dynamic_req}\n{dynamic_detail_resp}')
                if str(self.dynamic_type) != '2' and not self.dynamic_id:
                    dynamic_req = await get_polymer_web_dynamic_detail(
                        rid=self.dynamic_rid,
                        dynamic_type=self.dynamic_type,
                        is_use_available_proxy=self.is_use_available_proxy
                    )
                else:
                    dynamic_req = await get_polymer_web_dynamic_detail(
                        dynamic_id=self.dynamic_id,
                        is_use_available_proxy=self.is_use_available_proxy
                    )
        except Exception as e:
            get_others_lot_log.exception(e)
            await asyncio.sleep(10)
            return await self._get_dyn_detail_resp()
        self.dynamic_raw_resp = dynamic_req
        return dynamic_req

    async def _solve_official_lot_data(self,
                                       dyn_id: Union[str, int],
                                       lot_type: OfficialLotType,
                                       official_lot_id: str):
        """
        将官方抽奖数据爬取并上传到数据库
        :param official_lot_id:
        :param lot_type:
        :param dyn_id:
        :return:
        """
        try:
            business_type = 0
            business_id = 0
            if lot_type == OfficialLotType.official_lot:
                business_type = 1
                business_id = dyn_id
            elif lot_type == OfficialLotType.reserve_lot:
                business_type = 10
                business_id = official_lot_id
            elif lot_type == OfficialLotType.charge_lot:
                business_type = 12
                business_id = dyn_id
            if business_type == 0 or business_id == 0:
                raise ValueError(f'未知的官方抽奖类型：{lot_type}！！！')
            await BiliLotDataPublisher.pub_official_reserve_charge_lot(
                business_type=business_type,
                business_id=business_id,
                origin_dynamic_id=dyn_id,
                extra_routing_key='GetOthersLotDyn.solve_official_lot_data'
            )
        except Exception as e:
            get_others_lot_log.exception(f'官方抽奖数据提取失败！！！\n{e}')

    async def judge_lottery(self,
                            highlight_word_list: List[str],
                            lotRound_id: int
                            ) -> BiliDynamicItemJudgeLotteryResult:
        """
        判断是否是抽奖 并且存储到数据库
        :param lotRound_id:
        :param highlight_word_list:
        :return:
        """
        await self._init()
        get_others_lot_log.debug(f'正在判断抽奖动态：{self.dynamic_id}')
        cur_dynamic = None
        orig_dynamic = None
        attached_card = None
        suffix = ''
        is_lot = True
        if self.dynamic_id:
            t_lot_dyn_info = await SqlHelper.getDynInfoByDynamicId(self.dynamic_id)
            if t_lot_dyn_info:  # 如果是本轮没有跑完的，那就添加进去
                if t_lot_dyn_info.dynLotRound_id == lotRound_id:
                    self.bili_judge_lottery_result = BiliDynamicItemJudgeLotteryResult(cur_dynamic=t_lot_dyn_info)
                # else:
                #     self.bili_judge_lottery_result = BiliDynamicItemJudgeLotteryResult()  # 这个是以前的动态，不加进去了
                #     return self.bili_judge_lottery_result
        await self._solve_dynamic_item_detail()
        dynamic_detail = self.dynamic_raw_detail
        try:
            if dynamic_detail and dynamic_detail.get('dynamic_id'):
                dynamic_detail_dynamic_id = dynamic_detail['dynamic_id']  # 获取正确的动态id，不然可能会是rid或者aid
                dynamic_content = dynamic_detail['dynamic_content']
                author_name = dynamic_detail['author_name']
                pub_time = dynamic_detail['pub_time']
                pub_ts = dynamic_detail['pub_ts']
                comment_count = dynamic_detail['comment_count']
                forward_count = dynamic_detail['forward_count']
                official_verify_type = dynamic_detail['official_verify_type']
                author_uid = dynamic_detail['author_uid']
                rid = dynamic_detail['rid']
                _type = dynamic_detail['type']
                module_dynamic: dict = dynamic_detail['module_dynamic']
                rawJSON = dynamic_detail['rawJSON']
                is_official_lot = False
                is_charge_lot = False
                is_reserve_lot = False
                lot_rid = ''
                for k, v in module_dynamic.items():
                    if k == 'additional':
                        if v:
                            if v.get('upower_lottery'):
                                lot_rid = str(v.get('upower_lottery').get('rid'))
                                is_charge_lot = True
                                break
                            if _reserve := v.get('reserve'):
                                if 'lottery/result' in json.dumps(_reserve):
                                    lot_rid = _reserve.get('rid')
                                    is_reserve_lot = True
                                    break
                    if k == 'major':
                        if v:
                            if v.get('type') == 'MAJOR_TYPE_OPUS':
                                for nodes in v.get('opus').get('summary').get('rich_text_nodes'):
                                    if nodes['type'] == 'RICH_TEXT_NODE_TYPE_LOTTERY':
                                        is_official_lot = True
                                        lot_rid = str(nodes['rid'])
                                        break
                    if k == 'desc':
                        if v:
                            if v.get('rich_text_nodes'):
                                for nodes in v.get('rich_text_nodes'):
                                    if nodes['type'] == 'RICH_TEXT_NODE_TYPE_LOTTERY':
                                        is_official_lot = True
                                        lot_rid = str(nodes['rid'])
                                        break
                if dynamic_content != '':
                    # deadline = self.nlp.information_extraction(dynamic_content, ['开奖日期'])['开奖日期']
                    deadline = None
                else:
                    get_others_lot_log.info(
                        f'https://t.bilibili.com/{dynamic_detail_dynamic_id}?type={self.dynamic_type}\t动态内容为空!')
                    deadline = None
                premsg = BAPI.pre_msg_processing(dynamic_content)
                ret_url = f'https://t.bilibili.com/{dynamic_detail_dynamic_id}'
                if BAPI.zhuanfapanduan(dynamic_content):
                    ret_url += '?tab=2'
                manual_judge = ''
                if await asyncio.to_thread(manual_reply_judge, dynamic_content):
                    manual_judge = '人工判断'
                high_lights_list = []
                for i in highlight_word_list:
                    if i in dynamic_content:
                        high_lights_list.append(i)
                if re.match(r'.*//@.*', str(dynamic_content), re.DOTALL) is not None:
                    dynamic_content = re.findall(r'(.*?)//@', dynamic_content, re.DOTALL)[0]
                if not self.is_lot_orig:
                    if BAPI.daily_choujiangxinxipanduan(dynamic_content):
                        if comment_count > 2000 or forward_count > 1000:  # 评论或转发超多的就算不是抽奖动态也要加进去凑个数
                            pass
                        else:
                            is_lot = False
                else:
                    is_lot = True
                official_lot_type = OfficialLotType.official_lot if is_official_lot else OfficialLotType.charge_lot if is_charge_lot else OfficialLotType.reserve_lot if is_reserve_lot else ''
                cur_dynamic = TLotdyninfo(dynId=dynamic_detail_dynamic_id,
                                          dynamicUrl=ret_url,
                                          authorName=author_name,
                                          up_uid=author_uid,
                                          pubTime=datetime.datetime.fromtimestamp(pub_ts),
                                          dynContent=dynamic_content,
                                          commentCount=comment_count,
                                          repostCount=forward_count,
                                          highlightWords=';'.join(high_lights_list),
                                          officialLotType=official_lot_type,
                                          officialLotId=str(lot_rid),
                                          isOfficialAccount=int(official_verify_type if official_verify_type else 0),
                                          isManualReply=manual_judge,
                                          isFollowed=int(bool(suffix)),
                                          isLot=int(is_lot),
                                          hashTag=premsg if premsg else '',
                                          dynLotRound_id=lotRound_id,
                                          rawJsonStr=rawJSON)
                await SqlHelper.addDynInfo(
                    cur_dynamic
                )

                try:
                    if is_official_lot or is_reserve_lot or is_charge_lot:
                        await self._solve_official_lot_data(str(dynamic_detail_dynamic_id), official_lot_type, lot_rid)
                except Exception as e:
                    get_others_lot_log.exception(f'上传官方抽奖失败！{e}')
                if dynamic_detail['orig_dynamic_id']:
                    # 'orig_dynamic_id': orig_dynamic_id,
                    # 'orig_mid': orig_mid,
                    # 'orig_name': orig_name,
                    # 'orig_pub_ts': orig_pub_ts,
                    # 'orig_official_verify': orig_official_verify,
                    # 'orig_comment_count': orig_comment_count,
                    # 'orig_forward_count': orig_forward_count,
                    # 'orig_like_count': orig_like_count,
                    # 'orig_dynamic_content': orig_dynamic_content,
                    # 'orig_relation': orig_relation,
                    # 'orig_desc': orig_desc
                    orig_dynamic_id = dynamic_detail['orig_dynamic_id']
                    orig_name = dynamic_detail['orig_name']
                    orig_pub_ts = dynamic_detail['orig_pub_ts']
                    orig_dynamic_content = dynamic_detail['orig_dynamic_content']
                    orig_comment_count = dynamic_detail['orig_comment_count']
                    orig_forward_count = dynamic_detail['orig_forward_count']
                    orig_official_verify = dynamic_detail['orig_official_verify']
                    dynamic_orig = dynamic_detail['dynamic_orig']
                    orig_ret_url = f'https://t.bilibili.com/{orig_dynamic_id}'
                    if 'tab=2' in ret_url:
                        orig_ret_url += '?tab=2'
                    elif BAPI.zhuanfapanduan(orig_dynamic_content):
                        orig_ret_url += '?tab=2'
                    orig_dynamic = TLotdyninfo(
                        dynId=orig_dynamic_id,
                        dynamicUrl=orig_ret_url,
                        authorName=orig_name,
                        up_uid=author_uid,
                        pubTime=datetime.datetime.fromtimestamp(orig_pub_ts),
                        dynContent=orig_dynamic_content,
                        commentCount=orig_comment_count,
                        repostCount=orig_forward_count,
                        highlightWords=';'.join(high_lights_list),
                        officialLotType=OfficialLotType.lot_dyn_origin_dyn,
                        officialLotId=None,
                        isOfficialAccount=orig_official_verify if type(orig_official_verify) is int else 0,
                        isManualReply=manual_judge,
                        isFollowed=int(bool(suffix)),
                        isLot=int(is_lot),
                        hashTag=premsg if premsg else '',
                        dynLotRound_id=lotRound_id,
                        rawJsonStr=dynamic_orig
                    )
                    await SqlHelper.addDynInfo(
                        orig_dynamic
                    )
                if is_lot:
                    if dynamic_detail.get('module_dynamic'):
                        if dynamic_detail.get('module_dynamic').get('additional'):
                            if dynamic_detail.get('module_dynamic').get('additional').get(
                                    'type') == 'ADDITIONAL_TYPE_UGC':
                                ugc = dynamic_detail.get('module_dynamic').get('additional').get('ugc')
                                aid_str = ugc.get('id_str')
                                if aid_str:
                                    aid_dynamic_item = BiliDynamicItem(
                                        dynamic_rid=aid_str,
                                        dynamic_type=8,
                                        is_lot_orig=True,
                                        is_use_available_proxy=self.is_use_available_proxy
                                    )
                                    await aid_dynamic_item.judge_lottery(high_lights_list, lotRound_id)
                                    attached_card = aid_dynamic_item.bili_judge_lottery_result.cur_dynamic if aid_dynamic_item.bili_judge_lottery_result else None
                                else:
                                    get_others_lot_log.critical(f'动态没有附加id_str\n{dynamic_detail}')
            else:
                get_others_lot_log.info(f'失效动态：https://t.bilibili.com/{self.dynamic_id}')
                cur_dynamic = TLotdyninfo(
                    dynId=str(self.dynamic_id) if self.dynamic_id else 0,
                    dynamicUrl=f'https://t.bilibili.com/{self.dynamic_id}',
                    authorName='',
                    up_uid=-1,
                    pubTime=datetime.datetime.fromtimestamp(86400),
                    dynContent='',
                    commentCount=-1,
                    repostCount=-1,
                    highlightWords='',
                    officialLotType='',
                    officialLotId=None,
                    isOfficialAccount=-1,
                    isManualReply='',
                    isFollowed=-1,
                    isLot=-1,
                    hashTag='',
                    dynLotRound_id=lotRound_id,
                    rawJsonStr=dynamic_detail.get('rawJSON')
                )
                await SqlHelper.addDynInfo(
                    cur_dynamic
                )
        except Exception as e:
            get_others_lot_log.exception(f'解析动态失败！！！{e}\n{dynamic_detail}')
            await asyncio.sleep(30)
            return await self.judge_lottery(highlight_word_list, lotRound_id)
        judge_result = BiliDynamicItemJudgeLotteryResult(
            cur_dynamic=cur_dynamic,
            orig_dynamic=orig_dynamic,
            attached_card=attached_card,
        )
        self.bili_judge_lottery_result = judge_result
        return judge_result


@dataclass
class BiliSpaceUserItem:
    """
    B站用户的空间
    """
    lot_round_id: int
    uid: int | str
    offset: int | str | None = 0
    lot_user_info: TLotuserinfo | None = field(default=None)  # 用户信息
    dynamic_infos: Set[BiliDynamicItem] = field(default_factory=set)  # 存放用户的空间动态详情
    pub_lot_users: Set['BiliSpaceUserItem'] = field(
        default_factory=set)  # 存放用户发布抽奖的用户详情，调用solve_space_dynamic的时候需要将isPubLotUser设置为True
    updateNum: int = field(default=0)
    is_use_available_proxy: bool = field(default=_is_use_available_proxy)

    def __hash__(self):
        return hash(int(self.uid))

    async def get_user_space_dynamic_id(
            self,
            secondRound=False,
            isPubLotUser=False,
            isPreviousRoundFinished=False,
            SpareTime=5 * 86400,
            succ_counter: ProgressCounter | None = None
    ) -> None:
        """
        支持了断点续爬
        根据时间和获取过的动态来判断是否结束爬取别人的空间主页
        :return:
        """

        def get_space_dynamic_time(space_req_dict: dict) -> list[int]:  # 返回list
            cards_json = space_req_dict.get('data').get('items')
            dynamic_time_list = []
            if cards_json:
                for card_dict in cards_json:
                    dynamic_time = card_dict.get('modules').get('module_author').get('pub_ts')
                    dynamic_time_list.append(dynamic_time)
            return dynamic_time_list

        n = 0
        first_get_dynamic_flag = True
        origin_offset = 0  # 初始offset
        lot_user_info: TLotuserinfo | None = await SqlHelper.getLotUserInfoByUid(self.uid)
        first_dynamic_id = 0
        self.offset = lot_user_info.offset if lot_user_info else 0
        # region 这部分是主要逻辑，包括断点续爬，需要注意逻辑是否正确
        if secondRound:
            newest_space_offset = await SqlHelper.getNewestSpaceDynInfoByUid(self.uid)
            if newest_space_offset:
                dynamic_calculated_ts = dynamic_id_2_ts(newest_space_offset)
                if int(time.time() - dynamic_calculated_ts) < 2 * 3600:
                    get_others_lot_log.info(
                        f'\n{self.uid}\nhttps://t.bilibili.com/{newest_space_offset} 距离上次获取抽奖时间（{datetime.datetime.fromtimestamp(dynamic_calculated_ts)}）不足2小时，跳过')
                    return
        if lot_user_info:
            # 只有当第二轮也获取完的时候，才会将latestFinishedOffset设置为最新的一条动态id值
            if not lot_user_info.isUserSpaceFinished and not isPreviousRoundFinished:  # 如果上一轮也没有完成，同时这个用户的空间没获取完，从上次的offset继续获取下去
                origin_offset = lot_user_info.offset
            elif lot_user_info.isUserSpaceFinished and not isPreviousRoundFinished:  # 如果上一轮抽奖没有完成，重新开始了，但是这个用户的空间获取完了，查询数据库，获取当前round_id的最小值 最多多获取到上一轮的全部数据
                origin_offset = await SqlHelper.getOldestSpaceOffsetByUidRoundId(
                    self.uid,
                    self.lot_round_id
                )
            else:  # lot_user_info.isUserSpaceFinished and isPreviousRoundFinished
                # 如果上一轮抽奖已经完成，并且这个用户的空间获取完了，那么就从0开始重新获取
                origin_offset = 0
            # 不会存在上一轮获取完了，但是用户没获取完的情况！！！不用讨论
        else:
            lot_user_info = TLotuserinfo(
                uid=self.uid,
                isPubLotUser=isPubLotUser,
                isUserSpaceFinished=0,
                offset=0,
                latestFinishedOffset=0
            )
        await SqlHelper.addLotUserInfo(lot_user_info)
        # endregion
        self.lot_user_info = lot_user_info
        cur_offset = deepcopy(origin_offset)
        uname = ''
        time_list = [0]
        get_others_lot_log.info(
            f'当前UID：https://space.bilibili.com/{self.uid}/dynamic'
            f'\t初始offseet:{origin_offset}\t是否为第二轮获取动态：{secondRound}')
        while 1:
            if succ_counter:
                succ_counter.update_ts = int(time.time())
            if origin_offset != 0 and first_get_dynamic_flag and not secondRound:  # 从半当中开始接着获取动态
                items = await SqlHelper.getSpaceRespTillOffset(self.uid, origin_offset)
                dyreq_dict = {
                    'code': 0,
                    'data': {
                        'has_more': True,
                        'items': items,
                        'offset': origin_offset,
                        "update_baseline": "",
                        'update_num': 0
                    },
                    'message': '0',
                    'ttl': 1
                }
                get_others_lot_log.info(
                    f'当前UID：https://space.bilibili.com/{self.uid}/dynamic\n从半当中开始接着获取动态，获取到时间在{origin_offset}之后的动态，共计{len(items)}条，之后沿着该offset继续从B站接口获取空间动态')
                first_get_dynamic_flag = False
            else:
                start_ts = time.time()
                get_others_lot_log.debug(f'正在前往获取用户【{self.uid}】空间动态请求！')
                dyreq_dict = await asyncio.create_task(get_space_dynamic_req_with_proxy(
                    self.uid,
                    cur_offset if cur_offset else "",
                    is_use_available_proxy=self.is_use_available_proxy
                ))
                code = dyreq_dict.get('code')
                msg = dyreq_dict.get('message')
                if code != 0:
                    get_others_lot_log.critical(
                        f'获取用户【{self.uid}】offset:{cur_offset} 空间动态请求失败！\n{dyreq_dict}')
                    await asyncio.to_thread(
                        pushme,
                        'get_others_lot_dyn',
                        f'获取用户【{self.uid}】offset:{cur_offset} 空间动态请求失败！\n{dyreq_dict}',
                        'text'
                    )
                    if code == 4101129:
                        get_others_lot_log.critical(
                            f'用户【{self.uid}】空间动态请求失败！\n{msg}')
                        await asyncio.sleep(3)
                        continue
                get_others_lot_log.info(
                    f'获取用户【{self.uid}】空间动态请求成功！耗时：{time.time() - start_ts}秒\n响应：\n{dyreq_dict}')
                resp_dyn_ids = await self.__add_space_card_to_db(dyreq_dict)
                if not first_dynamic_id and resp_dyn_ids:
                    first_dynamic_id = resp_dyn_ids[0]
            try:
                dynamic_items: list[dict] = dyreq_dict.get('data').get('items')
                if dynamic_items:
                    uname = dynamic_items[0].get('modules').get('module_author').get('name')
            except Exception as e:
                get_others_lot_log.error(f'获取空间动态用户名失败！{dyreq_dict}')
                get_others_lot_log.exception(e)
            try:
                repost_dynamic_id_list = await self._solve_space_dynamic(
                    dyreq_dict,
                    isPubLotUser
                )  # 脚本们转发生成的动态id 同时将需要获取的抽奖发布者的uid记录下来
            except Exception as e:
                get_others_lot_log.critical(f'解析空间动态失败！\n{e}\n{self.uid} {cur_offset}')
                get_others_lot_log.exception(e)
                continue
            if not repost_dynamic_id_list:
                get_others_lot_log.info(f'{self.uid}空间动态数量为0!{repost_dynamic_id_list}')
                break
            n += len(repost_dynamic_id_list)
            if dyreq_dict.get('data').get('offset') is not None:
                offset_str = dyreq_dict.get('data').get('offset')
                cur_offset = int(offset_str if offset_str else "0")
            else:
                get_others_lot_log.critical(f'获取用户【{self.uid}】offset:{cur_offset} 空间动态请求失败！\n{dyreq_dict}')
                await asyncio.to_thread(
                    pushme,
                    'get_others_lot_dyn',
                    f'获取用户【{self.uid}】offset:{cur_offset} 空间动态请求失败！\n{dyreq_dict}',
                    'text'
                )
                break
            self.offset = cur_offset
            time_list = get_space_dynamic_time(dyreq_dict)
            if not secondRound:  # 第二轮获取动态，不更新数据库
                lot_user_info = TLotuserinfo(
                    uid=self.uid,
                    uname=uname,
                    updateNum=self.updateNum,
                    updatetime=lot_user_info.updatetime,  # 只有最后完成了才会更新`updatetime`
                    isUserSpaceFinished=0,
                    offset=cur_offset,
                    latestFinishedOffset=lot_user_info.latestFinishedOffset,
                    isPubLotUser=isPubLotUser
                )
                await SqlHelper.addLotUserInfo(
                    lot_user_info
                )
            self.lot_user_info = lot_user_info
            if len(time_list) == 0:
                get_others_lot_log.error(f'timelist is empty\t{json.dumps(dyreq_dict)}')
                break
            if time.time() - time_list[-1] >= SpareTime:
                get_others_lot_log.info(
                    f'超时动态，当前UID：https://space.bilibili.com/{self.uid}/dynamic\t获取结束\t{BAPI.timeshift(time.time())}')
                # await asyncio.sleep(60)
                break
            if cur_offset and cur_offset <= lot_user_info.latestFinishedOffset:
                get_others_lot_log.info(
                    f'遇到获取过的动态offset，当前UID：https://space.bilibili.com/{self.uid}/dynamic\t获取结束\t'
                    f'cur_offset:{cur_offset}\n'
                    f'latestFinishedOffset:{lot_user_info.latestFinishedOffset}'
                )
                break
            try:
                if not dyreq_dict.get('data').get('has_more'):
                    get_others_lot_log.info(f'当前用户 https://space.bilibili.com/{self.uid}/dynamic 无更多动态')
                    break
            except Exception as e:
                get_others_lot_log.critical(f'Error: has_more获取失败\n{dyreq_dict}\n{e}')
                get_others_lot_log.exception(e)
        get_others_lot_log.debug(f'更新lot_user_info')
        await SqlHelper.addLotUserInfo(TLotuserinfo(
            # 第二轮获取完了才接着更新数据库，这样下次获取的时候，不论是从中间开始还是重新起一轮，都不会收到第二轮的数据的影响
            uid=self.uid,
            uname=uname,
            updateNum=self.updateNum,
            updatetime=datetime.datetime.now(),
            isUserSpaceFinished=1,
            offset=cur_offset,
            latestFinishedOffset=first_dynamic_id if first_dynamic_id else lot_user_info.latestFinishedOffset,
            isPubLotUser=isPubLotUser
        ))
        if not secondRound:
            get_others_lot_log.debug(f'更新lot_user_info最终状态')
            await asyncio.create_task(self.get_user_space_dynamic_id(
                secondRound=True,
                isPubLotUser=isPubLotUser,
                isPreviousRoundFinished=isPreviousRoundFinished,
                SpareTime=SpareTime,
                succ_counter=succ_counter
            ))
        if n <= 50 and time.time() - time_list[-1] >= SpareTime and secondRound == False and not isPubLotUser:
            get_others_lot_log.critical(
                f'{self.uid}\t当前UID获取到的动态太少，前往：\nhttps://space.bilibili.com/{self.uid}\n查看详情')
        get_others_lot_log.debug(f'{self.uid}空间动态获取完毕！')

    async def __add_space_card_to_db(self, spaceResp: dict) -> List[int | str] | None:
        try:
            spaceResp['data']['items'] = [i for i in spaceResp.get('data').get('items') if
                                          i.get('modules', {}).get('module_tag', {}).get('text') != '置顶']
            ret_list = []
            if spaceResp.get('data') and spaceResp.get('data').get('items'):
                for i in spaceResp.get('data').get('items'):
                    space_resp_card_dynamic_id = i.get('id_str')
                    await SqlHelper.addSpaceResp(LotUserSpaceResp=TLotuserspaceresp(
                        spaceUid=self.uid,
                        spaceOffset=space_resp_card_dynamic_id,
                        spaceRespJson=i,
                        dynLotRound_id=self.lot_round_id
                    ))
                    ret_list.append(space_resp_card_dynamic_id)
            return ret_list
        except Exception as _e:
            get_others_lot_log.critical(f'添加空间动态响应至数据库失败！{spaceResp}\n{_e}')
            get_others_lot_log.exception(_e)

    def _add_pub_lot_user(self, uid):
        for i in self.pub_lot_users:  # O(n)复杂度
            if str(i.uid) == str(uid):
                return
        self.pub_lot_users.add(BiliSpaceUserItem(
            uid=str(uid),
            lot_round_id=self.lot_round_id
        ))

    async def _solve_space_dynamic(self, space_req_dict: dict, isPubLotUser: bool) -> List[BiliDynamicItem] | None:
        """
        脚本们转发生成的动态id 同时将需要获取的抽奖发布者的uid记录下来
        :param isPubLotUser:发布抽奖动态的up
        :param space_req_dict:
        :return:
        """
        ret_list = []
        try:
            for dynamic_item in space_req_dict.get('data').get('items'):
                self.updateNum += 1
                dynamic_id_str = str(dynamic_item.get('id_str'))
                ret_list.append(dynamic_id_str)
                if isPubLotUser:  # 只有是发布抽奖动态的up才会将他的动态信息加入抽奖动态列表里面
                    single_dynamic_resp = {
                        'code': 0,
                        'data':
                            {
                                "item": dynamic_item
                            }
                    }
                    bili_dynamic_item = BiliDynamicItem(
                        dynamic_id=dynamic_id_str,
                        dynamic_raw_resp=single_dynamic_resp,
                        is_use_available_proxy=self.is_use_available_proxy
                    )
                    if isPubLotUser:  # 只添加发布抽奖动态的人的原始动态，如果是转发抽奖的抽奖号，那么他的转发抽奖的转发动态是不需要加入检查动态set的
                        self.dynamic_infos.add(bili_dynamic_item)
                else:
                    if dynamic_item.get('type') == 'DYNAMIC_TYPE_FORWARD':
                        orig_dynamic_item = dynamic_item.get('orig', {})
                        orig_dynamic_id_str = orig_dynamic_item.get('id_str')
                        orig_single_dynamic_resp = {
                            'code': 0,
                            'data':
                                {
                                    "item": orig_dynamic_item
                                }
                        }
                        if orig_dynamic_id_str and orig_dynamic_item.get('type') != 'DYNAMIC_TYPE_NONE':
                            orig_bili_dynamic_item = BiliDynamicItem(
                                dynamic_id=orig_dynamic_id_str,
                                dynamic_raw_resp=orig_single_dynamic_resp,
                                is_use_available_proxy=self.is_use_available_proxy
                            )
                            self.dynamic_infos.add(orig_bili_dynamic_item)
                        else:
                            if orig_dynamic_item and orig_dynamic_item.get('type') != 'DYNAMIC_TYPE_NONE':
                                get_others_lot_log.critical(f'遇到转发动态，但是没有找到原始动态！\n{dynamic_item}')
                        module_dynamic = dynamic_item.get('modules').get('module_dynamic')
                        rich_text_nodes = module_dynamic.get('desc').get('rich_text_nodes')
                        dynamic_text = module_dynamic.get('desc').get('text')
                        at_users_nodes = list(
                            filter(lambda x: x.get('type') == 'RICH_TEXT_NODE_TYPE_AT', rich_text_nodes))
                        need_at_usernames = re.findall('//@(.{0,20}):', dynamic_text)
                        for need_at_username in need_at_usernames:
                            for i in at_users_nodes:
                                if need_at_username in i.get('text'):
                                    need_uid = i.get('rid')
                                    self._add_pub_lot_user(need_uid)
            if space_req_dict.get('data').get('inplace_fold'):
                for i in space_req_dict.get('data').get('inplace_fold'):
                    if i.get('dynamic_ids'):
                        for dyn_id in i.get('dynamic_ids'):
                            ret_list.append(dyn_id)
                    get_others_lot_log.critical(f'遇到折叠内容！inplace_fold:{i}')
            if not space_req_dict.get('data').get('has_more') and len(ret_list) == 0:
                return None
            return ret_list
        except Exception as _e:
            get_others_lot_log.exception(_e)
            raise _e


class GetOthersLotDynRobot:
    """
    获取其他人的抽奖动态
    """

    def __init__(self):
        self.isPreviousRoundFinished = False  # 上一轮抽奖是否结束
        self.nowRound: TLotmaininfo = TLotmaininfo()
        self.username = ''
        self.nonLotteryWords = ['分享视频', '分享动态']
        self.SpareTime = 86400 * 5  # 多少时间以前的就不获取别人的动态了
        self.highlight_word_list = HighlightWordList
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
        tasks = set()
        for i in bili_space_user_items:
            task = asyncio.create_task(
                self.__do_space_task(i, isPubLotUser),
                name=f'{i.uid}'
            )
            tasks.add(task)
            task.add_done_callback(tasks.discard)
        await asyncio_gather(*tasks, log=get_others_lot_log)
        get_others_lot_log.info(f'{len(bili_space_user_items)}个空间获取完成')
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
            get_others_lot_log.critical(f'当前获取别人抽奖轮次：{sqlalchemy_model_2_dict(latest_round)}')
            await SqlHelper.addLotMainInfo(latest_round)

        async def init_bili_space_user():
            if redis_data := await get_other_lot_redis_manager.get_target_uid_list():
                self.bili_space_user_items_set.update(
                    [BiliSpaceUserItem(uid=x, lot_round_id=self.nowRound.lotRound_id) for x in redis_data]
                )
            else:
                get_others_lot_log.critical('获取b站抽奖用户列表失败，使用默认列表！')
                default_list = [319857159,
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
                                7538278
                                ]
                self.bili_space_user_items_set.update(
                    [BiliSpaceUserItem(uid=x, lot_round_id=self.nowRound.lotRound_id) for x in default_list])

        await init_round()
        await init_bili_space_user()
        get_others_lot_log.info('初始化完成！')

    async def __judge_dynamic(self,
                              item: BiliDynamicItem,
                              highlight_word_list: List[str],
                              lotRound_id: int,
                              queue: asyncio.Queue
                              ):
        """
        判断抽奖
        :param item:
        :param highlight_word_list:
        :param lotRound_id:
        :return:
        """
        queue.get_nowait()
        self.dyn_succ_counter.running_params.add(self.__hash__())
        await item.judge_lottery(highlight_word_list=highlight_word_list, lotRound_id=lotRound_id)
        self.dyn_succ_counter.running_params.discard(self.__hash__())
        self.dyn_succ_counter.succ_count += 1
        return

    async def main(self):
        await self.__init()
        await self.get_all_space_dyn_id(self.bili_space_user_items_set, isPubLotUser=False)  # 获取抽奖号的空间
        pub_lot_uid_set: Set[BiliSpaceUserItem] = set()
        for x in self.bili_space_user_items_set:
            pub_lot_uid_set.update(x.pub_lot_users)
        get_others_lot_log.critical(f'总共要获取{len(pub_lot_uid_set)}个发起抽奖用户的空间！')
        await self.get_all_space_dyn_id(pub_lot_uid_set, isPubLotUser=True)  # 获取那些发起抽奖的人的空间
        total_lot_uid_set: Set[BiliSpaceUserItem] = set()
        total_lot_uid_set.update(self.bili_space_user_items_set)
        total_lot_uid_set.update(pub_lot_uid_set)
        get_others_lot_log.critical(f'总共获取了{len(pub_lot_uid_set)}个发起抽奖用户的空间！')
        for x in total_lot_uid_set:
            self.goto_check_dynamic_item_set.update(x.dynamic_infos)
            for y in x.pub_lot_users:
                self.goto_check_dynamic_item_set.update(y.dynamic_infos)

        get_others_lot_log.critical(f'{len(self.goto_check_dynamic_item_set)}条待检查动态')
        self.dyn_succ_counter.total_num = len(self.goto_check_dynamic_item_set)
        tasks = set()
        queue = asyncio.Queue(50)
        for x in self.goto_check_dynamic_item_set:
            await queue.put(1)
            task = asyncio.create_task(
                self.__judge_dynamic(x, self.highlight_word_list, self.nowRound.lotRound_id, queue=queue),
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
    async def get_new_dyn(self) -> list[str]:
        """
        主函数，获取一般最新的抽奖
        :return:
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
        get_others_lot_log.error(f'上次获取别人B站动态空间抽奖时间：{datetime.datetime.fromtimestamp(self.get_dyn_ts)}')
        if int(time.time()) - self.get_dyn_ts >= 1.5 * 24 * 3600:  # 每隔1.5天获取一次
            self.robot = None
            self.robot = GetOthersLotDynRobot()
            await self.robot.main()
            await get_other_lot_redis_manager.set_get_dyn_ts(int(time.time()))
        self.is_getting_dyn_flag = False
        return await self.solve_return_lot()

    async def get_official_lot_dyn(self) -> list[str]:
        """
        返回官方抽奖信息，结尾是tab=1
        :return:
        """
        recent_official_lot_data: Sequence[Lotdata] = await grpc_sql_helper.query_official_lottery_by_timelimit(
            time_limit=30 * 24 * 3600,
            order_by_ts_desc=False
        )
        is_lot_list = await asyncio.to_thread(big_reserve_predict,
                                              [' '.join(
                                                  [x.first_prize_cmt, x.second_prize_cmt if x.second_prize_cmt else '',
                                                   x.third_prize_cmt if x.third_prize_cmt else '']) for x
                                                  in recent_official_lot_data])
        ret_list = []
        for i in range(len(recent_official_lot_data)):
            if is_lot_list[i] == 1:
                if recent_official_lot_data[i].lottery_time - int(time.time()) < 2 * 3600 * 24:  # 忽略两天以内的
                    continue
                ret_list.append(f'https://t.bilibili.com/{recent_official_lot_data[i].business_id}?tab=1')
        if ret_list:
            await asyncio.to_thread(
                pushme,
                f"必抽的官方抽奖【{len(ret_list)}】条", '\n'.join(ret_list),
                'text'
            )
        return ret_list

    async def get_unignore_Big_lot_dyn(self, time_limit: int = GET_LOT_DYN_TIME_LIMIT) -> list[str]:
        """
        获取必抽的大奖
        :return:
        """
        all_lot = await SqlHelper.getAllLotDynByTimeLimit()
        all_lot = [x for x in all_lot if self.__is_need_lot(x)]
        dyn_content_list = [x.dynContent for x in all_lot]
        is_lot_list = await asyncio.to_thread(big_lot_predict, dyn_content_list)
        ret_list = []
        for i in range(len(all_lot)):
            if is_lot_list[i] == 1:
                ret_list.append(all_lot[i].dynamicUrl)
        if ret_list:
            await asyncio.to_thread(
                pushme,
                f"必抽的大奖【{len(ret_list)}】条", '\n'.join(ret_list),
                'text'
            )
        return ret_list

    async def get_unignore_reserve_lot_space(self) -> list[TUpReserveRelationInfo]:
        all_lots = await mysq.get_all_available_reserve_lotterys()
        recent_lots: list[TUpReserveRelationInfo] = [x for x in all_lots if
                                                     x.etime and x.etime - int(time.time()) < 2 * 3600 * 24]
        reserve_infos: list[str] = [x.text for x in recent_lots]
        is_lot_list = await asyncio.to_thread(big_reserve_predict, reserve_infos)
        ret_list = []
        ret_info_list = []
        for i in range(len(recent_lots)):
            if is_lot_list[i] == 1:
                ret_info_list.append(
                    ' '.join([f'https://space.bilibili.com/{recent_lots[i].upmid}/dynamic', recent_lots[i].text]))
                ret_list.append(recent_lots[i])
        if ret_info_list:
            await asyncio.to_thread(
                pushme,
                f"必抽的预约抽奖【{len(ret_info_list)}】条", '\n'.join(ret_info_list),
                'text'
            )
        return ret_list

    # endregion

    # region 推送抽奖用的函数
    def push_lot_csv(self, title: str, content_list: list[TLotdyninfo]):
        """
        推送抽奖信息到手机
        :param title:
        :param content_list:
        :return:
        """
        tabletitile = '|动态链接<br>up昵称&#124;账号类型<br>发布时间<br>评论数&#124;转发数|动态内容|\n'

        content = tabletitile + '|:---:|---|\n'

        # tabletitile = '<tr><th colspan="2">动态链接<br>昵称|账号类型<br>发布时间<br>评论数|转发数</th><th>动态内容</th></tr>'
        # content = '\n<table align="center" width="400" cellspacing="0" border="1">' + tabletitile
        for i in content_list:
            dynurl = i.dynamicUrl
            nickname = i.authorName
            official_verify = i.isOfficialAccount
            pubtime = i.pubTime
            dyncontent = i.dynContent.replace('\r', '').replace('|', '&#124;').replace('\n', '<br>').replace('&',
                                                                                                             '&amp;')
            comment_count = i.commentCount
            rep_count = i.repostCount
            content += f"|{dynurl} <br></br>{nickname}&#124;{official_verify}<br></br>{pubtime}<br></br>{comment_count}&#124;{rep_count}|{dyncontent}|\n"
            # content += f"""<tr><td colspan="2">{dynurl}</td><td rowspan="4">{dyncontent}</td></tr><tr><td>{nickname}</td><td>{official_verify}</td></tr><tr><td colspan="2">{pubtime}</td></tr><tr><td>{comment_count}</td><td>{rep_count}</td></tr>"""
        # content += '</table>'

        try:
            resp = pushme(title, content, 'markdata')
            get_others_lot_log.debug(resp.text)
        except Exception as e:
            get_others_lot_log.error(f'推送至pushme失败！\n{e}')

    # endregion

    # region 获取抽奖csv里的数据
    def __is_need_lot(self, lot_det: TLotdyninfo):
        """
        过滤抽奖函数，只保留一般抽奖 最长大概是判断20天
        :param lot_det:
        :return:
        """
        if lot_det.pubTime.year < 2000:
            return False
        pub_ts = int(lot_det.pubTime.timestamp())
        official_verify = lot_det.isOfficialAccount
        lot_type = lot_det.officialLotType
        comment_count = lot_det.commentCount
        rep_count = lot_det.repostCount
        if lot_type == OfficialLotType.lot_dyn_origin_dyn.value:
            if int(time.time()) - pub_ts >= 20 * 24 * 3600:  # 抽奖动态的源动态放宽到20天
                return False
            return True
        if lot_type in [OfficialLotType.charge_lot.value, OfficialLotType.reserve_lot.value,
                        OfficialLotType.official_lot.value]:
            return False
        if int(self.get_dyn_ts - pub_ts) <= 2 * 3600:  # 获取时间和发布时间间隔小于2小时的不按照评论转发数量过滤
            return True
        if comment_count is not None and comment_count > 0:
            if int(comment_count) < 20 and int(rep_count) < 20:
                return False
        if official_verify != 1:
            if int(time.time()) - pub_ts >= 10 * 24 * 3600:  # 超过10天的不抽
                return False
        else:
            if int(time.time()) - pub_ts >= 15 * 24 * 3600:  # 官方号放宽到15天
                return False
        return True

    async def solve_return_lot(self, time_limit: int = GET_LOT_DYN_TIME_LIMIT) -> list[str]:
        """
        解析并过滤抽奖的csv，直接返回动态链接的列表
        :return:
        """
        all_lot_det = await SqlHelper.getAllLotDynByTimeLimit(time_limit)
        filtered_list: list[TLotdyninfo] = list(filter(self.__is_need_lot, all_lot_det))
        filtered_list.sort(key=lambda x: x.dynId, reverse=True)
        self.push_lot_csv(
            f"一般动态抽奖信息【{len(filtered_list)}】条",
            filtered_list
        )
        get_others_lot_log.critical(f'一般动态抽奖信息【{len(filtered_list)}】条')
        ret_list = [str(x.dynId) for x in filtered_list]
        if ret_list:
            await asyncio.to_thread(
                pushme,
                f"一般动态抽奖信息【{len(filtered_list)}】条", '\n'.join(ret_list),
                'text'
            )
        return ret_list

    # endregion


get_others_lot_dyn = GetOthersLotDyn()

if __name__ == '__main__':
    import aiomonitor


    async def main():
        loop = asyncio.get_running_loop()
        run_forever = loop.create_future()
        loop.create_task(get_others_lot_dyn.get_new_dyn())
        with aiomonitor.start_monitor(loop):
            await run_forever


    asyncio.run(main())
