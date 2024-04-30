# coding:utf-8
import sys

import asyncio
import datetime
import json
import os
import pandas
import random
import re
import urllib.parse
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Union
import execjs
from loguru import logger
from CONFIG import CONFIG
from github.my_operator.get_others_lot.Tool.newSqlHelper.models import TLotuserspaceresp, TLotdyninfo, TLotuserinfo, \
    TLotmaininfo
from opus新版官方抽奖.预约抽奖.db.models import TUpReserveRelationInfo
from utl.pushme.pushme import pushme
from utl.代理.request_with_proxy import request_with_proxy
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import Bilibili_methods.all_methods
from github.my_operator.get_others_lot.Tool.newSqlHelper.SqlHelper import SqlHelper
from github.my_operator.get_others_lot.svmJudgeBigLot.judgeBigLot import big_lot_predict
from github.my_operator.get_others_lot.svmJudgeBigReserve.judgeReserveLot import big_reserve_predict
from utl.加密.wbi加密 import gen_dm_args, get_wbi_params

root_dir = CONFIG.root_dir
relative_dir = 'github/my_operator/get_others_lot/'  # 执行文件所在的相对路径
request_proxy = request_with_proxy()
get_others_lot_log = logger.bind(user='get_others_lot')
# get_others_lot_log.add(sys.stderr, level="DEBUG",
#                        filter=lambda record: record["extra"].get('user') == "get_others_lot")


@dataclass
class user_space_dyn_detail:
    """
    描述获取的b站用户的动态
    """
    latest_dyid_list: list = field(default_factory=list)
    update_num: int = 0


@dataclass
class pub_lot_user_info:
    """
    描述发布动态的用户信息
    """
    uid: str = ''
    dynContent_list: list[str] = field(default_factory=list)

    def find_dyn_content(self, dyncontent: str) -> bool:
        """
        判断动态内容是否在动态列表中
        :param dyncontent:
        :return:
        """
        for i in self.dynContent_list:
            if dyncontent[:10] in i:
                return True
        return False


@dataclass
class scrapyData:
    queryUserInfo: Dict[
        str, user_space_dyn_detail] = field(default_factory=dict)
    gitee_dyn_id_list: list[str] = field(default_factory=list)  # str(dynid)
    uidlist: list[int] = field(default_factory=lambda: [
        # 100680137,#你的工具人老公
        # 323360539,#猪油仔123
        20958956,  # T_T欧萌
        # 970408,  # up主的颜粉
        # 24150189,#不适这样的
        # 275215223,#黑板小弟
        # 4380948,#玉瑢
        # 96948162,#究极貔貅
        # 365404611,#梦灵VtL
        # 672080,#喋血的爱丽丝
        # 587970586,#扬升平安夜
        # 239894183,#お帰り_Doctor
        # 47350939,#焰燃丶
        # 456414076,#为斯卡蒂献出心脏T_T
        # 442624804,#粉墨小兔兔
        # 295117380,#乘风破浪锦鲤小皇后
        # 672080,#喋血的爱丽丝
        # 1397970246,#六七爱十三k
        # 323198113,#⭐吃蓝莓的喵酱

        332793152,  # ⭐欧王本王
        87838475,  # *万事屋无痕
        646686238,  # 小欧太难了a
        386051299,  # 云散水消
        332793152,  # 仲夏凝秋
        1045135038,  # 神之忏悔王神
        381282283,  # 小尤怜
        279262754,  # 星空听虫鸣
        20343656,
        16101659,
        1183157743,
        31341142,
        6369160,
        106821863,
        1869690859,
        1824937075,
        6781805,
        4586734,
        90123009,
        71583520,
        490029339,
        5191526,
        22218483,  # 仰望陨听
        3493092200024392,
        41596583,
        1677356873,
        4586734,
        2365817,
        211553556,
        1234306704,
        319857159,
        14134177,
        1817853136,
        1741486871,
        266223923,
        646327721
    ])
    dyidList: list[str] = field(default_factory=list)  # 动态id
    lotidList: list[str] = field(default_factory=list)  # 抽奖id


class FileMap(str, Enum):
    _log_path = root_dir + relative_dir + 'log/'
    lot_dyid = _log_path + 'lot_dyid.txt'
    get_dyid = _log_path + 'get_dyid.txt'  # 最后写入文件记录
    uidlist_json = _log_path + 'uidlist.json'
    本轮检查的动态id = _log_path + '本轮检查的动态id.txt'
    所有抽奖信息 = _log_path + '所有过滤抽奖信息.csv'
    所有无用信息 = _log_path + '所有无用信息.csv'

    _result_path = root_dir + relative_dir + 'result/'
    过滤抽奖信息 = _result_path + '过滤抽奖信息.csv'
    无用信息 = _result_path + '无用信息.csv'

    获取过动态的b站用户 = root_dir + relative_dir + '获取过动态的b站用户.json'
    get_dyn_ts = root_dir + relative_dir + 'get_dyn_ts.txt'

    loguru日志 = _log_path + 'loguru日志.log'


class OfficialLotType(str, Enum):
    预约抽奖 = '预约抽奖'
    充电抽奖 = '充电抽奖'
    官方抽奖 = '官方抽奖'
    抽奖动态的源动态 = '抽奖动态的源动态'


def writeIntoFile(write_in_list: list[Any], filePath, write_mode='w', sep=','):
    try:
        if 'a' in write_mode:
            if not os.path.exists(filePath):
                write_mode = 'w'
        write_in_list = list(map(str, write_in_list))
        with open(filePath, write_mode, encoding='utf-8') as f:
            f.writelines(sep.join(write_in_list))
    except Exception as e:
        get_others_lot_log.critical(f'写入文件失败！\n{e}')


# get_others_lot_log.add(
#     sink=FileMap.loguru日志.value,
#     level="INFO",
#     filter=lambda x: 'ERROR' in str(x['level']).upper() or 'CRITICAL' in str(x['level']),
#     enqueue=True,
#     rotation="300 MB",
#     format="{time} | {level} | {message}",
#     encoding="utf-8",
#     backtrace=True,
#     diagnose=True,
#     compression="zip",
# )


class GetOthersLotDyn:
    """
    获取其他人的抽奖动态
    """

    def __init__(self):
        # 上一轮抽奖是否结束
        self.isPreviousRoundFinished = False
        self.sem = asyncio.Semaphore(10)
        self.space_sem = asyncio.Semaphore(10)
        self.nowRound: TLotmaininfo = TLotmaininfo()
        self.aid_list = []
        self.fake_cookie = True
        self.sqlHlper = SqlHelper()
        self.username = ''
        self.nonLotteryWords = ['分享视频', '分享动态']
        self.cookie3 = gl.get_value('cookie3')  # 斯卡蒂
        self.fullcookie3 = gl.get_value('fullcookie3')
        self.ua3 = gl.get_value('ua3')
        self.fingerprint3 = gl.get_value('fingerprint3')
        self.csrf3 = gl.get_value('csrf3')
        self.uid3 = gl.get_value('uid3')
        self.username3 = gl.get_value('uname3')
        self.all_followed_uid = []
        self.SpareTime = 86400 * 5  # 多少时间以前的就不获取别人的动态了
        self.manual_reply_judge = execjs.compile("""
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
        self.highlight_word_list = [
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
        self.spaceRecordedDynamicIdList = []
        self.BAPI = Bilibili_methods.all_methods.methods()

        self.queried_dynamic_id_list: list[str] = []  # 所有查询过的动态id
        self.lottery_dynamic_detail_list = []  # 动态详情，最后写入抽奖文件里的内容！
        self.useless_info = []

        self.queryingData = scrapyData()
        self.queriedData = scrapyData()
        self.create_dir()
        self.lock = asyncio.Lock()

        self.pub_lot_user_info_list: list[pub_lot_user_info] = []  # 获取发布抽奖动态的用户信息

    def calculate_pub_ts_by_dynamic_id(self, dynamic_id: str) -> int:
        return int((int(dynamic_id) + 6437415932101782528) / 4294939971.297)

    def create_dir(self):
        if not os.path.exists(FileMap._log_path):
            os.makedirs(FileMap._log_path)
        if not os.path.exists(FileMap._result_path):
            os.mkdir(FileMap._result_path)

    # region 获取gitee抽奖动态id
    def solveGiteeFileContent(self, file_content, allqueried_dynamnic_id) -> list[str]:
        """
        解析gitee获取的别人的抽奖动态id
        :param allqueried_dynamnic_id: 所有获取过的动态id
        :param file_content:
        :return:
        """

        def is_valid_date(_str):
            '''判断是否是一个有效的日期字符串'''
            try:
                time.strptime(_str, "%Y-%m-%d")
                return True
            except:
                try:
                    time.strptime(_str, "%m-%d-%Y")
                    return True
                except:
                    return False

        ret_list = []
        now_date = datetime.datetime.now()
        file_split = file_content.split(',')
        file_split.reverse()
        for i in file_split:
            if is_valid_date(i):
                try:
                    lottery_update_date = datetime.datetime.strptime(i, '%Y-%m-%d')
                except:
                    lottery_update_date = datetime.datetime.strptime(i, "%m-%d-%Y")
                if (now_date - lottery_update_date).days >= 4:  # 多少天前的跳过
                    get_others_lot_log.info(lottery_update_date)
                    break
            if i not in allqueried_dynamnic_id and i != '' and i != ' ' and str.isdigit(i):
                ret_list.append(i.strip())
        return ret_list

    def fetchGiteeInfo(self):
        os.system(f'cd "{root_dir}github/bili_upload" && git fetch --all && git reset --hard && git pull')

    # endregion

    # region 登录并获取关注数据
    def login_check(self, cookie, ua):
        return
        # headers = {
        #     'User-Agent': ua,
        #     'cookie': cookie
        # }
        # url = 'https://api.bilibili.com/x/web-interface/nav'
        # res = requests.get(url=url, headers=headers).json()
        # if res['data']['isLogin'] == True:
        #     name = res['data']['uname']
        #     self.username = name
        #     self.uid3 = res['data']['mid']
        #     get_others_lot_log.info('登录成功,当前账号用户名为%s uid:%s' % (name, str(self.uid3)))
        #     return 1
        # else:
        #     get_others_lot_log.info('登陆失败,请重新登录')
        #     sys.exit('登陆失败,请重新登录')

    def get_attention(self, mid, cookie, ua):
        return [
            508103429,
            86205301,
            360811001,
            653812,
            36882906,
            349077957,
            106017013,
            54671014,
            1323818,
            2305653,
            3546386257676482,
            3546579726239816,
            1025662408,
            3546603795253744,
            1942338550,
            1055874935,
            3546599072466985,
            3546569525692605,
            22353137,
            3494378731473306,
            1114967249,
            437277180,
            275163312,
            261113477,
            3546557873916902,
            3493280922732873,
            1909569,
            3405607,
            160450916,
            88741067,
            3546598900501279,
            491461718,
            400192152,
            267484788,
            3546390615559007,
            3493282386545566,
            1636034895,
            472729452,
            620667498,
            171818544,
            1317104224,
            321173469,
            626332915,
            1409863611,
            15810,
            297242063,
            32782335,
            8992943,
            9053928,
            3494360941333381,
            51886960,
            1005316503,
            285881562,
            11046926,
            254140017,
            1540567449,
            178362496,
            470806599,
            436175352,
            3494379073309365,
            1057051140,
            43855,
            22863497,
            337037191,
            3493281335872187,
            506761354,
            1224108408,
            516314798,
            396822361,
            8047632,
            2126081242,
            389712930,
            356798697,
            21096200,
            14762311,
            928123,
            18943826,
            3461576713570746,
            268035532,
            30928054,
            8048877,
            733871,
            438880209,
            125526,
            2026561407,
            3546608469805954,
            1460552010,
            3493108557809994,
            39627524,
            12355462,
            520152906,
            32708626,
            358703861,
            32660634,
            1442000,
            3493284731160723,
            16760873,
            1343321779,
            1197454103,
            381718532,
            521325931,
            17125638,
            619162217,
            403520147,
            1562750317,
            254031358,
            156619610,
            8969156,
            1631015691,
            32708726,
            3546563777399037,
            697654195,
            19001465,
            49631892,
            647409444,
            37090048,
            14232358,
            6131035,
            434334701,
            3493134189202377,
            1943410799,
            1436758643,
            450905062,
            3494376565115651,
            421267475,
            1420628859,
            323938301,
            2007250903,
            98627270,
            545424466,
            1746158065,
            3493265644980448,
            471284594,
            1988649931,
            3546599741458758,
            3461576967326521,
            1205794152,
            163637592,
            490023,
            501042852,
            3493131051862885,
            10899123,
            3461565349104457,
            3546569118845228,
            1121571225,
            348615390,
            16685211,
            2080323,
            487331757,
            6639802,
            2990100,
            33004908,
            264245565,
            34690710,
            1890519108,
            66556492,
            1703797642,
            471376624,
            3746384,
            75955887,
            3546597797398545,
            245833292,
            3493144066788118,
            412504829,
            3546631297305020,
            62487654,
            11417094,
            3546384728852917,
            1588417299,
            416515478,
            703007996,
            1129115529,
            283301853,
            343198,
            1786990706,
            690545051,
            143392930,
            3546599919716930,
            41007267,
            613345189,
            1276787,
            3218476,
            3546609591781698,
            3493290691267121,
            618107325,
            1353156303,
            1942864208,
            175686397,
            392380092,
            3546375291668881,
            8656648,
            440519389,
            3546624106171104,
            91287557,
            356701257,
            626795438,
            3494365156608185,
            688617128,
            384514636,
            343961277,
            3546561980139883,
            407373225,
            516026909,
            1554380563,
            494736442,
            3546379764893769,
            3546574258964484,
            1294678093,
            3546595553446156,
            3461573676894477,
            3461565583984850,
            3546389449542352,
            3546375279086021,
            3546610155915957,
            516324694,
            3537113974835320,
            107946270,
            100474924,
            1737547258,
            3546589689809274,
            3546615193274883,
            14617453,
            3546606416694144,
            1822237798,
            3546571564124310,
            373086508,
            577730079,
            383587023,
            1192652620,
            3546628250143324,
            214871639,
            293627423,
            7847261,
            475154530,
            1163073259,
            3546605940640278,
            400798813,
            3546610883627909,
            1513826630,
            3493142120631012,
            3493104367700577,
            678884946,
            3546617523210497,
            35432481,
            3546609826663112,
            3537108906019651,
            24924450,
            354376649,
            15252895,
            3493087705827505,
            1738710719,
            1992687971,
            562197,
            3537112682989619,
            3546563796273842,
            36800662,
            34646754,
            443348418,
            23796550,
            15680186,
            65900190,
            3546600276232382,
            1502815111,
            3493135961295379,
            3546573438978521,
            26350092,
            37399681,
            73857541,
            105505,
            262556896,
            381218218,
            1131201421,
            415094177,
            16018969,
            30502823,
            438550870,
            131918955,
            3546600957807502,
            14266048,
            258786,
            26867299,
            1814756990,
            3546625297353356,
            1978636705,
            1085234961,
            1748512975,
            330359689,
            14481654,
            2200736,
            19193,
            436089892,
            455417154,
            485548414,
            283827671,
            1508339769,
            1836714320,
            3493122384333125,
            3546604204198677,
            3493081957534067,
            38731397,
            22976912,
            3546607798717004,
            43983742,
            3493124712172000,
            3493298639472884,
            3546602375482217,
            3537117477079233,
            434476793,
            1493793977,
            326229399,
            1166586460,
            22649032,
            3493293352553103,
            1889312221,
            308459,
            3461569182698067,
            2138602891,
            3461568597592093,
            434056774,
            1217754423,
            256468152,
            1950721001,
            96639395,
            306839302,
            399925144,
            67141,
            395845182,
            3493141164329470,
            290851143,
            3537119419042405,
            26916676,
            161106007,
            226286970,
            505470889,
            296093128,
            514362734,
            3493118999529865,
            438956793,
            3546585919130360,
            28861187,
            597823619,
            326499679,
            50145252,
            394091270,
            382198016,
            7815280,
            483232841,
            1422294,
            390179953,
            1312702972,
            1079825019,
            475912512,
            519163662,
            275522811,
            13630808,
            131509166,
            40665101,
            438249246,
            13164144,
            25813,
            204120111,
            1868902080,
            382318634,
            172269292,
            28938343,
            3546586793642838,
            432131619,
            2001534,
            387414374,
            406871371,
            470998073,
            3493286016715621,
            3493136928082317,
            5788217,
            212520172,
            19762253,
            84359667,
            8523650,
            8881297,
            3546611349195586,
            270317383,
            1501416672,
            450185921,
            249770505,
            1800045535,
            670406059,
            28143775,
            353318057,
            394711337,
            3493104365603329,
            366468148,
            1864106469,
            9001997,
            1016116969,
            5080853,
            51156028,
            1478409891,
            3546571603970543,
            3493271338748086,
            3546591350754134,
            1927037753,
            57584675,
            3493134539425925,
            3546386867947958,
            442799448,
            442433707,
            1677445,
            81345676,
            501271968,
            11544428,
            181804397,
            40006642,
            555882509,
            16304186,
            3493131160913998,
            3494353391585585,
            676200579,
            15884598,
            517312875,
            257871895,
            677573141,
            162151104,
            1861940979,
            323024456,
            40488476,
            390600690,
            2011749793,
            451867943,
            8065087,
            1318036049,
            690601717,
            671538942,
            3546392328931335,
            3494362438699415,
            241062897,
            3546561632012585,
            471827265,
            3494354387733101,
            3546581471070432,
            288630011,
            3537120390023307,
            1776037,
            3494373702502581,
            428350256,
            1849410874,
            3493105997187935,
            19432127,
            388742853,
            494877604,
            3493143888529706,
            676608450,
            3546575571782042,
            2142803447,
            61879712,
            2000609327,
            674539396,
            3537120012535816,
            3494377829697625,
            74112426,
            3546605781256354,
            490096466,
            1048734456,
            295939334,
            3493136433154204,
            41322626,
            480108216,
            1609526545,
            3494349618809370,
            43220898,
            1221637505,
            361775100,
            1619305144,
            1713150198,
            129860965,
            7482932,
            7514413,
            1872701020,
            441666939,
            3546604193712453,
            3461565862906475,
            701388668,
            7951280,
            483571431,
            3546601962343143,
            57931345,
            2023371763,
            6655514,
            1625224065,
            316674188,
            3493076259571957,
            25852539,
            3546585526962572,
            17892516,
            3493260743936120,
            3493266412538144,
            1388197149,
            1647442754,
            3493279152736345,
            129927976,
            289254911,
            402416759,
            202653692,
            486874632,
            50329118,
            161720141,
            3537109818280481,
            434017074,
            650663945,
            308110197,
            1206813890,
            38047059,
            3493085459778150,
            354933377,
            507379381,
            3494360530291387,
            3493145165695750,
            362788146,
            3493274857769109,
            3493298704485308,
            1624498938,
            3546569418738131,
            1736214473,
            661965883,
            1549035,
            7002827,
            25887826,
            652281965,
            3546389355170433,
            3546585608751224,
            73415842,
            628451542,
            3493267412880183,
            300634025,
            456869112,
            260777624,
            1114539017,
            410502055,
            179407530,
            3546582169422209,
            1288772,
            3537118540335992,
            3546560665225304,
            17832530,
            495443110,
            3546558119283625,
            475768460,
            503492188,
            77943061,
            617459493,
            4578433,
            552530237,
            1447555,
            1899220593,
            210028574,
            2139961917,
            1322086170,
            402439210,
            390892,
            3461563858029334,
            254682216,
            3494357371980734,
            3493257151514770,
            3546569288714792,
            3546614608169407,
            3546612137724690,
            10310692,
            193585800,
            398597510,
            1691085051,
            3546584379820848,
            3546587137575734,
            3493112397695311,
            629601798,
            600359203,
            3494365169190991,
            405279279,
            13046,
            698438232,
            428040854,
            49785517,
            300702024,
            1856528671,
            276928941,
            618447026,
            233108841,
            353609978,
            3494360677091641,
            597701,
            149145888,
            628647489,
            483439650,
            145901490,
            4868003,
            1894087058,
            3493277313534134,
            249512,
            2080561247,
            399918500,
            421669645,
            473950562,
            783075,
            1824814640,
            3494377817114721,
            264862821,
            4689610,
            477007052,
            39776696,
            32741563,
            8156542,
            480995615,
            1237606399,
            333211352,
            3537109228980530,
            7349,
            3546385752263407,
            3546593980582299,
            6905116,
            3493146293963304,
            3546375010650869,
            3546572027595605,
            3494376642710133,
            5408366,
            3546582217656805,
            476116996,
            3546578570709595,
            3546380448565968,
            1097083213,
            67175339,
            429714179,
            3494358064040446,
            52423847,
            3546568147864207,
            3537118376757251,
            522367764,
            120454010,
            383095,
            4507159,
            3546393671109159,
            228058205,
            14916113,
            473244363,
            3546381031573584,
            1665814220,
            73846456,
            240264404,
            523165888,
            1317059990,
            28934624,
            25487242,
            637187407,
            163653,
            359127917,
            52457965,
            360234219,
            18081402,
            480761641,
            479122299,
            23454070,
            373471445,
            171844704,
            3493293461604604,
            141664434,
            1912950348,
            3537125792286787,
            3493140916865450,
            354340498,
            3546608325102324,
            44937175,
            3461563923040303,
            3546559671175666,
            3494363801847943,
            3546556848408781,
            207211376,
            12210545,
            9964401,
            3546588425226836,
            412650254,
            9802904,
            1796865271,
            3546394092636294,
            700304332,
            1058373230,
            51178727,
            508292812,
            433612309,
            3546583085878159,
            7987912,
            2094056221,
            3493144085662191,
            76045082,
            446184263,
            3546579732532060,
            46356715,
            1815364,
            13829896,
            59097656,
            504406727,
            29329085,
            436197297,
            253761257,
            14626386,
            3493275610646926,
            3546605405866064,
            2728123,
            28822227,
            436665925,
            26989008,
            100674883,
            1879281116,
            34144840,
            295396262,
            491728962,
            3546378707929125,
            282234318,
            419220,
            3493108949977323,
            491118390,
            3494374853839123,
            321391209,
            3493296160639187,
            29332710,
            3493109639940441,
            3494380161730626,
            361124424,
            137952,
            3709586,
            3493113230265002,
            1427895,
            2034176092,
            1205495476,
            1569337486,
            2117588160,
            1624848965,
            3494372867836563,
            489790761,
            1,
            494611210,
            2051371208,
            3546386807130885,
            430641591,
            1965051467,
            39858121,
            275981,
            3546560294029394,
            37390043,
            164627,
            3546579342461018,
            2995733,
            319084300,
            8084791,
            2529007,
            1881796598,
            3127528,
            4287618,
            180311598,
            3493144272309101,
            315554376,
            215626311,
            13565996,
            3493258283977582,
            3546392819665605,
            3546571553638932,
            108866409,
            1060170678,
            185709816,
            183462346,
            3570093,
            4831263,
            3546376906475584,
            3493258732767466,
            15940002,
            3537117839886340,
            331195228,
            450731805,
            3546606286670567,
            1855519979,
            3537117036677627,
            483184309,
            1813207326,
            506008646,
            5500585,
            3546579415861359,
            306243985,
            3493287662979492,
            252110355,
            1836588299,
            1561515,
            690608698,
            587067607,
            330113,
            27512611,
            1834090921,
            455001021,
            3493277349186168,
            3546383590098998,
            3461570877197190,
            3493085258451879,
            30654958,
            1864757,
            1213949796,
            3546577784277425,
            1376650682,
            75480955,
            396316042,
            1279920682,
            3546584344169345,
            392170748,
            303573687,
            3494356673629124,
            271265555,
            1517763,
            242136088,
            25072735,
            8492739,
            15938156,
            369355405,
            488791101,
            112326892,
            438108472,
            388684610,
            422568947,
            303036871,
            556214167,
            3546574533691447,
            474271530,
            495834671,
            19353880,
            385177544,
            1800205731,
            3537119532288563,
            485852279,
            1980919855,
            32700318,
            4564056,
            657804,
            338617869,
            73051222,
            780791,
            3546591178787449,
            3546604762040540,
            3493080290298403,
            13477686,
            3546599942785333,
            79577853,
            201189,
            3546565746624875,
            1710204,
            3493282965359329,
            3537120142559895,
            191238060,
            389661489,
            686201061,
            3546392410721100,
            3546587739457542,
            382109768,
            3546583777937416,
            3493138589026311,
            3546602574710835,
            9404404,
            52058013,
            389088,
            318814252,
            353708919,
            3461579420993636,
            3537109073791588,
            3546384800155947,
            247324785,
            287190004,
            42163853,
            3546382296156775,
            1577804,
            24840238,
            697168351,
            592150173,
            511015948,
            36942607,
            1519134,
            807817,
            1665228366,
            12901940,
            3461570791214015,
            3546392830151287,
            2068290472,
            336649293,
            26261068,
            3546567963314854,
            3494370875542389,
            3493120173935568,
            3735450,
            3546591786961668,
            472497932,
            328133860,
            431404385,
            665181,
            31230055,
            477631979,
            55479977,
            82380529,
            235119834,
            268999208,
            3546601316420557,
            3546554835142977,
            10985479,
            423802410,
            3546579365529816,
            3546579237603837,
            1920908011,
            451115073,
            287390748,
            1432747633,
            235555226,
            1979117482,
            3493259242375305,
            234430486,
            479149236,
            1797746737,
            3461572997417576,
            25826990,
            66607740,
            491302664,
            102670251,
            23723448,
            647359920,
            25117083,
            1221879760,
            622557681,
            688537578,
            3494357447478112,
            3821157,
            3546389720074629,
            514442152,
            629425724,
            626789173,
            306936843,
            32909772,
            3546589490579604,
            3546583123626739,
            3546578394548552,
            326949807,
            1242743972,
            2045003,
            345637267,
            3493130317859637,
            3546592904743002,
            2052851329,
            21615973,
            2029306,
            470800039,
            95090812,
            3546575387232823,
            1819400390,
            382580184,
            2072586344,
            701179700,
            664086886,
            1617515924,
            3546562057734227,
            3537121650412059,
            3546585239652561,
            1619192567,
            3494356927384280,
            22081435,
            3493288778664767,
            598808891,
            9151481,
            349316844,
            3494371481618553,
            25000899,
            1870845692,
            8618005,
            3494361880856991,
            18306025,
            108766164,
            20094989,
            629219032,
            3494378450454586,
            1068536952,
            696057192,
            8624082,
            383724164,
            340273654,
            777536,
            259638715,
            425642,
            1510647653,
            671264816,
            3546588492335307,
            3546383636237157,
            1876619321,
            6285309,
            314401241,
            551404525,
            3493271057730096,
            3460280,
            12450452,
            380551543,
            398223772,
            3537122520730473,
            179568377,
            39964093,
            373546001,
            502193688,
            43219807,
            617775502,
            3493132035427070,
            43721113,
            1271916102,
            497525820,
            356369995,
            68021907,
            6969062,
            15358689,
            3546584706975781,
            364416989,
            93686590,
            12939237,
            8908944,
            1255435359,
            3546593001212437,
            1743593860,
            3546563678833475,
            237140787,
            3546379135748876,
            382696576,
            385143694,
            9004111,
            632207543,
            3494376640613074,
            3546570997893383,
            3494370223327232,
            3546564282812924,
            489412051,
            1349294347,
            522708672,
            15462010,
            401168825,
            41853418,
            3494358269561570,
            1497555,
            1571570218,
            3546599452051699,
            107473818,
            3760773,
            78013399,
            1489545634,
            315151971,
            2390163,
            1536568491,
            396481253,
            391774002,
            514926676,
            494934731,
            257605948,
            94510621,
            3494361526438335,
            36700106,
            544336675,
            1393437,
            3546582888745247,
            287886755,
            11131476,
            679237565,
            383053366,
            480582281,
            25237642,
            457462821,
            1206440560,
            502027274,
            1821580575,
            796978,
            71694397,
            24065322,
            1533440983,
            3546383055325977,
            399815233,
            3546381536987157,
            325294915,
            593002848,
            393220967,
            921044,
            248305128,
            703182646,
            31150341,
            1601364131,
            1514351646,
            3493287600065480,
            14357325,
            60702941,
            3546591835196172,
            3493294401129029,
            551062363,
            362123499,
            3493117489580467,
            1920863298,
            619805457,
            414411614,
            404888281,
            403940805,
            19888888,
            479326757,
            441897078,
            1067722283,
            631146901,
            21068151,
            18234591,
            352596669,
            3494369931823571,
            2052016987,
            391445,
            179651913,
            4590552,
            1156144197,
            2110567804,
            1282271864,
            1522570666,
            19288025,
            3493271198239548,
            3546389868972074,
            3546579547982386,
            532791,
            82044006,
            396788198,
            2108856,
            275016013,
            43272050,
            249153892,
            3494350191331449,
            98666360,
            11223799,
            441833336,
            385378925,
            1069874770,
            44373414,
            3493131630676612,
            3546592195905641,
            100562870,
            3546589106801172,
            318620091,
            3546366466852921,
            3546556684831328,
            370200323,
            3546586586024608,
            17038445,
            3546380152867244,
            20488878,
            3546388430326591,
            391063471,
            28278764,
            90957375,
            525124571,
            335573347,
            3546585036229249,
            333334084,
            73587174,
            3537109822474581,
            38385543,
            571791768,
            27218150,
            3546572799347360,
            647310437,
            104655299,
            624757844,
            454673997,
            27564630,
            3546558983309335,
            385586872,
            444200878,
            3546390210807877,
            2038213385,
            24526143,
            2778055,
            1310542304,
            3546559425809054,
            39281277,
            485401838,
            25879971,
            6421869,
            47236123,
            1697120080,
            3546569326463026,
            3493130959588185,
            25470223,
            2072717192,
            2051617240,
            480680646,
            133132,
            13854759,
            94599618,
            436258392,
            474566624,
            3493133878823219,
            375191059,
            516512434,
            21057784,
            226102317,
            529249,
            58923464,
            3614240,
            94270150,
            3537122600422180,
            1678147735,
            291656314,
            1056226751,
            1485277312,
            3493290261350560,
            2086914019,
            254726274,
            3546384905013340,
            3494367880809387,
            316955009,
            686606640,
            103128201,
            3493134099024327,
            1150915963,
            663775136,
            3546380599560763,
            97495251,
            1771385364,
            51260551,
            474075001,
            14387072,
            3494354943478207,
            16409654,
            698550911,
            27717502,
            3494370097498223,
            25938105,
            3537113779800745,
            476935471,
            3493142460369130,
            3546571715119846,
            2010167052,
            8670079,
            524154749,
            3546372888332910,
            690748574,
            516677641,
            669171629,
            672596161,
            14238585,
            12260,
            1097927383,
            3493074929977892,
            523841848,
            3493140294011340,
            317631826,
            382281138,
            673258366,
            18226672,
            351686170,
            93841264,
            3537111588276745,
            3537122732542813,
            13908542,
            3493118494116797,
            343896546,
            90873,
            3546554600261774,
            1285048861,
            50144673,
            1798443432,
            396998418,
            381820630,
            178429408,
            8615846,
            674121390,
            32708543,
            1588219408,
            1046210349,
            1232220869,
            430040367,
            3546556598847987,
            1902330279,
            297929898,
            1404690642,
            398629298,
            3546566554028938,
            7706705,
            3494375428459474,
            3546592902645924,
            3546582884551097,
            1538249,
            3546587076758330,
            34023081,
            39115570,
            1990455546,
            374183950,
            21808424,
            1813205998,
            2103816454,
            1113108521,
            21353574,
            183430,
            1641720127,
            1002318188,
            412493059,
            38849217,
            591892279,
            3546393121654885,
            456239799,
            429749003,
            386387204,
            3546595626846430,
            3546593223510226,
            697737710,
            6446922,
            1705813027,
            15084373,
            213697595,
            6458603,
            21562856,
            474480402,
            402593521,
            2124352378,
            2122458627,
            27403737,
            28200210,
            514665245,
            3035105,
            1847229100,
            3493080034445826,
            1678704506,
            1753389255,
            3546559295785809,
            7555391,
            14064034,
            454539762,
            702596883,
            1329085897,
            430648086,
            676238724,
            104342965,
            1099766788,
            304066098,
            264442337,
            3546375935494445,
            3494353704061716,
            496944206,
            20409215,
            1762258446,
            439108787,
            3546390376482934,
            3493088288836299,
            1508362912,
            386495613,
            5321968,
            489075815,
            477792,
            63892820,
            479179848,
            3546579359238152,
            1695220112,
            3494349635586827,
            1041474702,
            36081646,
            212273071,
            2078781964,
            3546589056469052,
            3546558670834289,
            413703,
            800431,
            149592,
            3546373775427738,
            3461577688746016,
            3546379727145630,
            533996453,
            1207274989,
            3493135705443235,
            1692198284,
            3537107937135483,
            3494363847985966,
            3546373234363030,
            587050283,
            26141511,
            3493075812879152,
            36231559,
            3537122988394668,
            3546563683027648,
            168834692,
            3546562743503281,
            279148275,
            3546392557521504,
            14049552,
            3546579422152881,
            1241721676,
            14553873,
            3494369332038563,
            14079394,
            3494361004247573,
            686581006,
            61898737,
            601737168,
            16836724,
            33064694,
            33605910,
            434950053,
            274459325,
            396826032,
            1184134670,
            430351780,
            35012692,
            390647282,
            690466686,
            1365139602,
            3493074630085052,
            9321359,
            3493270950775388,
            2088487272,
            3494377934555297,
            123639998,
            496158245,
            526729810,
            17898455,
            335515254,
            51030552,
            232750024,
            3546393782258039,
            1667514736,
            3493119043570098,
            513361925,
            190942638,
            485568023,
            526257714,
            3493106940906178,
            1074346981,
            417296980,
            504043099,
            31073126,
            509069409,
            3546387146869570,
            3546386094099147,
            520359099,
            3494363002833837,
            266075681,
            207329796,
            357061011,
            15116146,
            431646218,
            3461565898558001,
            7005369,
            6189069,
            3537120727665638,
            5168707,
            3546389296449813,
            424394752,
            1654172551,
            2061426062,
            45280964,
            546962791,
            493230543,
            21540057,
            342507763,
            13608402,
            3493138211539444,
            11121031,
            483311105,
            3546582651767123,
            1357128731,
            3546566382062356,
            23236091,
            9983449,
            3494380258200406,
            620666,
            267637532,
            1694610556,
            43769757,
            6055289,
            549049797,
            3546574720338075,
            677465908,
            1654338713,
            8751142,
            295606275,
            1628139107,
            474267806,
            22707531,
            32680671,
            16720403,
            586631367,
            3493082817366845,
            628895496,
            330774558,
            526510260,
            206706701,
            388567456,
            284453579,
            520494803,
            500615835,
            1494786563,
            194046502,
            26987075,
            434786611,
            515090296,
            8492486,
            26177922,
            238134119,
            417064185,
            505706074,
            669497011,
            3461581402802752,
            498857917,
            393107174,
            456902573,
            429873791,
            20012419,
            3494368814041403,
            391901062,
            91352,
            504859080,
            3546377684519102,
            23207307,
            37677705,
            475443398,
            689904,
            519872029,
            346059,
            3494380539218906,
            496148832,
            481855819,
            22492980,
            1513088467,
            324412345,
            514051666,
            84567302,
            883724,
            700764023,
            137543719,
            3493077213776788,
            614748272,
            8244646,
            349976981,
            479633069,
            434976151,
            590490400,
            162776218,
            47563275,
            11861569,
            15641218,
            3546381522307184,
            2137985829,
            1495135714,
            73427011,
            3493081433246513,
            3546557840361556,
            407429489,
            3546571264232375,
            401480763,
            1298579146,
            12799703,
            401742377,
            55398490,
            477318199,
            3494358099692362,
            3493290997451047,
            1846211239,
            35781336,
            39335774,
            226257459,
            3546384737241436,
            3546557326559354,
            38331130,
            1322550456,
            7862914,
            1216353331,
            168598,
            1890662098,
            1184238527,
            61637521,
            3493144656087841,
            340250800,
            37780021,
            108569350,
            3546373645404611,
            180983799,
            3493264086796543,
            328590987,
            10850238,
            1858788244,
            499135372,
            3546569861237287,
            274442384,
            1102073186,
            50329485,
            503801557,
            3494374897879365,
            287295904,
            3537117997173280,
            3546557649520888,
            3493259078798188,
            2016504838,
            1638469672,
            23213472,
            652298653,
            3546575127186161,
            651186829,
            21716305,
            3537119148509379,
            3537116529166543,
            1725978881,
            675081568,
            35798565,
            3546580187613271,
            436377373,
            66596113,
            284551466,
            536773688,
            573693898,
            1129687681,
            1676248821,
            386869863,
            3494352942795263,
            3493115455343048,
            597364896,
            1687766935,
            12444306,
            1556777122,
            583085712,
            3537123302967486,
            3546394092636388,
            3546562064026496,
            3494371661973969,
            1300500455,
            300646326,
            366761116,
            689229570,
            2094233792,
            3546377986509291,
            400230277,
            36265198,
            3493125324540501,
            1823500310,
            3494353580329697,
            3546572811930599,
            3546380125604140,
            3546581217315340,
            3546576473557107,
            471474481,
            3537121470056546,
            3546378280110877,
            17633031,
            505566286,
            8263502,
            67991584,
            23730666,
            473499647,
            193147738,
            745493,
            1241072475,
            301940,
            476085595,
            275209169,
            3493291060366195,
            16843978,
            3494368669338503,
            3546559983651507,
            419522569,
            18465890,
            1099371313,
            3546579797543866,
            223256662,
            66964454,
            3546569607482138,
            450062077,
            512488108,
            410922660,
            1741810867,
            626347730,
            3546582364457864,
            619185460,
            3546574915373830,
            400389050,
            3537118123002250,
            10867865,
            10267465,
            408683080,
            3493267228330427,
            3537106206984343,
            11617841,
            387873209,
            55051092,
            537789980,
            3494358212938584,
            17854241,
            131401424,
            1090409678,
            1226398781,
            21206328,
            26287758,
            38034169,
            22192872,
            699598998,
            7971871,
            699204462,
            10337485,
            2136132,
            513700415,
            3493135424424688,
            28451621,
            1747594614,
            1871737115,
            3546564666591611,
            34281603,
            3494357252442916,
            15770782,
            1565860520,
            557818222,
            6595,
            602664449,
            238623328,
            326246517,
            309134148,
            1202880548,
            103048625,
            30973654,
            348383515,
            1265301803,
            3546384015820931,
            281172076,
            1630529821,
            489400034,
            380800207,
            1569223452,
            212395881,
            621089888,
            631208134,
            386100603,
            358247498,
            100022032,
            1035854407,
            27717433,
            3546393683691626,
            2126499311,
            3546390424717336,
            149890182,
            3493260146247708,
            1710145840,
            194484313,
            3546378452076755,
            506055382,
            696823618,
            383268722,
            3546558366746964,
            3546386408671329,
            703018634,
            16510117,
            1717092095,
            3493267645663496,
            3493139945884106,
            3494361943771236,
            1752319365,
            14272337,
            57086,
            1914445316,
            3493295875426563,
            544161405,
            1504129585,
            478299220,
            477646977,
            46545652,
            326530944,
            176063604,
            3546561392937060,
            382666849,
            1300259363,
            3493080560830654,
            2143947781,
            1467300706,
            26499192,
            1841256325,
            1926095632,
            320258,
            141452588,
            2177350,
            1581329897,
            23068975,
            394988440,
            11164088,
            7596516,
            57863910,
            489004577,
            223289804,
            2088331161,
            1773346,
            1201485436,
            504505810,
            15782465,
            17171565,
            23791195,
            649661652,
            9448580,
            4370617,
            57608186,
            2733216,
            371612,
            638816489,
            294868409,
            496845537,
            387087511,
            352111,
            414406143,
            190854052,
            544030731,
            526886168,
            905323,
            221648,
            14141146,
            7295246,
            157761,
            390483777,
            436036217,
            168687092,
            674734501,
            444175222,
            479409514,
            55439761,
            395991094,
            701623084,
            3493123841853732,
            31155640,
            414059218,
            29338392,
            7744849,
            663083059,
            1530628534,
            25503580,
            7936287,
            216844,
            102751804,
            147546636,
            4364539,
            33380653,
            345734492,
            473837611,
            70903428,
            10814669,
            2177677,
            314387912,
            1338030495,
            1752630832,
            305470882,
            3461582430407479,
            91254197,
            1700284274,
            165016731,
            145544,
            158555793,
            480810988,
            15858567,
            31107135,
            32367854,
            264869770,
            48394160,
            689955536,
            101037051,
            528461028,
            4925207,
            229733301,
            102637603,
            620069664,
            3493082584582776,
            431073645,
            362767725,
            553536,
            8878219,
            49960899,
            2028453585,
            397554988,
            6731340,
            22238589,
            296732,
            1464627422,
            275956490,
            218413290,
            57276677,
            430726,
            89818930,
            41140492,
            2941854,
            2030906413,
            2979938,
            171086,
            14636150,
            434003400,
            696523981,
            418988661,
            21767408,
            17871667,
            92337361,
            39668304,
            521950960,
            477782158,
            103261012,
            262503053,
            191002806,
            1111924041,
            364510642,
            1850189660,
            367103968,
            8049684,
            622872714,
            52914908,
            333515232,
            518888859,
            307460405,
            357515451,
            432499697,
            2195452,
            9838560,
            216025,
            550674844,
            4305299,
            690856559,
            253350665,
            17223352,
            3461568046041659,
            84706708,
            393116415,
            203337614,
            78110942,
            198748058,
            70070,
            1182716845,
            942755,
            473519710,
            94281836,
            198427927,
            451618887,
            10119428,
            49362348,
            3546561957070965,
            50528422,
            3546390235974086,
            700608201,
            1864084681,
            9387093,
            7584632,
            420231720,
            1575718735,
            287795639,
            1514206231,
            1944092630,
            281718537,
            3493093607213343,
            254463269,
            379015709,
            3546384064055449,
            3546386157013826,
            3537119901387660,
            152389373,
            673059520,
            1010203255,
            6739643,
            177613639,
            172233467,
            2100609493,
            18154819,
            232472043,
            81824112,
            1000185818,
            243243435,
            444854666,
            23912390,
            493570956,
            327711134,
            590729158,
            3493076800636934,
            23920239,
            516685210,
            1117600375,
            673520112,
            471303350,
            354832248,
            1935882,
            1694196506,
            25577001,
            383530301,
            3493082110626505,
            384306796,
            369750017,
            31659234,
            1249926364,
            613115943,
            471278344,
            1656099063,
            401315430,
            691415738,
            108412997,
            25150941,
            172447618,
            37636616,
            1988816464,
            222628253,
            1310714247,
            2196632,
            346469145,
            24157637,
            94360081,
            4603239,
            1032936971,
            274282526,
            234507192,
            487207514,
            1858861103,
            37029661,
            485344823,
            4059920,
            434718226,
            6983491,
            5910565,
            396981801,
            668794409,
            96205654,
            1712677288,
            1980678022,
            1748347861,
            278760537,
            408539084,
            1959209,
            403731699,
            1593537869,
            10272440,
            233114659,
            488818381,
            405067166,
            26846937,
            36047134,
            27899754,
            354963705,
            1266594350,
            7599814,
            352735241,
            385079033,
            60429538,
            329519036,
            39279965,
            428112437,
            368671873,
            393163404,
            237691744,
            1598041481,
            2122302588,
            21838789,
            365842307,
            588240862,
            14871346,
            1863639532,
            133901828,
            516579621,
            293556783,
            224267770,
            130041813,
            1304031564,
            3493145624971298,
            115058458,
            435609896,
            3493258785196866,
            531236984,
            61055477,
            482474986,
            1248013461,
            88675080,
            1340190821,
            21401670,
            408715466,
            477322873,
            70783742,
            1845213301,
            211005705,
            585316473,
            1480201267,
            443237317,
            1871001,
            1096128140,
            1567835994,
            394618791,
            2048450375,
            3493089586972896,
            1221549602,
            4995329,
            25876945,
            946974,
            311871090,
            1538910381,
            647428124,
            6608033,
            457653459,
            611214594,
            1576770770,
            30079180,
            417583826,
            2000380121,
            427494870,
            37408712,
            154058118,
            434786180,
            25592156,
            142400951,
            493105507,
            1465254680,
            50329337,
            1046346301,
            231896831,
            8564761,
            310269586,
            30819051,
            453972,
            627553716,
            2145624252,
            470156882,
            17138783,
            269923679,
            543816944,
            519585408,
            383666009,
            396025514,
            293985384,
            174922880,
            1955897084,
            1023693244,
            25642632,
            112037663,
            1606210274,
            598464467,
            37663924,
            651039864,
            86439234,
            420461147,
            627710058,
            4551292,
            696899383,
            297594331,
            512103258,
            43222001,
            340242809,
            330246090,
            178690106,
            516248671,
            381875112,
            359211088,
            7861934,
            4186021,
            1297043116,
            472064280,
            174501086,
            1305067770,
            64985859,
            351085345,
            297991412,
            1842854433,
            3322724,
            382931759,
            475961,
            688146247,
            178323184,
            9617619,
            258852214,
            5626102,
            382072818,
            1880049807,
            12145493,
            35359510,
            1328260,
            589183005,
            1164893733,
            102734471,
            63414376,
            553450157,
            394373125,
            55083199,
            515019371,
            1458577926,
            37610578,
            311219139,
            399259929,
            1903083115,
            2038413965,
            1823213,
            647193094,
            1425239276,
            406425799,
            516638154,
            364680842,
            517461175,
            477316442,
            39101587,
            3053296,
            1521701206,
            47994846,
            473965081,
            397664175,
            1261835179,
            26012012,
            340380931,
            561914130,
            527134350,
            25654099,
            473830670,
            1358802044,
            442207408,
            627947058,
            1695585090,
            380375358,
            1833227,
            514645997,
            96611127,
            1930420310,
            403912654,
            1929903779,
            352063206,
            209757637,
            1438240034,
            178047796,
            1524323881,
            1974326,
            17236262,
            652205462,
            433865481,
            1536750746,
            17456270,
            6131739,
            485703766,
            294887687,
            1847279326,
            521960086,
            511744123,
            1024366005,
            1513368083,
            1476167907,
            327988055,
            343470950,
            12433090,
            652239032,
            1024186553,
            1429723107,
            628309293,
            251868562,
            102999485,
            2042487748,
            3532811,
            2140412037,
            396895652,
            90668673,
            277665295,
            389552703,
            171617844,
            578270486,
            2383748,
            673460902,
            109778207,
            405285618,
            1149104926,
            387636363,
            1723478808,
            1275608712,
            2004454126,
            585326130,
            1459627806,
            99748932,
            686890441,
            1010614805,
            187878266,
            205429635,
            1832605957,
            1952914799,
            334454303,
            315819794,
            255229141,
            628831867,
            1547028482,
            505670427,
            480520643,
            434249025,
            626184566,
            8349119,
            686978491,
            102308177,
            438284866,
            587079556,
            1807039532,
            628599946,
            1779709282,
            2114104946,
            1531631564,
            2454462,
            432158620,
            587272348,
            690100803,
            1488064527,
            651410600,
            333641046,
            1207226422,
            325889132,
            162827591,
            388800103,
            1590640199,
            10907932,
            2026733267,
            177560641,
            513858872,
            679151170,
            421635439,
            384495920,
            643873396,
            436170053,
            1365324912,
            476645168,
            404987905,
            586006318,
            2056013660,
            386055742,
            471130916,
            486445583,
            588049766,
            601210376,
            396808737,
            429597337,
            533316954,
            370877395,
            302951148,
            502893941,
            85682906,
            27034065,
            485422279,
            25876049,
            482515584,
            627629503,
            404066457,
            35365327,
            492777646,
            587108252,
            50233288,
            318081722,
            510173985,
            630280232,
            626369036,
            36719905,
            37896119,
            545433105,
            286980475,
            351870889,
            407022539,
            652532931,
            332632721,
            403730552,
            526693814,
            31748830,
            60253266,
            395845200,
            481429887,
            427487966,
            483980557,
            471926059,
            471130755,
            519219184,
            405724215,
            402925510,
            383768376,
            451913461,
            125086406,
            9535164,
            429643625,
            386615477,
            351899011,
            416514298,
            9068490,
            4223525
        ]
        # url = 'https://account.bilibili.com/api/member/getCardByMid?mid=%s' % mid
        # headers = {
        #     'cookie': cookie,
        #     'user-agent': ua
        # }
        # req = requests.get(url=url, headers=headers)
        # return req.json().get('card').get('attentions')

    # endregion

    async def getLastestScrapyInfo(self):
        try:
            with open(FileMap.获取过动态的b站用户, 'r', encoding='utf-8') as f:
                for k, v in json.load(f).items():
                    self.queriedData.queryUserInfo.update({
                        k: user_space_dyn_detail(**v)
                    })
            get_others_lot_log.info('上次获取的动态：')
            import pprint
            pprint.pprint(self.queriedData.queryUserInfo, indent=4)
        except Exception as e:
            get_others_lot_log.warning(f'获取b站用户的配置失败！使用默认内容！{e}')

        if os.path.exists(FileMap.uidlist_json):
            try:
                with open(FileMap.uidlist_json) as f:
                    self.queryingData.uidlist = json.load(f).get('uidlist')
                    self.queryingData.uidlist = list(set(self.queryingData.uidlist))
                    self.queriedData.uidlist = self.queryingData.uidlist
            except Exception as e:
                get_others_lot_log.warning(f'获取抽奖用户uid列表失败，使用默认配置！{e}')
        else:
            pass

        if os.path.exists(FileMap.get_dyid):
            try:
                with open(FileMap.get_dyid) as f:
                    for i in f.read().split(','):
                        if i.strip():
                            self.queriedData.dyidList.append(i.strip())
            except Exception as e:
                get_others_lot_log.warning(f'获取get_dyid列表失败，使用默认配置！{e}')
        else:
            pass

        if os.path.exists(FileMap.lot_dyid):
            try:
                with open(FileMap.lot_dyid) as f:
                    for i in f.read().split(','):
                        if i.strip():
                            self.queriedData.lotidList.append(i.strip())
            except Exception as e:
                get_others_lot_log.warning(f'获取lot_dyid列表失败，使用默认配置！{e}')
        else:
            pass

    def getGiteeLotdyid(self) -> list[str]:
        path = root_dir + "github/bili_upload"
        datanames = os.listdir(path)
        path_dir_name = []
        for i in datanames:
            if str.isdigit(i):
                path_dir_name.append(i)

        effective_files_content_list = []

        for i in path_dir_name:
            with open(root_dir + 'github/bili_upload/' + i + '/dyid.txt', 'r', encoding='utf-8') as f:
                effective_files_content_list.append(''.join(f.readlines()))
        for i in effective_files_content_list:
            self.queriedData.gitee_dyn_id_list = self.solveGiteeFileContent(i, self.queriedData.dyidList)  # 记录动态id
        get_others_lot_log.info(
            f'共获取{len(path_dir_name)}个文件，新增{len(self.queriedData.gitee_dyn_id_list)}条抽奖！')
        return self.queriedData.gitee_dyn_id_list

    # region 获取uidlist中的空间动态
    async def get_space_dynamic_req_with_proxy(self, hostuid: Union[int, str], offset: str):
        '''
        获取动态空间的response
        :param hostuid:要访问的uid
        :param offset:
        :return:reqtext
        '''
        ua = random.choice(CONFIG.UA_LIST)
        headers = {
            'user-agent': ua,
            'cookie': '1'
        }
        dongtaidata = {
            'offset': offset,
            'host_mid': hostuid,
            'timezone_offset': -480,
            'platform': 'web',
            'features': 'itemOpusStyle,listOnlyfans,opusBigCover,onlyfansVote',
            'web_location': "333.999",
        }
        dongtaidata = gen_dm_args(dongtaidata)  # 先加dm参数
        dongtaidata.update({
            "x-bili-device-req-json": json.dumps({"platform": "web", "device": "pc"}, separators=(',', ':')),
            "x-bili-web-req-json": json.dumps({"spm_id": "333.999"}, separators=(',', ':'))
        })
        wbi_sign = await get_wbi_params(dongtaidata)
        dongtaidata.update({
            'w_rid': wbi_sign['w_rid']
        })
        dongtaidata.update({
            "wts": wbi_sign['wts']
        })

        url = 'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space'
        headers.update({'referer': f"https://space.bilibili.com/{hostuid}/dynamic"
                        }
                       )
        url_params = url + '?' + urllib.parse.urlencode(dongtaidata, safe='[],:')

        try:
            req = await request_proxy.request_with_proxy(method='GET',
                                                         url=url_params,
                                                         headers=headers,
                                                         # data=dongtaidata,
                                                         verify=False,
                                                         mode='single'
                                                         )
            return req
        except Exception as e:
            get_others_lot_log.critical(f'Exception while getting space history dynamic {hostuid} {offset}!\n{e}')
            return await self.get_space_dynamic_req_with_proxy(hostuid, offset)

    def solveSpaceDetailResp(self, space_req_dict: dict):  # 直接处理
        '''
        解析空间动态的json，不过滤重复遇到过的内容
        :param space_req_dict:
        :return:
        '''

        def card_detail(cards_json):
            """
            返回间接动态和原始动态的动态id
            :param cards_json:
            :return:
            """
            # get_others_lot_log.info(card_json)  # 测试点
            try:
                orig_dy_id = str(cards_json.get('orig').get('id_str'))
            except:
                orig_dy_id = None

            return [orig_dy_id]

        req_dict = space_req_dict
        if req_dict.get('code') == -412:
            get_others_lot_log.info(req_dict)
            get_others_lot_log.info(req_dict.get('message'))
            # await asyncio.sleep(10 * 60)
        if not req_dict:
            get_others_lot_log.info(f'ERROR{space_req_dict}')
            return 404
        card_item = req_dict.get('data').get('items')
        dynamic_id_list = []
        if card_item:
            for card_dict in card_item:
                dynamic_id = str(card_dict.get('orig', {}).get('id_str', "0"))  # 判断中转动态id是否重复；非最原始动态id 类型为string
                try:
                    dynamic_repost_content = card_dict.get('modules').get('module_dynamic').get('desc').get('text')
                except:
                    dynamic_repost_content = None
                get_others_lot_log.info(
                    f"当前动态： https://t.bilibili.com/{card_dict.get('id_str')}\t{time.asctime()}\n转发|评论|发布内容：{dynamic_repost_content}")
                if dynamic_repost_content in self.nonLotteryWords:
                    # get_others_lot_log.info('转发评论内容为非抽奖词，跳过')
                    continue
                if dynamic_id == "0":
                    # get_others_lot_log.info('遇到已删除动态')
                    continue
                if dynamic_id in dynamic_id_list:
                    # get_others_lot_log.info('遇到重复动态id')
                    # get_others_lot_log.info('https://t.bilibili.com/{}'.format(dynamic_id))
                    continue
                dynamic_time = card_dict.get('modules').get('module_author').get('pub_ts')  # 判断是否超时，超时直接退出
                if time.time() - dynamic_time >= self.SpareTime:
                    # get_others_lot_log.info('遇到超时动态')
                    return 0
                for _ in card_detail(card_dict):
                    if _:
                        # get_others_lot_log.info(f'添加进记录：{_}')
                        dynamic_id_list.append(str(_))  # 间接和原始的动态id全部记录
        else:
            get_others_lot_log.error(space_req_dict)
            get_others_lot_log.error('cards_json为None')
        if dynamic_id_list:
            self.spaceRecordedDynamicIdList.extend(dynamic_id_list)

        # if not dynamic_id_list:
        #     await asyncio.sleep(2)
        return 0

    async def get_user_space_dynamic_id(self, uid: int, secondRound=False, isPubLotUser=False) -> None:
        """
        支持了断点续爬
        根据时间和获取过的动态来判断是否结束爬取别人的空间主页
        :return:
        """

        async def addSpaceCardToDb(spaceResp: dict):
            try:
                spaceResp['data']['items'] = [i for i in spaceResp.get('data').get('items') if
                                              i.get('modules', {}).get('module_tag', {}).get('text') != '置顶']
                if spaceResp.get('data') and spaceResp.get('data').get('items'):
                    for i in spaceResp.get('data').get('items'):
                        spaceRespCardDynamicId = i.get('id_str')
                        await self.sqlHlper.addSpaceResp(LotUserSpaceResp=TLotuserspaceresp(
                            spaceUid=uid,
                            spaceOffset=spaceRespCardDynamicId,
                            spaceRespJson=i,
                        ))
                return spaceResp
            except Exception as _e:
                get_others_lot_log.critical(f'添加空间动态响应至数据库失败！{spaceResp}\n{_e}')
                get_others_lot_log.exception(_e)

        async def solve_space_dynamic(space_req_dict: dict) -> Union[list[str], None]:
            """
            解析动态列表，获取动态id
            :param space_req_dict:
            :return:
            """
            ret_list = []
            try:
                for dynamic_item in space_req_dict.get('data').get('items'):
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
                        dynamic_detail = await self.solve_dynamic_item_detail(dynamic_id_str, single_dynamic_resp)
                        await self.judge_lottery_by_dynamic_resp_dict(dynamic_id_str,
                                                                      dynamic_detail=dynamic_detail)
                    else:
                        if dynamic_item.get('type') == 'DYNAMIC_TYPE_FORWARD':
                            module_dynamic = dynamic_item.get('modules').get('module_dynamic')
                            rich_text_nodes = module_dynamic.get('desc').get('rich_text_nodes')
                            dynamic_text = module_dynamic.get('desc').get('text')
                            at_users_nodes = list(
                                filter(lambda x: x.get('type') == 'RICH_TEXT_NODE_TYPE_AT', rich_text_nodes))
                            need_at_usernames = re.findall('//@(.{0,20}):', dynamic_text)
                            subbed_text = re.sub('.*//@(.{0,20}):', '', dynamic_text)
                            for need_at_username in need_at_usernames:
                                for i in at_users_nodes:
                                    if need_at_username in i.get('text'):
                                        need_uid = i.get('rid')
                                        pub_lot_user_infos = list(
                                            filter(lambda x: x.uid == need_uid, self.pub_lot_user_info_list))
                                        if pub_lot_user_infos:
                                            for _ in pub_lot_user_infos:
                                                if not _.find_dyn_content(subbed_text):
                                                    _.dynContent_list.append(subbed_text)
                                        else:
                                            self.pub_lot_user_info_list.append(
                                                pub_lot_user_info(
                                                    uid=need_uid,
                                                    dynContent_list=[subbed_text]
                                                )
                                            )

                if space_req_dict.get('data').get('inplace_fold'):
                    for i in space_req_dict.get('data').get('inplace_fold'):
                        if i.get('dynamic_ids'):
                            for dyn_id in i.get('dynamic_ids'):
                                ret_list.append(dyn_id)
                        get_others_lot_log.debug(f'遇到折叠内容！inplace_fold:{i}')
                if not space_req_dict.get('data').get('has_more') and len(ret_list) == 0:
                    return None
                return ret_list
            except Exception as _e:
                get_others_lot_log.exception(_e)
                raise _e

        def get_space_dynmaic_time(space_req_dict: dict) -> list[int]:  # 返回list
            cards_json = space_req_dict.get('data').get('items')
            dynamic_time_list = []
            if cards_json:
                for card_dict in cards_json:
                    dynamic_time = card_dict.get('modules').get('module_author').get('pub_ts')
                    dynamic_time_list.append(dynamic_time)
            return dynamic_time_list

        n = 0
        first_get_dynamic_falg = True
        origin_offset = 0
        LotUserInfo: TLotuserinfo = await self.sqlHlper.getLotUserInfoByUid(uid)

        if secondRound:
            newest_space_offset = await self.sqlHlper.getNewestSpaceDynInfoByUid(uid)
            if newest_space_offset:
                dynamic_calculated_ts = self.calculate_pub_ts_by_dynamic_id(newest_space_offset)
                updatetime = await self.sqlHlper.get_lot_user_info_updatetime_by_uid(uid)
                updatetime_ts = updatetime.timestamp() if updatetime else 0
                if int(time.time() - dynamic_calculated_ts) < 2 * 3600 or int(time.time() - updatetime_ts) < 2 * 3600:
                    get_others_lot_log.info(f'{uid} 距离上次获取抽奖不足2小时，跳过')
                    return
        if LotUserInfo:
            if not self.isPreviousRoundFinished:  # 如果上一轮抽奖没有完成
                origin_offset = LotUserInfo.latestFinishedOffset
        else:
            LotUserInfo = TLotuserinfo(
                uid=uid,
                isPubLotUser=isPubLotUser
            )
            await self.sqlHlper.addLotUserInfo(LotUserInfo)
        if uid not in self.queryingData.uidlist:
            self.queryingData.uidlist.append(uid)
        if uid not in self.queriedData.uidlist:
            self.queriedData.uidlist.append(uid)
        if secondRound:
            origin_offset = ""
        origin_offset = origin_offset if origin_offset else ""
        offset = origin_offset
        uname = ''
        timelist = [0]
        get_others_lot_log.info(
            f'当前UID：https://space.bilibili.com/{uid}/dynamic\t进度：【{self.queryingData.uidlist.index(uid) + 1}/{len(self.queryingData.uidlist)}】\t初始offseet:{origin_offset}\t是否为第二轮获取动态：{secondRound}')
        while 1:
            if origin_offset != "" and first_get_dynamic_falg:
                items = await self.sqlHlper.getSpaceRespTillOffset(uid, origin_offset)
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
            else:
                dyreq_dict = await self.get_space_dynamic_req_with_proxy(uid, offset)
                dyreq_dict = await addSpaceCardToDb(dyreq_dict)
            try:
                if dyreq_dict.get('data').get('items'):
                    uname = dyreq_dict.get('data').get('items')[0].get('modules').get('module_author').get('name')
            except Exception as e:
                get_others_lot_log.error(f'获取空间动态用户名失败！{dyreq_dict}')
                get_others_lot_log.exception(e)
            try:
                repost_dynamic_id_list = await solve_space_dynamic(dyreq_dict)  # 脚本们转发生成的动态id 同时将需要获取的抽奖发布者的uid记录下来
            except Exception as e:
                get_others_lot_log.critical(f'解析空间动态失败！\n{e}\n{uid} {offset}')
                get_others_lot_log.exception(e)
                continue
            if repost_dynamic_id_list is None:
                get_others_lot_log.info(f'{uid}空间动态数量为0')
                break
            async with self.lock:
                if repost_dynamic_id_list:
                    if first_get_dynamic_falg:
                        if self.queriedData.queryUserInfo.get(str(uid)):
                            update_num = len(repost_dynamic_id_list) - len(
                                set(repost_dynamic_id_list) & set(
                                    self.queriedData.queryUserInfo.get(str(uid)).latest_dyid_list))
                        else:
                            update_num = len(repost_dynamic_id_list)
                        self.queryingData.queryUserInfo.update(
                            {str(uid): user_space_dyn_detail(repost_dynamic_id_list[0:10], update_num)})
                        first_get_dynamic_falg = False
                    else:
                        if self.queriedData.queryUserInfo.get(str(uid)):
                            update_num = len(repost_dynamic_id_list) - len(
                                set(repost_dynamic_id_list) & set(
                                    self.queriedData.queryUserInfo.get(str(uid)).latest_dyid_list))
                        else:
                            update_num = len(repost_dynamic_id_list)
                        self.queryingData.queryUserInfo.get(str(uid)).update_num += update_num

                n += 1
                if self.solveSpaceDetailResp(dyreq_dict) != 0:  # 解析空间动态的json，不过滤重复遇到过的内容
                    offset = ""
                    continue
                offset = dyreq_dict.get('data').get('offset')
                timelist = get_space_dynmaic_time(dyreq_dict)
                # await asyncio.sleep(5)

                await self.sqlHlper.addLotUserInfo(
                    TLotuserinfo(uid=uid, uname=uname,
                                 updateNum=self.queryingData.queryUserInfo.get(str(uid)).update_num,
                                 updatetime=LotUserInfo.updatetime,
                                 isUserSpaceFinished=0,
                                 offset=offset,
                                 latestFinishedOffset=LotUserInfo.latestFinishedOffset,
                                 isPubLotUser=isPubLotUser
                                 ))
                if len(timelist) == 0:
                    get_others_lot_log.error('timelist is empty')
                    break
                if time.time() - timelist[-1] >= self.SpareTime:
                    get_others_lot_log.info(
                        f'超时动态，当前UID：https://space.bilibili.com/{uid}/dynamic\t获取结束\t{self.BAPI.timeshift(time.time())}')
                    # await asyncio.sleep(60)
                    break
                if self.queriedData.queryUserInfo.get(str(uid)):
                    # get_others_lot_log.info(self.queriedData.queryUserInfo.get(str(uid)))
                    # get_others_lot_log.info(repost_dynamic_id_list)
                    if set(self.queriedData.queryUserInfo.get(str(uid)).latest_dyid_list) & set(repost_dynamic_id_list):
                        get_others_lot_log.info(
                            f'遇到获取过的动态，当前UID：https://space.bilibili.com/{uid}/dynamic\t获取结束\t{self.BAPI.timeshift(time.time())}')
                        # await asyncio.sleep(60)
                        break

            try:
                if not dyreq_dict.get('data').get('has_more'):
                    get_others_lot_log.info(f'当前用户 https://space.bilibili.com/{uid}/dynamic 无更多动态')
                    break
            except Exception as e:
                get_others_lot_log.critical(f'Error: has_more获取失败\n{dyreq_dict}\n{e}')
                get_others_lot_log.exception(e)
        await self.sqlHlper.addLotUserInfo(TLotuserinfo(
            uid=uid,
            uname=uname,
            updateNum=self.queryingData.queryUserInfo.get(str(uid)).update_num if self.queryingData.queryUserInfo.get(
                str(uid)) else 0,
            updatetime=datetime.datetime.now() if origin_offset == "" else LotUserInfo.updatetime,
            isUserSpaceFinished=1,
            offset=offset,
            latestFinishedOffset=offset if not secondRound else LotUserInfo.latestFinishedOffset,
            isPubLotUser=isPubLotUser
        ))
        # if 1==1:
        #     return
        if origin_offset != "" and not secondRound:
            self.queriedData.queryUserInfo.update({
                str(uid): self.queryingData.queryUserInfo.get(str(uid))
            })
            await self.get_user_space_dynamic_id(uid, secondRound=True, isPubLotUser=isPubLotUser)
        if n <= 4 and time.time() - timelist[-1] >= self.SpareTime and secondRound == False:
            # self.uidlist.remove(uid)
            get_others_lot_log.info(f'{uid}\t当前UID获取到的动态太少，前往：\nhttps://space.bilibili.com/{uid}\n查看详情')
        self.space_sem.release()

    async def getAllSpaceDynId(self, uidlist=None, isPubLotUser=False) -> list[str]:
        if uidlist is None:
            uidlist = self.queryingData.uidlist
        uidlist = list(set(uidlist))
        tasks = []
        for i in uidlist:
            await self.space_sem.acquire()
            task = asyncio.create_task(self.get_user_space_dynamic_id(i, isPubLotUser=isPubLotUser))
            tasks.append(task)
        await asyncio.gather(*tasks)
        while True:
            task_doing = [i for i in tasks if not i.done()]
            if len(task_doing) == 0:
                break
            else:
                get_others_lot_log.debug(f'当前正在获取用户空间的任务数量：{len(task_doing)}/{len(tasks)}')
            await asyncio.sleep(5)
        await asyncio.gather(*tasks, return_exceptions=False)
        return self.spaceRecordedDynamicIdList

    # endregion
    # region 判断单个动态是否是抽奖动态

    async def thread_judgedynamic(self, write_in_list):
        async def judge_single_dynamic(dynamic_id):
            new_resp = await self.get_dyn_detail_resp(dynamic_id)
            dynamic_detail = await self.solve_dynamic_item_detail(dynamic_id, new_resp)
            await self.judge_lottery_by_dynamic_resp_dict(dynamic_id, dynamic_detail)
            self.sem.release()

        get_others_lot_log.info('多线程获取动态')
        task_list = []
        for i in write_in_list:
            await self.sem.acquire()
            tk = asyncio.create_task(judge_single_dynamic(i))
            task_list.append(tk)

        while True:
            task_doing = [i for i in task_list if not i.done()]
            if len(task_doing) == 0:
                break
            else:
                get_others_lot_log.debug(f'当前正在获取动态的任务数量：{len(task_doing)}/{len(task_list)}')
            await asyncio.sleep(5)

        get_dyn_resp_result = await asyncio.gather(*task_list, return_exceptions=False)
        get_others_lot_log.info(f'获取动态报错结果：{get_dyn_resp_result}')

    async def get_dyn_detail_resp(self, dynamic_id, _cookie="", _useragent="", dynamic_type=2) -> dict:
        """
        返回{
                        'code':0,
                        'data':{
                            "item":dynamic_req
                        }
                    }这样的dict
        :param dynamic_id:
        :param _cookie:
        :param _useragent:
        :param dynamic_type:
        :return:
        """
        dynamic_req = None
        isDynExist = await self.sqlHlper.isExistDynInfoByDynId(dynamic_id)
        if isDynExist:
            # get_others_lot_log.critical(f'存在过的动态！！！{isDynExist.__dict__}')
            if isDynExist.officialLotType != OfficialLotType.抽奖动态的源动态.value:
                dynamic_req = isDynExist.rawJsonStr
                if type(dynamic_req) is not None:
                    dynamic_req = {
                        'code': 0,
                        'data': {
                            "item": dynamic_req
                        }
                    }
        isSpaceExist = await self.sqlHlper.isExistSpaceInfoByDynId(dynamic_id)
        if isSpaceExist:
            # get_others_lot_log.critical(f'存在过的动态！！！{isDynExist.__dict__}')
            dynamic_req = isSpaceExist.spaceRespJson
            if type(dynamic_req) is not None:
                dynamic_req = {
                    'code': 0,
                    'data': {
                        "item": dynamic_req
                    }
                }
        if _cookie == '':
            headers = {
                'referer': f'https://t.bilibili.com/{dynamic_id}', 'Connection': 'close',
                'user-agent': random.choice(CONFIG.UA_LIST),
                'cookie': '1'
            }
        else:
            headers = {
                'referer': f'https://t.bilibili.com/{dynamic_id}', 'Connection': 'close',
                'user-agent': random.choice(CONFIG.UA_LIST),
                'cookie': _cookie
                # 'X-Forwarded-For': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
                #                                         random.choice(range(0, 255)), random.choice(range(0, 255))),
                # 'X-Real-IP': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
                #                                   random.choice(range(0, 255)), random.choice(range(0, 255))),
                # 'From': 'bingbot(at)microsoft.com',
            }
        url = 'http://api.bilibili.com/x/polymer/web-dynamic/v1/detail'
        data = {
            'timezone_offset': -480,
            'platform': 'web',
            'gaia_source': 'main_web',
            'id': dynamic_id,
            'features': 'itemOpusStyle,opusBigCover,onlyfansVote,endFooterHidden',
            'web_location': '333.1368',
            "x-bili-device-req-json": json.dumps({"platform": "web", "device": "pc"}, separators=(',', ':')),
            "x-bili-web-req-json": json.dumps({"spm_id": "333.1368"}, separators=(',', ':'))
        }
        if dynamic_type != 2:
            data = {
                'timezone_offset': -480,
                'platform': 'web',
                'gaia_source': 'main_web',
                'rid': dynamic_id,
                'type':dynamic_type,
                'features': 'itemOpusStyle,opusBigCover,onlyfansVote,endFooterHidden',
                'web_location': '333.1368',
                "x-bili-device-req-json": json.dumps({"platform": "web", "device": "pc"}, separators=(',', ':')),
                "x-bili-web-req-json": json.dumps({"spm_id": "333.1368"}, separators=(',', ':'))
            }
        wbi_sign = await get_wbi_params(data)
        data.update({
            'w_rid': wbi_sign['w_rid'],
            "wts": wbi_sign['wts']
        })
        url_with_params = url + '?' + urllib.parse.urlencode(data, safe='[],:')
        try:
            if not dynamic_req:
                dynamic_req = await request_proxy.request_with_proxy(method='GET', url=url_with_params, headers=headers,
                                                                     mode='single')
        except Exception as e:
            traceback.print_exc()
            return await self.get_dyn_detail_resp(dynamic_id, _cookie, _useragent)
        return dynamic_req

    async def solve_dynamic_item_detail(self, dynamic_id, dynamic_req: dict) -> dict:
        """
        使用代理获取动态详情，传入空间的动态响应前，需要先构建成单个动态的响应！！！
        :param dynamic_req: {code:4101131,data:{item:...} }
        :param dynamic_id:
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

        try:
            if dynamic_req.get('code') == 4101131:
                get_others_lot_log.info(f'动态内容不存在！{dynamic_id}\t{dynamic_req}')
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
            if dynamic_type == '2' and str(dynamic_data_dynamic_id) != dynamic_id:
                get_others_lot_log.critical(f"获取的动态信息与需要的动态不符合！！！{dynamic_data}")
                new_req = await self.get_dyn_detail_resp(dynamic_id)
                return await self.solve_dynamic_item_detail(dynamic_id, new_req)
            dynamic_rid = dynamic_item.get('basic').get('comment_id_str')
            relation = dynamic_item.get('modules').get('module_author').get('following')
            author_uid = dynamic_item.get('modules').get('module_author').get('mid')
            author_name = dynamic_item.get('modules').get('module_author').get('name')
            # pub_time = dynamic_item.get('modules').get('module_author').get('pub_time') # 这个遇到一些电视剧，番剧之类的特殊响应会无法获取到
            pub_time = datetime.datetime.fromtimestamp(
                self.calculate_pub_ts_by_dynamic_id(dynamic_data_dynamic_id)).strftime('%Y年%m月%d日 %H:%M')
            pub_ts = dynamic_item.get('modules').get('module_author').get('pub_ts')
            try:
                official_verify_type = dynamic_item.get('modules').get('module_author').get(
                    'official_verify').get('type')
                if type(official_verify_type) is str:
                    official_verify_type = 1
            except:
                official_verify_type = -1
            comment_count = dynamic_item.get('modules').get('module_stat').get('comment').get('count')
            forward_count = dynamic_item.get('modules').get('module_stat').get('forward').get('count')
            like_count = dynamic_item.get('modules').get('module_stat').get('like').get('count')
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
            is_liked = dynamic_item.get('modules').get('module_stat').get('like').get('status')
            if is_liked:
                is_liked = 1
            else:
                is_liked = 0
            if relation != 1:
                get_others_lot_log.info(
                    f'未关注的response\nhttps://space.bilibili.com/{author_uid}\n{dynamic_data_dynamic_id}')
        except Exception as e:
            get_others_lot_log.critical(f'https://t.bilibili.com/{dynamic_id}\n{dynamic_req}\n{e}')
            traceback.print_exc()
            if dynamic_req.get('code') == -412:
                get_others_lot_log.info('412风控')
                await asyncio.sleep(10)
                new_req = await self.get_dyn_detail_resp(dynamic_id)
                return await self.solve_dynamic_item_detail(dynamic_id, new_req)
            if dynamic_req.get('code') == 4101128:
                get_others_lot_log.info(dynamic_req.get('message'))
            if dynamic_req.get('code') is None:
                new_req = await self.get_dyn_detail_resp(dynamic_id)
                return await self.solve_dynamic_item_detail(dynamic_id, new_req)
            if dynamic_req.get('code') == 401:
                get_others_lot_log.critical(dynamic_req)
                await asyncio.sleep(10)
                new_req = await self.get_dyn_detail_resp(dynamic_id)
                return await self.solve_dynamic_item_detail(dynamic_id, new_req)
            return {}

        top_dynamic = None
        try:
            module_tag = dynamic_item.get('modules').get('module_tag')
            if module_tag:
                module_tag_text = module_tag.get('text')
                if module_tag_text == "置顶":
                    top_dynamic = True
                else:
                    get_others_lot_log.info(module_tag_text)
                    get_others_lot_log.info('未知动态tag')
            else:
                top_dynamic = False
        except:
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
            get_others_lot_log.info(dynamic_req)
            get_others_lot_log.error(e)
            traceback.print_exc()
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

    # region 获取评论
    async def get_pinglunreq_with_proxy(self, dynamic_id, rid, pn, _type, *mode):
        """
        3是热评，2是最新的，大概
        :param dynamic_id:
        :param rid:
        :param pn:
        :param _type:
        :param mode:
        :return:
        """
        if mode:
            mode = mode[0]
        else:
            mode = 2
        ctype = 17
        if str(_type) == '8':
            ctype = 1
        elif str(_type) == '4' or str(_type) == '1':
            ctype = 17
        elif str(_type) == '2':
            ctype = 11
        elif str(_type) == '64':
            ctype = 12
        if len(str(rid)) == len(str(dynamic_id)):
            oid = dynamic_id
        else:
            oid = rid
        pinglunheader = {
            'Referer': f'https://t.bilibili.com/{rid}?type={_type}',
            'Connection': 'close',
            'User-Agent': random.choice(CONFIG.UA_LIST),
            'cookie': '1'
        }
        pinglunurl = 'http://api.bilibili.com/x/v2/reply/main?next=' + str(pn) + '&type=' + str(ctype) + '&oid=' + str(
            oid) + '&mode=' + str(mode) + '&plat=1&_=' + str(int(time.time()))
        pinglundata = {
            'jsonp': 'jsonp',
            'next': pn,
            'type': ctype,
            'oid': oid,
            'mode': mode,
            'plat': 1,
            '_': time.time()
        }
        try:
            pinglunreq = await request_proxy.request_with_proxy(method="GET", url=pinglunurl, data=pinglundata,
                                                                headers=pinglunheader, mode='single')
        except:
            traceback.print_exc()
            get_others_lot_log.info(f'{pinglunurl}\t获取评论失败')
            pinglunreq = await self.get_pinglunreq_with_proxy(dynamic_id, rid, pn, _type)
            return pinglunreq
        return pinglunreq

    async def get_topcomment_with_proxy(self, dynamicid, rid, pn, _type, mid):
        iner_replies = ''
        pinglunreq = await self.get_pinglunreq_with_proxy(dynamicid, rid, pn, _type, 3)
        try:
            pinglun_dict = pinglunreq
            pingluncode = pinglun_dict.get('code')
            if pingluncode != 0:
                get_others_lot_log.info('获取置顶评论失败')
                message = pinglun_dict.get('message')
                get_others_lot_log.info(pinglun_dict)

                if message != 'UP主已关闭评论区' and message != '啥都木有' and message != '评论区已关闭':
                    while 1:
                        try:
                            await asyncio.sleep(1)
                            break
                        except:
                            continue
                    return 'null'
                else:
                    get_others_lot_log.info(message)
                    return 'null'
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
                topmsg = 'null' + iner_replies
        except Exception as e:
            get_others_lot_log.info(e)
            get_others_lot_log.info('获取置顶评论失败')
            if pinglunreq is None or pinglunreq.get('code') is None:
                return await self.get_topcomment_with_proxy(dynamicid, rid, pn, _type, mid)
            pinglun_dict = pinglunreq
            data = pinglun_dict.get('data')
            get_others_lot_log.info(pinglun_dict)
            get_others_lot_log.info(data)
            topmsg = 'null'
            get_others_lot_log.info(self.BAPI.timeshift(int(time.time())))
            if data == '评论区已关闭':
                topmsg = data
            else:
                while 1:
                    try:
                        await asyncio.sleep(1)
                        break
                    except:
                        continue
        return topmsg

    # endregion

    async def judge_single_dynamic_id(self, dynamic_id: str, dynamic_type: int = 2, is_lot_orig=False):
        dynamic_detail = None
        while 1:
            try:
                fake_cookie_str = ""

                if self.fake_cookie:
                    fake_cookie_str = self.fake_cookie
                else:
                    fake_cookie = {
                        "buvid3": "{}{:05d}infoc".format(uuid.uuid4(), random.randint(1, 99999)),
                        "DedeUserID": "{}".format(random.randint(1, 99999))
                    }
                    for k, v in fake_cookie.items():
                        fake_cookie_str += f'{k}={v}; '
                dynamic_resp = await self.get_dyn_detail_resp(dynamic_id, fake_cookie_str,
                                                              random.choice(CONFIG.UA_LIST),
                                                              dynamic_type=dynamic_type)  # 需要增加假的cookie
                dynamic_detail = await self.solve_dynamic_item_detail(dynamic_id, dynamic_resp)
                if dynamic_type == 2:
                    if dynamic_detail.get('dynamic_id') and dynamic_detail.get('dynamic_id') != str(dynamic_id):
                        get_others_lot_log.error(
                            f'获取动态响应与所求动态值（https://t.bilibili.com/{dynamic_id} ）不同！！{dynamic_detail}')
                        continue
                break
            except:
                # await asyncio.sleep(60)
                get_others_lot_log.critical(f'获取动态响应失败！！！\n{traceback.format_exc()}')
                continue
                # return await self.judge_lottery(dynamic_id, dynamic_type, is_lot_orig)

        return await self.judge_lottery_by_dynamic_resp_dict(dynamic_id, dynamic_detail, dynamic_type, is_lot_orig)

    async def judge_lottery_by_dynamic_resp_dict(self, dynamic_id: str, dynamic_detail: dict, dynamic_type: int = 2,
                                                 is_lot_orig=False):
        """
        判断是否是抽奖 通过已经获取好了的动态id
        :param dynamic_detail: 经过 await self.solve_dynamic_item_detail(dynamic_id_str, single_dynamic_resp) 之后的内容
        :param dynamic_id:
        :param dynamic_type:
        :param is_lot_orig:
        :return:
        """
        async with self.lock:
            if str(dynamic_id) in self.queried_dynamic_id_list or \
                    str(dynamic_id) in self.queriedData.dyidList or \
                    str(dynamic_id) in self.queryingData.dyidList:
                get_others_lot_log.warning(f'当前动态 {dynamic_id} 已经查询过了，不重复查询')
                return
            self.queried_dynamic_id_list.append(str(dynamic_id))
        suffix = ''
        isLot = True
        get_others_lot_log.info(
            f'当前动态：https://t.bilibili.com/{dynamic_id}\ttype={dynamic_type}\n{str(dynamic_detail)[30:180]}')
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
                            if v.get('reserve'):
                                if v.get('reserve').get('desc'):
                                    lot_rid = str(v.get('reserve').get('rid'))
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
                    get_others_lot_log.info(f'https://t.bilibili.com/{dynamic_detail_dynamic_id}?type={dynamic_type}')
                    get_others_lot_log.info('动态内容为空')
                    deadline = None
                premsg = self.BAPI.pre_msg_processing(dynamic_content)
                if comment_count > 300:
                    dynamic_content += await self.get_topcomment_with_proxy(str(dynamic_detail_dynamic_id), str(rid),
                                                                            str(0), _type,
                                                                            author_uid)
                elif str(dynamic_detail.get('type')) == '8':
                    if comment_count > 100:
                        dynamic_content += await self.get_topcomment_with_proxy(str(dynamic_detail_dynamic_id),
                                                                                str(rid),
                                                                                str(0), _type,
                                                                                author_uid)
                if author_uid in self.all_followed_uid:
                    suffix = 'followed_uid'
                ret_url = f'https://t.bilibili.com/{dynamic_detail_dynamic_id}'
                if self.BAPI.zhuanfapanduan(dynamic_content):
                    ret_url += '?tab=2'
                Manual_judge = ''
                if self.manual_reply_judge.call("manual_reply_judge", dynamic_content):
                    Manual_judge = '人工判断'
                high_lights_list = []
                for i in self.highlight_word_list:
                    if i in dynamic_content:
                        high_lights_list.append(i)
                format_list = [ret_url, author_name, str(official_verify_type), str(pub_time), repr(dynamic_content),
                               str(comment_count), str(forward_count), Manual_judge,
                               ';'.join(high_lights_list),
                               OfficialLotType.官方抽奖.value if is_official_lot else OfficialLotType.充电抽奖.value if is_charge_lot else OfficialLotType.预约抽奖.value if is_reserve_lot else '',
                               lot_rid, suffix,
                               premsg,
                               str(deadline)
                               ]
                format_str = '\t'.join(map(str, format_list))
                if re.match(r'.*//@.*', str(dynamic_content), re.DOTALL) is not None:
                    dynamic_content = re.findall(r'(.*?)//@', dynamic_content, re.DOTALL)[0]
                if not is_lot_orig:
                    if self.BAPI.daily_choujiangxinxipanduan(dynamic_content):
                        if comment_count > 2000 or forward_count > 1000:  # 评论或转发超多的就算不是抽奖动态也要加进去凑个数
                            pass
                        else:
                            isLot = False
                async with self.lock:  # 这个地方一定要加锁保证数据的一致性！！！
                    if isLot:
                        self.lottery_dynamic_detail_list.append(format_str)
                        self.queryingData.lotidList.append(str(dynamic_detail_dynamic_id))
                    else:
                        self.useless_info.append(format_str)
                self.queryingData.dyidList.append(str(dynamic_detail_dynamic_id))
                await self.sqlHlper.addDynInfo(
                    TLotdyninfo(
                        dynId=str(dynamic_detail_dynamic_id),
                        dynamicUrl=ret_url,
                        authorName=author_name,
                        up_uid=author_uid,
                        pubTime=datetime.datetime.fromtimestamp(pub_ts),
                        dynContent=dynamic_content,
                        commentCount=comment_count,
                        repostCount=forward_count,
                        highlightWords=';'.join(high_lights_list),
                        officialLotType=OfficialLotType.官方抽奖.value if is_official_lot else OfficialLotType.充电抽奖.value if is_charge_lot else OfficialLotType.预约抽奖.value if is_reserve_lot else '',
                        officialLotId=str(lot_rid),
                        isOfficialAccount=int(official_verify_type if official_verify_type else 0),
                        isManualReply=Manual_judge,
                        isFollowed=int(bool(suffix)),
                        isLot=int(isLot),
                        hashTag=premsg if premsg else '',
                        dynLotRound_id=self.nowRound.lotRound_id,
                        rawJsonStr=rawJSON
                    )
                )
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
                    isRecorded = False
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
                    elif self.BAPI.zhuanfapanduan(orig_dynamic_content):
                        orig_ret_url += '?tab=2'
                    format_list = [orig_ret_url, orig_name, str(orig_official_verify),
                                   str(time.strftime("%Y年%m月%d日 %H:%M", time.localtime(orig_pub_ts))),
                                   repr(orig_dynamic_content),
                                   str(orig_comment_count), str(orig_forward_count), Manual_judge,
                                   ';'.join(high_lights_list),
                                   OfficialLotType.抽奖动态的源动态.value,
                                   lot_rid,
                                   suffix,
                                   premsg,
                                   str(deadline)
                                   ]
                    format_str = '\t'.join(map(str, format_list))

                    async with self.lock:  # 这个地方一定要加锁保证数据的一致性！！！
                        if str(orig_dynamic_id) in self.queriedData.lotidList or \
                                str(orig_dynamic_id) in self.queryingData.lotidList or \
                                str(orig_dynamic_id) in self.queriedData.dyidList or \
                                str(orig_dynamic_id) in self.queryingData.dyidList or \
                                str(orig_dynamic_id) in self.queried_dynamic_id_list:  # 如果源动态已经被判定为抽奖动态过了的话，就不在加入抽奖列表里
                            get_others_lot_log.warning(f'原动态 {orig_ret_url} 已经有抽奖过了，不加入抽奖动态中')
                            isRecorded = True
                        else:
                            # self.queryingData.dyidList.append(str(orig_dynamic_id))
                            # self.queriedData.dyidList.append(str(orig_dynamic_id))
                            # self.queried_dynamic_id_list.append(str(orig_dynamic_id))
                            if isLot:
                                self.lottery_dynamic_detail_list.append(format_str)
                            else:
                                self.useless_info.append(format_str)
                    if not isRecorded:
                        await self.sqlHlper.addDynInfo(
                            TLotdyninfo(
                                dynId=str(orig_dynamic_id),
                                dynamicUrl=orig_ret_url,
                                authorName=orig_name,
                                up_uid=author_uid,
                                pubTime=datetime.datetime.fromtimestamp(orig_pub_ts),
                                dynContent=orig_dynamic_content,
                                commentCount=orig_comment_count,
                                repostCount=orig_forward_count,
                                highlightWords=';'.join(high_lights_list),
                                officialLotType=OfficialLotType.抽奖动态的源动态.value,
                                officialLotId=str(None),
                                isOfficialAccount=int(
                                    orig_official_verify if type(orig_official_verify) is not int else 0),
                                isManualReply=Manual_judge,
                                isFollowed=int(bool(suffix)),
                                isLot=int(isLot),
                                hashTag=premsg if premsg else '',
                                dynLotRound_id=self.nowRound.lotRound_id,
                                rawJsonStr=dynamic_orig
                            )
                        )
                if isLot:
                    if dynamic_detail.get('module_dynamic'):
                        if dynamic_detail.get('module_dynamic').get('additional'):
                            if dynamic_detail.get('module_dynamic').get('additional').get(
                                    'type') == 'ADDITIONAL_TYPE_UGC':
                                ugc = dynamic_detail.get('module_dynamic').get('additional').get('ugc')
                                aid_str = ugc.get('id_str')
                                async with self.lock:  # 这个地方一定要加锁保证数据的一致性！！！
                                    isChecked = aid_str in self.aid_list
                                    if not isChecked:
                                        self.aid_list.append(aid_str)
                                if not isChecked:
                                    new_dyn_resp = await self.get_dyn_detail_resp(dynamic_id=aid_str,
                                                                                  dynamic_type=8,
                                                                                  )
                                    new_dyn_detail = await self.solve_dynamic_item_detail(dynamic_id=aid_str,
                                                                                          dynamic_req=new_dyn_resp
                                                                                          )
                                    await self.judge_lottery_by_dynamic_resp_dict(dynamic_id=aid_str,
                                                                                  dynamic_detail=new_dyn_detail,
                                                                                  dynamic_type=8,
                                                                                  is_lot_orig=True
                                                                                  )
            else:
                get_others_lot_log.warning(f'失效动态：https://t.bilibili.com/{dynamic_id}')
                await self.sqlHlper.addDynInfo(
                    TLotdyninfo(
                        dynId=str(dynamic_id),
                        dynamicUrl=f'https://t.bilibili.com/{dynamic_id}',
                        authorName='',
                        up_uid=-1,
                        pubTime=datetime.datetime.fromtimestamp(0),
                        dynContent='',
                        commentCount=-1,
                        repostCount=-1,
                        highlightWords='',
                        officialLotType='',
                        officialLotId='',
                        isOfficialAccount=-1,
                        isManualReply='',
                        isFollowed=-1,
                        isLot=-1,
                        hashTag='',
                        dynLotRound_id=self.nowRound.lotRound_id,
                        rawJsonStr=dynamic_detail.get('rawJSON')
                    )
                )
        except Exception as e:
            get_others_lot_log.error(f'解析动态失败！！！\n{dynamic_detail}')
            get_others_lot_log.exception(e)

    # endregion

    async def checkDBDyn(self):
        allDyn = await self.sqlHlper.getAllDynByLotRound(self.nowRound.lotRound_id)
        useless_dynurl_list = [x.split('\t')[0] for x in self.useless_info]
        lottery_dynamicurl_list = [x.split('\t')[0] for x in self.lottery_dynamic_detail_list]
        for i in allDyn:
            format_list = [i.dynamicUrl, i.authorName, str(i.isOfficialAccount),
                           str(i.pubTime.strftime('%Y年%m月%d日 %H:%M')),
                           repr(i.dynContent),
                           str(i.commentCount), str(i.repostCount), i.isManualReply,
                           i.highlightWords,
                           i.officialLotType,
                           i.officialLotId, i.isFollowed,
                           i.hashTag,
                           None
                           ]
            if i.isLot == 1:
                if i.dynamicUrl not in lottery_dynamicurl_list:
                    format_str = '\t'.join(map(str, format_list))
                    self.lottery_dynamic_detail_list.append(format_str)
            else:
                if i.dynamicUrl not in useless_dynurl_list:
                    format_str = '\t'.join(map(str, format_list))
                    self.useless_info.append(format_str)

    def write_in_log(self):

        a = []
        a.extend(self.queriedData.dyidList)
        a.extend(self.queryingData.dyidList)
        a = list(set(a))[-10000:]
        writeIntoFile(a, FileMap.get_dyid, 'w', ',')

        a = []
        a.extend(self.queriedData.lotidList)
        a.extend(self.queryingData.lotidList)
        a = list(set(a))[-10000:]
        writeIntoFile(a, FileMap.lot_dyid, 'w', ',')

        json_dict = dict()
        self.queryingData.queryUserInfo = dict(
            sorted(self.queryingData.queryUserInfo.items(), key=lambda x: x[1].update_num))
        for k, v in self.queryingData.queryUserInfo.items():
            json_dict.update({k: v.__dict__})
        writeIntoFile([json.dumps(json_dict, indent=4)], FileMap.获取过动态的b站用户, 'w', '\n')

        writeIntoFile(self.lottery_dynamic_detail_list, FileMap.过滤抽奖信息, 'w', '\n')
        a = [x for x in self.lottery_dynamic_detail_list]
        a.append(datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M'))
        a.append("")
        writeIntoFile(a, FileMap.所有抽奖信息, 'a+', '\n')

        writeIntoFile(self.useless_info, FileMap.无用信息, 'w', '\n')
        a = [x for x in self.useless_info]
        a.append(datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M'))
        a.append("")
        writeIntoFile(a, FileMap.所有无用信息, 'a+', '\n')
        # FileMap.本轮检查的动态id

    async def main(self):
        latest_round = await self.sqlHlper.getLatestRound()
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
        get_others_lot_log.info(f'当前获取别人抽奖轮次：{latest_round.__dict__}')
        await self.sqlHlper.addLotMainInfo(latest_round)
        self.login_check(self.cookie3, self.ua3)
        self.all_followed_uid = self.get_attention(self.uid3, self.cookie3, self.ua3)
        get_others_lot_log.info(f'共{len(self.all_followed_uid)}个关注')
        self.fetchGiteeInfo()
        await self.getLastestScrapyInfo()

        GOTO_check_lot_dyn_id_list: list[str] = self.getGiteeLotdyid()  # 添加gitee动态id

        GOTO_check_lot_dyn_id_list.extend(await self.getAllSpaceDynId(self.queryingData.uidlist, False))  # 添加用户空间动态id
        pub_lot_uid_list = [x.uid for x in self.pub_lot_user_info_list]
        pub_lot_uid_list = list(set(pub_lot_uid_list))  # 去个重先

        print(f'总共要获取{len(pub_lot_uid_list)}个发起抽奖用户的空间！')
        GOTO_check_lot_dyn_id_list.extend(await self.getAllSpaceDynId(pub_lot_uid_list, True))

        GOTO_check_lot_dyn_id_list = list(set(GOTO_check_lot_dyn_id_list))  # 去个重先
        print(f'过滤前{len(GOTO_check_lot_dyn_id_list)}条待检查动态')
        GOTO_check_lot_dyn_id_list = [x for x in GOTO_check_lot_dyn_id_list if x not in self.queriedData.dyidList]
        print(f'过滤后{len(GOTO_check_lot_dyn_id_list)}条待检查动态')
        writeIntoFile(GOTO_check_lot_dyn_id_list, FileMap.本轮检查的动态id, 'w', ',')

        await self.thread_judgedynamic(GOTO_check_lot_dyn_id_list)
        await self.checkDBDyn()  # 从数据库里面吧本轮的抽奖动态重新检查一遍

        self.nowRound.allNum = len(GOTO_check_lot_dyn_id_list)
        self.nowRound.lotNum = len(self.lottery_dynamic_detail_list)
        self.nowRound.uselessNum = len(self.useless_info)
        self.nowRound.isRoundFinished = 1
        self.write_in_log()
        await self.sqlHlper.addLotMainInfo(self.nowRound)


class GET_OTHERS_LOT_DYN:
    """
        获取更新的抽奖，如果时间在1天之内，那么直接读取文件获取结果，将结果返回回去
    """

    def __init__(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.is_getting_dyn_flag_lock = asyncio.Lock()
        self.save_lock = asyncio.Lock()
        if os.path.exists(FileMap.get_dyn_ts):
            with open(FileMap.get_dyn_ts, 'r', encoding='utf-8') as f:
                try:
                    self.get_dyn_ts: int = int(f.read())
                except Exception as e:
                    get_others_lot_log.error(f'读取上次获取动态时间戳失败！\n{e}')
                    self.get_dyn_ts = 0
                if not isinstance(self.get_dyn_ts, int):
                    self.get_dyn_ts: int = 0
        else:
            self.get_dyn_ts: int = 0
        self.is_getting_dyn_flag = False

    async def save_now_get_dyn_ts(self, ts: int):
        async with self.save_lock:
            with open(FileMap.get_dyn_ts, 'w', encoding='utf-8') as f:
                self.get_dyn_ts = ts
                f.writelines(f'{ts}')

    # region 主函数 （包括获取普通新抽奖，推送官方抽奖，推送大奖，推送预约抽奖）
    async def get_new_dyn(self) -> list[str]:
        """
        主函数，获取一般最新的抽奖
        :return:
        """
        while self.is_getting_dyn_flag:
            await asyncio.sleep(30)
        if os.path.exists(FileMap.get_dyn_ts):
            with open(FileMap.get_dyn_ts, 'r', encoding='utf-8') as f:
                try:
                    self.get_dyn_ts: int = int(f.read())
                    if not isinstance(self.get_dyn_ts, int):
                        self.get_dyn_ts: int = 0
                except:
                    self.get_dyn_ts: int = 0
        else:
            self.get_dyn_ts: int = 0
        get_others_lot_log.debug(f'上次获取别人B站动态空间抽奖时间：{datetime.datetime.fromtimestamp(self.get_dyn_ts)}')
        if int(time.time()) - self.get_dyn_ts >= 0.8 * 24 * 3600:
            async with self.is_getting_dyn_flag_lock:
                self.is_getting_dyn_flag = True
            ___ = GetOthersLotDyn()
            await ___.main()
            await self.save_now_get_dyn_ts(int(time.time()))
            async with self.is_getting_dyn_flag_lock:
                self.is_getting_dyn_flag = False

        return self.solve_lot_csv()

    def get_official_lot_dyn(self, limit=7) -> list[str]:
        """
        返回官方抽奖信息，结尾是tab=1
        :param limit 限制转发数量最高的7个
        :return:
        """

        def try_parse_int(string: str) -> int:
            if string != 'None':
                return int(string)
            else:
                return 0

        def is_official_lot(lot_det: str):
            """
            过滤抽奖函数，同时设置官方抽奖的阈值，只抽抽奖人数多的官方抽奖
            :param lot_det:
            :return:
            """
            lot_det_sep = lot_det.split('\t')
            pubtime_str = lot_det_sep[3]
            comment_count_str = lot_det_sep[5]
            rep_count_str = lot_det_sep[6]
            lot_type = lot_det_sep[9]
            dt = datetime.datetime.strptime(pubtime_str, '%Y年%m月%d日 %H:%M')
            if dt.year < 2000:
                return False
            pub_ts = int(datetime.datetime.timestamp(datetime.datetime.strptime(pubtime_str, '%Y年%m月%d日 %H:%M')))
            if int(time.time()) - pub_ts > 1 * 30 * 24 * 3600:  # 超过一个月的不要
                return False
            official_verify = lot_det_sep[2]
            official_lot_desc = lot_det_sep[9]
            if official_lot_desc == OfficialLotType.官方抽奖.value:
                if int(rep_count_str) < 200:
                    if int(self.get_dyn_ts - pub_ts) <= 2 * 3600:  # 获取时间和发布时间间隔小于2小时的不按照评论转发数量过滤
                        return True
                    return False
                return True
            return False

        all_lot_det = []
        with open(FileMap.过滤抽奖信息, 'r', encoding='utf-8') as f:
            for i in f.readlines():
                all_lot_det.append(i.strip())
        filtered_list: list[str] = list(filter(is_official_lot, all_lot_det))
        filtered_list.sort(key=lambda x: try_parse_int(x.split("\t")[5]), reverse=True)
        if filtered_list:
            self.push_lot_csv(f"官方抽奖信息", filtered_list[0:10])  # {datetime.datetime.now().strftime('%m月%d日')}
        filtered_list.sort(key=lambda x: x.split("\t")[6], reverse=True)  # 按照转发数量降序排序
        ret_list = [x.split('\t')[0].replace('?tab=2', '') + '?tab=1' for x in filtered_list]
        return ret_list[:limit]

    def get_unignore_Big_lot_dyn(self) -> list[str]:
        """
        获取大奖
        :return:
        """
        """
                解析并过滤抽奖的csv，直接返回动态链接的列表
                :return:
                """

        def try_parse_int(string: str) -> int:
            if string != 'None':
                return int(string)
            else:
                return 0

        all_lot_det = []
        with open(FileMap.过滤抽奖信息, 'r', encoding='utf-8') as f:
            for i in f.readlines():
                all_lot_det.append(i.strip())
        filtered_list: list = list(filter(self.is_need_lot, all_lot_det))
        filtered_list.sort(key=lambda x: try_parse_int(x.split("\t")[5]), reverse=True)
        filtered_list.sort(key=lambda x: x.split("\t")[0], reverse=True)  # 按照降序排序
        dyn_content_list = [x.split('\t')[4] for x in filtered_list]
        big_lot_list = big_lot_predict(dyn_content_list)
        ret_filtered_list = []
        for i in range(len(dyn_content_list)):
            if big_lot_list[i] == 1:
                ret_filtered_list.append(filtered_list[i])
        if ret_filtered_list:
            self.push_lot_csv(f"必抽的大奖", ret_filtered_list[0:10])  # {datetime.datetime.now().strftime('%m月%d日')}
        ret_list = [x.split('\t')[0] for x in ret_filtered_list]
        return ret_list

    async def get_unignore_reserve_lot_space(self) -> list[TUpReserveRelationInfo]:
        from opus新版官方抽奖.预约抽奖.db.sqlHelper import SqlHelper as sqh
        mysq = sqh()
        all_lots = await mysq.get_all_available_reserve_lotterys()
        recent_lots: list[TUpReserveRelationInfo] = [x for x in all_lots if
                                                     x.etime and x.etime - int(time.time()) < 2 * 3600 * 24]
        reserve_infos: list[str] = [x.text for x in recent_lots]
        is_lot_list = big_reserve_predict(reserve_infos)
        ret_list = []
        ret_info_list = []
        for i in range(len(recent_lots)):
            if is_lot_list[i] == 1:
                ret_info_list.append(
                    ' '.join([f'https://space.bilibili.com/{recent_lots[i].upmid}/dynamic', recent_lots[i].text]))
                ret_list.append(recent_lots[i])
        if ret_info_list:
            pushme(f"必抽的预约抽奖", '\n'.join(ret_info_list[0:10]),
                   'text')
        return ret_list

    # endregion

    # region 推送抽奖用的函数
    def push_lot_csv(self, title: str, content_list: list):
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
            content_sep = i.split('\t')
            dynurl = content_sep[0]
            nickname = content_sep[1]
            official_verify = content_sep[2]
            pubtime = content_sep[3]
            dyncontent = eval(
                content_sep[4].replace('\\r', '').replace('|', '&#124;').replace('\\n', '<br>').replace('&', '&amp;'))
            comment_count = content_sep[5]
            rep_count = content_sep[6]
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
    def is_need_lot(self, lot_det: str):
        """
        过滤抽奖函数，只保留一般抽奖
        :param lot_det:
        :return:
        """
        lot_det_sep = lot_det.split('\t')
        pubtime_str = lot_det_sep[3]
        comment_count_str = lot_det_sep[5]
        rep_count_str = lot_det_sep[6]
        lot_type = lot_det_sep[9]
        dt = datetime.datetime.strptime(pubtime_str, '%Y年%m月%d日 %H:%M')
        if dt.year < 2000:
            return False
        pub_ts = int(datetime.datetime.timestamp(datetime.datetime.strptime(pubtime_str, '%Y年%m月%d日 %H:%M')))
        official_verify = lot_det_sep[2]
        official_lot_desc = lot_det_sep[9]
        if lot_type == OfficialLotType.抽奖动态的源动态.value:
            if int(time.time()) - pub_ts >= 20 * 24 * 3600:  # 抽奖动态的源动态放宽到20天
                return False
            return True
        if official_lot_desc in [OfficialLotType.充电抽奖.value, OfficialLotType.预约抽奖.value,
                                 OfficialLotType.官方抽奖.value]:
            return False
        if int(self.get_dyn_ts - pub_ts) <= 2 * 3600:  # 获取时间和发布时间间隔小于2小时的不按照评论转发数量过滤
            return True
        if comment_count_str != 'None':
            if int(comment_count_str) < 20 and int(rep_count_str) < 20:
                return False
        if official_verify != '1':
            if int(time.time()) - pub_ts >= 10 * 24 * 3600:  # 超过10天的不抽
                return False
        else:
            if int(time.time()) - pub_ts >= 15 * 24 * 3600:  # 官方号放宽到15天
                return False
        return True

    def solve_lot_csv(self) -> list[str]:
        """
        解析并过滤抽奖的csv，直接返回动态链接的列表
        :return:
        """

        def try_parse_int(string: str) -> int:
            if string != 'None':
                return int(string)
            else:
                return 0

        all_lot_det = []
        with open(FileMap.过滤抽奖信息, 'r', encoding='utf-8') as f:
            for i in f.readlines():
                all_lot_det.append(i.strip())
        filtered_list: list = list(filter(self.is_need_lot, all_lot_det))
        filtered_list.sort(key=lambda x: try_parse_int(x.split("\t")[5]), reverse=True)
        self.push_lot_csv(f"动态抽奖信息", filtered_list[0:10])  # {datetime.datetime.now().strftime('%m月%d日')}
        filtered_list.sort(key=lambda x: x.split("\t")[0], reverse=True)  # 按照降序排序
        ret_list = [x.split('\t')[0] for x in filtered_list]
        ret_list = list(set(ret_list))
        ret_list.sort(reverse=True)
        return ret_list

    # endregion


if __name__ == '__main__':
    b = GET_OTHERS_LOT_DYN()
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(b.get_new_dyn())
    print(b.solve_lot_csv())
    pass
    # b = GET_OTHERS_LOT_DYN()
    # c = b.get_unignore_reserve_lot_space()
    # print(c)
