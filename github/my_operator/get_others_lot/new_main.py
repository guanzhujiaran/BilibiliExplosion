import asyncio
import datetime
import gc
import json
import math
import os
import random
import re
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Union, List
import subprocess
from functools import partial
from fastapi接口.service.MQ.base.MQClient.BiliLotDataPublisher import BiliLotDataPublisher
from grpc获取动态.grpc.bapi.biliapi import proxy_req, get_space_dynamic_req_with_proxy, \
    get_polymer_web_dynamic_detail
from opus新版官方抽奖.Model.BaseLotModel import BaseSuccCounter, ProgressCounter

subprocess.Popen = partial(subprocess.Popen, encoding="utf-8")
from py_mini_racer import MiniRacer
from fastapi接口.log.base_log import get_others_lot_logger as get_others_lot_log
from CONFIG import CONFIG
from github.my_operator.get_others_lot.Tool.newSqlHelper.models import TLotuserspaceresp, TLotdyninfo, TLotuserinfo, \
    TLotmaininfo
from opus新版官方抽奖.预约抽奖.db.models import TUpReserveRelationInfo
from utl.pushme.pushme import pushme
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import Bilibili_methods.all_methods
from github.my_operator.get_others_lot.Tool.newSqlHelper.SqlHelper import SqlHelper
from github.my_operator.get_others_lot.svmJudgeBigLot.judgeBigLot import big_lot_predict
from github.my_operator.get_others_lot.svmJudgeBigReserve.judgeReserveLot import big_reserve_predict


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
        646327721,
        3546605886114075
    ])
    dyidList: list[str] = field(default_factory=list)  # 动态id
    lotidList: list[str] = field(default_factory=list)  # 抽奖id


class FileMap(str, Enum):
    current_file_path: str = os.path.dirname(os.path.abspath(__file__))
    github_bili_upload: str = os.path.join(current_file_path, '../../bili_upload')

    _log_path = os.path.join(current_file_path, 'log/')
    lot_dyid = os.path.join(_log_path, 'lot_dyid.txt')
    get_dyid = os.path.join(_log_path, 'get_dyid.txt')  # 最后写入文件记录
    uidlist_json = os.path.join(_log_path, 'uidlist.json')
    本轮检查的动态id = os.path.join(_log_path, '本轮检查的动态id.txt')
    所有抽奖信息 = os.path.join(_log_path, '所有过滤抽奖信息.csv')
    所有无用信息 = os.path.join(_log_path, '所有无用信息.csv')

    _result_path = os.path.join(current_file_path, 'result/')
    过滤抽奖信息 = os.path.join(_result_path, '过滤抽奖信息.csv')
    无用信息 = os.path.join(_result_path, '无用信息.csv')

    获取过动态的b站用户 = os.path.join(current_file_path, '获取过动态的b站用户.json')
    get_dyn_ts = os.path.join(current_file_path, 'get_dyn_ts.txt')


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


class GetOthersLotDynRobot:
    """
    获取其他人的抽奖动态
    """

    def __init__(self):
        # 上一轮抽奖是否结束
        self.isPreviousRoundFinished = False
        self.sem = asyncio.Semaphore(30)
        self.space_sem = asyncio.Semaphore(30)
        self.nowRound: TLotmaininfo = TLotmaininfo()
        self.aid_list = []
        self.fake_cookie = True
        self.sqlHlper = SqlHelper
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
        ctx = MiniRacer()
        self.manual_reply_judge = ctx.eval("""
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
                    """, )
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

        self.space_succ_counter = ProgressCounter()
        self.dyn_succ_counter = ProgressCounter()

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
        os.system(f'cd "{FileMap.github_bili_upload.value}" && git fetch --all && git reset --hard && git pull')

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
        return []
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
            get_others_lot_log.info(f'上次获取的动态：{self.queriedData.queryUserInfo}')
        except Exception as e:
            get_others_lot_log.exception(f'加载【获取过动态的b站用户】数据失败！')

        if os.path.exists(FileMap.uidlist_json):
            try:
                with open(FileMap.uidlist_json) as f:
                    self.queryingData.uidlist = json.load(f).get('uidlist')
                    self.queryingData.uidlist = list(set(self.queryingData.uidlist))
            except Exception as e:
                get_others_lot_log.exception(f'获取抽奖用户uid列表失败，使用默认配置！{e}')
        else:
            get_others_lot_log.exception(f'抽奖用户uid列表文件不存在，使用默认配置！')

        if os.path.exists(FileMap.get_dyid):
            try:
                with open(FileMap.get_dyid) as f:
                    for i in f.read().split(','):
                        if i.strip():
                            self.queriedData.dyidList.append(i.strip())
            except Exception as e:
                get_others_lot_log.exception(f'获取get_dyid列表失败，使用默认配置！{e}')
        else:
            get_others_lot_log.exception(f'获取get_dyid列表文件不存在，使用默认配置！')

        if os.path.exists(FileMap.lot_dyid):
            try:
                with open(FileMap.lot_dyid) as f:
                    for i in f.read().split(','):
                        if i.strip():
                            self.queriedData.lotidList.append(i.strip())
            except Exception as e:
                get_others_lot_log.warning(f'获取lot_dyid列表失败，使用默认配置！{e}')
        else:
            get_others_lot_log.exception(f'获取lot_dyid列表文件不存在，使用默认配置！')

    def getGiteeLotdyid(self) -> list[str]:
        path = FileMap.github_bili_upload.value
        datanames = os.listdir(path)
        path_dir_name = []
        for i in datanames:
            if str.isdigit(i):
                path_dir_name.append(i)

        effective_files_content_list = []

        for i in path_dir_name:
            with open(os.path.join(FileMap.github_bili_upload.value, f'{i}/dyid.txt'), 'r', encoding='utf-8') as f:
                effective_files_content_list.append(''.join(f.readlines()))
        for i in effective_files_content_list:
            self.queriedData.gitee_dyn_id_list = self.solveGiteeFileContent(i, self.queriedData.dyidList)  # 记录动态id
        get_others_lot_log.info(
            f'共获取{len(path_dir_name)}个文件，新增{len(self.queriedData.gitee_dyn_id_list)}条抽奖！')
        return self.queriedData.gitee_dyn_id_list

    # region 获取uidlist中的空间动态

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
            get_others_lot_log.error(f'cards_json为None\t{json.dumps(space_req_dict)}')
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
        first_get_dynamic_flag = True
        origin_offset = 0
        lot_user_info: TLotuserinfo = await self.sqlHlper.getLotUserInfoByUid(uid)

        if secondRound:
            newest_space_offset = await self.sqlHlper.getNewestSpaceDynInfoByUid(uid)
            if newest_space_offset:
                dynamic_calculated_ts = self.calculate_pub_ts_by_dynamic_id(newest_space_offset)
                updatetime = await self.sqlHlper.get_lot_user_info_updatetime_by_uid(uid)
                updatetime_ts = updatetime.timestamp() if updatetime else 0
                if int(time.time() - dynamic_calculated_ts) < 2 * 3600 or int(time.time() - updatetime_ts) < 2 * 3600:
                    get_others_lot_log.info(f'{uid} 距离上次获取抽奖不足2小时，跳过')
                    return
        if lot_user_info:
            if not self.isPreviousRoundFinished:  # 如果上一轮抽奖没有完成
                origin_offset = lot_user_info.latestFinishedOffset
        else:
            lot_user_info = TLotuserinfo(
                uid=uid,
                isPubLotUser=isPubLotUser
            )
            await self.sqlHlper.addLotUserInfo(lot_user_info)
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
            if origin_offset != "" and first_get_dynamic_flag:
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
                dyreq_dict = await get_space_dynamic_req_with_proxy(uid, offset)
                dyreq_dict = await addSpaceCardToDb(dyreq_dict)
            try:
                if dynamic_items := dyreq_dict.get('data').get('items'):
                    uname = dynamic_items[0].get('modules').get('module_author').get('name')
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
                    if first_get_dynamic_flag:
                        if self.queriedData.queryUserInfo.get(str(uid)):
                            update_num = len(repost_dynamic_id_list) - len(
                                set(repost_dynamic_id_list) & set(
                                    self.queriedData.queryUserInfo.get(str(uid)).latest_dyid_list))
                        else:
                            update_num = len(repost_dynamic_id_list)
                        self.queryingData.queryUserInfo.update(
                            {str(uid): user_space_dyn_detail(repost_dynamic_id_list[0:10], update_num)})
                        first_get_dynamic_flag = False
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
                                 updatetime=lot_user_info.updatetime,
                                 isUserSpaceFinished=0,
                                 offset=offset,
                                 latestFinishedOffset=lot_user_info.latestFinishedOffset,
                                 isPubLotUser=isPubLotUser
                                 ))
                if len(timelist) == 0:
                    get_others_lot_log.error(f'timelist is empty\t{json.dumps(dyreq_dict)}')
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
            updatetime=datetime.datetime.now() if origin_offset == "" else lot_user_info.updatetime,
            isUserSpaceFinished=1,
            offset=offset,
            latestFinishedOffset=offset if not secondRound else lot_user_info.latestFinishedOffset,
            isPubLotUser=isPubLotUser
        ))
        # if 1==1:
        #     return
        if origin_offset != "" and not secondRound:
            self.queriedData.queryUserInfo.update({
                str(uid): self.queryingData.queryUserInfo.get(str(uid))
            })
            await self.get_user_space_dynamic_id(uid, secondRound=True, isPubLotUser=isPubLotUser)
        if uid in self.queryingData.uidlist:
            if n <= 4 and time.time() - timelist[-1] >= self.SpareTime and secondRound == False:
                # self.uidlist.remove(uid)
                get_others_lot_log.critical(
                    f'{uid}\t当前UID获取到的动态太少，前往：\nhttps://space.bilibili.com/{uid}\n查看详情')
            if not secondRound:
                self.space_succ_counter.succ_count += 1
        self.space_sem.release()

    async def getAllSpaceDynId(self, uidlist=None, isPubLotUser=False) -> list[str]:
        if uidlist is None:
            uidlist = self.queryingData.uidlist
        uidlist = list(set(uidlist))
        tasks = []
        self.space_succ_counter.total_num = len(uidlist)
        for i in uidlist:
            await self.space_sem.acquire()
            task = asyncio.create_task(self.get_user_space_dynamic_id(i, isPubLotUser=isPubLotUser))
            tasks.append(task)
        # while 1:
        #     task_doing = [i for i in tasks if not i.done()]
        #     get_others_lot_log.info(f'当前正在获取用户空间的任务进度【{len(task_doing)}/{len(tasks)}】')
        #     if len(task_doing) == 0:
        #         break
        #     else:
        #         await asyncio.sleep(10)
        # await asyncio.gather(*tasks)
        while True:
            task_doing = [i for i in tasks if not i.done()]
            if len(task_doing) == 0:
                break
            else:
                get_others_lot_log.debug(
                    f'当前正在获取用户空间的任务数量：{len(task_doing)}（正在执行的数量）/{len(tasks)}（所有任务数量）')
            await asyncio.sleep(5)
        await asyncio.gather(*tasks, return_exceptions=False)
        self.space_succ_counter.is_running = False
        return self.spaceRecordedDynamicIdList

    # endregion
    # region 判断单个动态是否是抽奖动态

    async def thread_judgedynamic(self, write_in_list: List[int | str]):
        async def judge_single_dynamic(dynamic_id):
            async with self.sem:
                new_resp = await self.get_dyn_detail_resp(dynamic_id)
                dynamic_detail = await self.solve_dynamic_item_detail(dynamic_id, new_resp)
                await self.judge_lottery_by_dynamic_resp_dict(dynamic_id, dynamic_detail)
                self.dyn_succ_counter.succ_count += 1

        self.dyn_succ_counter.total_num = len(write_in_list)
        get_others_lot_log.info('多线程获取动态')
        task_list = []
        for i in write_in_list:
            if i is None:
                get_others_lot_log.error(f'动态id获取为None:{i}')
                self.dyn_succ_counter.succ_count += 1
                continue
            tk = asyncio.create_task(judge_single_dynamic(i))
            task_list.append(tk)
        # while True:
        #     task_doing = [i for i in task_list if not i.done()]
        #     if len(task_doing) == 0:
        #         break
        #     else:
        #         get_others_lot_log.debug(f'当前正在获取动态的任务数量：{len(task_doing)}/{len(task_list)}')
        #     await asyncio.sleep(10)
        get_dyn_resp_result = await asyncio.gather(*task_list, return_exceptions=False)
        get_others_lot_log.info(f'获取动态报错结果：{[x for x in get_dyn_resp_result if x]}')
        self.dyn_succ_counter.is_running = False

    async def get_dyn_detail_resp(self, dynamic_id, dynamic_type=2) -> dict:
        """
        返回{
                        'code':0,
                        'data':{
                            "item":dynamic_req
                        }
                    }这样的dict
        :param dynamic_id:
        :param dynamic_type:
        :return:
        """
        get_others_lot_log.debug(f'正在获取动态响应：{dynamic_id}')
        dynamic_req = None
        isDynExist = await self.sqlHlper.isExistDynInfoByDynId(dynamic_id)
        if isDynExist:
            # get_others_lot_log.critical(f'存在过的动态！！！{isDynExist.__dict__}')
            if isDynExist.officialLotType != OfficialLotType.抽奖动态的源动态.value:
                dynamic_req = isDynExist.rawJsonStr
                if dynamic_req is not None:
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
            if dynamic_req is not None:
                dynamic_req = {
                    'code': 0,
                    'data': {
                        "item": dynamic_req
                    }
                }
        try:
            if not dynamic_req:
                if dynamic_type != 2:
                    dynamic_req = await get_polymer_web_dynamic_detail(rid=dynamic_id, dynamic_type=dynamic_type)
                else:
                    dynamic_req = await get_polymer_web_dynamic_detail(dynamic_id=dynamic_id, )
        except Exception as e:
            get_others_lot_log.exception(e)
            return await self.get_dyn_detail_resp(dynamic_id, )
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
        get_others_lot_log.debug(f'正在解析动态详情：{dynamic_id}')
        try:
            if dynamic_req.get('code') == 4101131 or dynamic_req.get('data') is None:
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
                get_others_lot_log.critical(f"获取的动态信息与需要的动态不符合！！！\t{dynamic_data}")
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
            get_others_lot_log.exception(
                f'解析动态失败！\thsolve_dynamic_item_detailttps://t.bilibili.com/{dynamic_id}\t{dynamic_req}\t{e}')
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
            get_others_lot_log.exception(f"解析动态失败！\n{dynamic_req}\n{e}")
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
            'referer': f'https://t.bilibili.com/{rid}?type={_type}',
            # 'connection': 'close',
            'user-agent': CONFIG.rand_ua,
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
            pinglunreq = await proxy_req.request_with_proxy(method="GET", url=pinglunurl, data=pinglundata,
                                                            headers=pinglunheader, mode='single', hybrid='1')
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
                dynamic_resp = await self.get_dyn_detail_resp(dynamic_id,
                                                              dynamic_type=dynamic_type)  # 需要增加假的cookie
                dynamic_detail = await self.solve_dynamic_item_detail(dynamic_id, dynamic_resp)
                if dynamic_type == 2:
                    if dynamic_detail.get('dynamic_id') and dynamic_detail.get('dynamic_id') != str(dynamic_id):
                        get_others_lot_log.error(
                            f'获取动态响应与所求动态值（https://t.bilibili.com/{dynamic_id} ）不同！！{dynamic_detail}')
                        continue
                break
            except Exception as e:
                # await asyncio.sleep(60)
                get_others_lot_log.exception(f'获取动态响应失败！！！\n{e}')
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
        get_others_lot_log.debug(f'正在判断抽奖动态：{dynamic_id}')
        async with self.lock:
            if str(dynamic_id) in self.queried_dynamic_id_list or \
                    str(dynamic_id) in self.queriedData.dyidList or \
                    str(dynamic_id) in self.queryingData.dyidList:
                get_others_lot_log.info(f'当前动态 {dynamic_id} 已经查询过了，不重复查询')
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
                if self.manual_reply_judge(dynamic_content):
                    Manual_judge = '人工判断'
                high_lights_list = []
                for i in self.highlight_word_list:
                    if i in dynamic_content:
                        high_lights_list.append(i)
                format_list = [
                    ret_url,
                    author_name,
                    str(official_verify_type),
                    str(pub_time),
                    repr(dynamic_content),
                    str(comment_count),
                    str(forward_count),
                    Manual_judge,
                    ';'.join(high_lights_list),
                    OfficialLotType.官方抽奖.value if is_official_lot else OfficialLotType.充电抽奖.value if is_charge_lot else OfficialLotType.预约抽奖.value if is_reserve_lot else '',
                    lot_rid,
                    suffix,
                    str(premsg).replace('\t', '').replace('\n', ''),
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
                official_lot_type = OfficialLotType.官方抽奖.value if is_official_lot else OfficialLotType.充电抽奖.value if is_charge_lot else OfficialLotType.预约抽奖.value if is_reserve_lot else ''
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
                        officialLotType=official_lot_type,
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

                try:
                    if is_official_lot or is_reserve_lot or is_charge_lot:
                        await self.solve_official_lot_data(str(dynamic_detail_dynamic_id), official_lot_type, lot_rid)
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
                    format_list = [
                        orig_ret_url,
                        orig_name,
                        str(orig_official_verify),
                        str(time.strftime("%Y年%m月%d日 %H:%M", time.localtime(orig_pub_ts))),
                        repr(orig_dynamic_content),
                        str(orig_comment_count),
                        str(orig_forward_count),
                        Manual_judge,
                        ';'.join(high_lights_list),
                        OfficialLotType.抽奖动态的源动态.value,
                        lot_rid,
                        suffix,
                        str(premsg).replace('\t', '').replace('\n', ''),
                        str(deadline)
                    ]
                    format_str = '\t'.join(map(str, format_list))

                    async with self.lock:  # 这个地方一定要加锁保证数据的一致性！！！
                        if str(orig_dynamic_id) in self.queriedData.lotidList or \
                                str(orig_dynamic_id) in self.queryingData.lotidList or \
                                str(orig_dynamic_id) in self.queriedData.dyidList or \
                                str(orig_dynamic_id) in self.queryingData.dyidList or \
                                str(orig_dynamic_id) in self.queried_dynamic_id_list:  # 如果源动态已经被判定为抽奖动态过了的话，就不在加入抽奖列表里
                            get_others_lot_log.info(f'原动态 {orig_ret_url} 已经有抽奖过了，不加入抽奖动态中')
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
                                isOfficialAccount=orig_official_verify if type(orig_official_verify) is int else 0,
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
                get_others_lot_log.info(f'失效动态：https://t.bilibili.com/{dynamic_id}')
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
            get_others_lot_log.exception(f'解析动态失败！！！{e}\n{dynamic_detail}')

    # endregion
    async def solve_official_lot_data(self,
                                      dyn_id: Union[str, int],
                                      lot_type: OfficialLotType | str,
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
            if lot_type == OfficialLotType.官方抽奖:
                business_type = 1
                business_id = dyn_id
            elif lot_type == OfficialLotType.预约抽奖:
                business_type = 10
                business_id = official_lot_id
            elif lot_type == OfficialLotType.充电抽奖:
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

    async def checkDBDyn(self, lot_round_id: int = None):
        if lot_round_id is None:
            lot_round_id = self.nowRound.lotRound_id
        if lot_round_id is None:
            return
        allDyn: [TLotdyninfo] = await self.sqlHlper.getAllDynByLotRound(lot_round_id)
        official_lots: [TLotdyninfo] = [x for x in allDyn if x.officialLotType == OfficialLotType.官方抽奖
                                        or x.officialLotType == OfficialLotType.预约抽奖
                                        or x.officialLotType == OfficialLotType.充电抽奖
                                        ]
        await asyncio.gather(
            *[self.solve_official_lot_data(x.dynId, x.officialLotType, x.officialLotId) for x in official_lots])

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

        get_others_lot_log.debug(f'总共要获取{len(pub_lot_uid_list)}个发起抽奖用户的空间！')
        GOTO_check_lot_dyn_id_list.extend(await self.getAllSpaceDynId(pub_lot_uid_list, True))

        GOTO_check_lot_dyn_id_list = list(set(GOTO_check_lot_dyn_id_list))  # 去个重先
        get_others_lot_log.debug(f'过滤前{len(GOTO_check_lot_dyn_id_list)}条待检查动态')
        GOTO_check_lot_dyn_id_list = [x for x in GOTO_check_lot_dyn_id_list if x not in self.queriedData.dyidList]
        get_others_lot_log.debug(f'过滤后{len(GOTO_check_lot_dyn_id_list)}条待检查动态')
        writeIntoFile(GOTO_check_lot_dyn_id_list, FileMap.本轮检查的动态id, 'w', ',')

        await self.thread_judgedynamic(GOTO_check_lot_dyn_id_list)
        await self.checkDBDyn()  # 从数据库里面吧本轮的抽奖动态重新检查一遍

        self.nowRound.allNum = len(GOTO_check_lot_dyn_id_list)
        self.nowRound.lotNum = len(self.lottery_dynamic_detail_list)
        self.nowRound.uselessNum = len(self.useless_info)
        self.nowRound.isRoundFinished = 1
        self.write_in_log()
        await self.sqlHlper.addLotMainInfo(self.nowRound)
        # 抽奖获取结束 尝试将这一轮获取到的非图片抽奖添加进数据库


class GetOthersLotDyn:
    """
        获取更新的抽奖，如果时间在1天之内，那么直接读取文件获取结果，将结果返回回去
    """

    def __init__(self):
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

        self.robot: GetOthersLotDynRobot | None = None

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
        while 1:
            async with self.is_getting_dyn_flag_lock:
                is_getting_dyn_flag = self.is_getting_dyn_flag
            if is_getting_dyn_flag:
                await asyncio.sleep(30)
            else:
                break
        if os.path.exists(FileMap.get_dyn_ts):
            with open(FileMap.get_dyn_ts, 'r', encoding='utf-8') as f:
                try:
                    self.get_dyn_ts: int = int(f.read())
                    if not isinstance(self.get_dyn_ts, int):
                        self.get_dyn_ts: int = 0
                except Exception as e:
                    self.get_dyn_ts: int = 0
        else:
            self.get_dyn_ts: int = 0
        get_others_lot_log.debug(f'上次获取别人B站动态空间抽奖时间：{datetime.datetime.fromtimestamp(self.get_dyn_ts)}')
        if int(time.time()) - self.get_dyn_ts >= 0.8 * 24 * 3600:
            async with self.is_getting_dyn_flag_lock:
                self.is_getting_dyn_flag = True
            self.robot = None
            gc.collect()
            self.robot = GetOthersLotDynRobot()
            await self.robot.main()
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
            official_verify = lot_det_sep[2]
            official_lot_desc = lot_det_sep[9]
            dt = datetime.datetime.strptime(pubtime_str, '%Y年%m月%d日 %H:%M')
            if dt.year < 2000:
                return False
            pub_ts = int(datetime.datetime.timestamp(datetime.datetime.strptime(pubtime_str, '%Y年%m月%d日 %H:%M')))
            if int(time.time()) - pub_ts > 1 * 30 * 24 * 3600:  # 超过一个月的不要
                return False
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
            self.push_lot_csv(f"官方抽奖信息【{len(filtered_list)}】条",
                              filtered_list[0:10])  # {datetime.datetime.now().strftime('%m月%d日')}
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
            self.push_lot_csv(f"必抽的大奖【{len(ret_filtered_list)}】条",
                              ret_filtered_list[0:10])  # {datetime.datetime.now().strftime('%m月%d日')}
        ret_list = [x.split('\t')[0] for x in ret_filtered_list]
        return ret_list

    async def get_unignore_reserve_lot_space(self) -> list[TUpReserveRelationInfo]:
        from opus新版官方抽奖.预约抽奖.db.sqlHelper import bili_reserve_sqlhelper as mysq
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
            pushme(f"必抽的预约抽奖【{len(ret_info_list)}】条", '\n'.join(ret_info_list[0:10]),
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
        self.push_lot_csv(f"动态抽奖信息【{len(filtered_list)}】条",
                          filtered_list[0:10])  # {datetime.datetime.now().strftime('%m月%d日')}
        filtered_list.sort(key=lambda x: x.split("\t")[0], reverse=True)  # 按照降序排序
        ret_list = [x.split('\t')[0] for x in filtered_list]
        ret_list = list(set(ret_list))
        ret_list.sort(reverse=True)
        return ret_list

    # endregion


get_others_lot_dyn = GetOthersLotDyn()

if __name__ == '__main__':
    async def __test():
        b = GetOthersLotDynRobot()

        for i in range(1, 115):
            print(await b.checkDBDyn(i))
        pass


    asyncio.run(__test())
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(b.get_new_dyn())

    # b = GET_OTHERS_LOT_DYN()
    # c = b.get_unignore_reserve_lot_space()
    # print(c)
