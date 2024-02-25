# -*- coding: utf-8 -*-
import asyncio
import uuid
from dataclasses import dataclass, field
from functools import reduce
import traceback
from typing import Dict
import execjs
import json
import random
import re
import sys
import datetime
import os
import requests
import time
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import Bilibili_methods.all_methods
from utl.代理.request_with_proxy import request_with_proxy
from utl.代理.SealedRequests import MYASYNCHTTPX
from loguru import logger
from CONFIG import CONFIG

# import Bilibili_methods.paddlenlp
root_dir = CONFIG.root_dir
relative_dir = 'github/my_operator/bili_upload/'  # 执行文件所在的相对路径
request_proxy = request_with_proxy()


@dataclass
class user_space_dyn_detail:
    """
    描述获取的b站用户的动态
    """
    latest_dyid_list: list = field(default_factory=list)
    update_num: int = 0


class renew:
    """
    获取他人的抽奖
    """

    def __init__(self):
        self.aid_list = []  # 记录动态附带的视频卡片的aid
        self.request_sem = asyncio.Semaphore(20)
        self.MyAsyncHttpx = MYASYNCHTTPX()
        self.create_dir()
        self.write_in_file_lock = asyncio.Lock()
        self.fake_cookie = '1'
        # self.fake_cookie =''
        logger.info(f'fake cookie:{self.fake_cookie}')
        self.get_dynamic_detail_lock = asyncio.Lock()
        self.js_lock = asyncio.Lock()
        self.lock = asyncio.Lock()
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
        ]  # 需要重点查看的关键词列表
        self.gitee_dyn_id_list: list[str] = []  # https://gitee.com/shellxx/bili_upload 上面获取到的动态id
        self._获取过动态的b站用户: Dict[
            str, user_space_dyn_detail] = dict()  # 格式：{uid:[1,2,3,4,5,6,7,8,9,10]} 最后一次获取的动态
        self._最后一次获取过动态的b站用户: Dict[str, user_space_dyn_detail] = dict()
        try:
            with open(root_dir + relative_dir + '获取过动态的b站用户.json') as f:
                for k, v in json.load(f).items():
                    self._获取过动态的b站用户.update({
                        k: user_space_dyn_detail(**v)
                    })
            logger.info('上次获取的动态：')
            import pprint
            pprint.pprint(self._获取过动态的b站用户, indent=4)
        except Exception as e:
            logger.warning(f'获取b站用户的配置失败！使用默认内容！{e}')

        if os.path.exists(root_dir + relative_dir + 'uidlist.json'):
            try:
                with open(root_dir + relative_dir + 'uidlist.json') as f:
                    self.uidlist = json.load(f).get('uidlist')
            except Exception as e:
                logger.warning(f'获取抽奖用户uid列表失败，使用默认配置！{e}')
        else:
            self.uidlist = [
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
            ]  # 需要爬取的uidlist

        self.uidlist = list(set(self.uidlist))  # 去个重
        self.nonLotteryWords = ['分享视频', '分享动态']
        self.cookie3 = gl.get_value('cookie3')  # 斯卡蒂
        self.fullcookie3 = gl.get_value('fullcookie3')
        self.ua3 = gl.get_value('ua3')
        self.fingerprint3 = gl.get_value('fingerprint3')
        self.csrf3 = gl.get_value('csrf3')
        self.uid3 = gl.get_value('uid3')
        self.username3 = gl.get_value('uname3')
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

        def login_check(cookie, ua):
            headers = {
                'User-Agent': ua,
                'cookie': cookie
            }
            url = 'https://api.bilibili.com/x/web-interface/nav'
            res = requests.get(url=url, headers=headers).json()
            if res['data']['isLogin'] == True:
                name = res['data']['uname']
                self.username = name
                self.uid3 = res['data']['mid']
                logger.info('登录成功,当前账号用户名为%s uid:%s' % (name, str(self.uid3)))
                return 1
            else:
                logger.info('登陆失败,请重新登录')
                sys.exit('登陆失败,请重新登录')

        login_check(self.cookie3, self.ua3)

        def get_attention(mid, cookie, ua):
            url = 'https://account.bilibili.com/api/member/getCardByMid?mid=%s' % mid
            headers = {
                'cookie': cookie,
                'user-agent': ua
            }
            req = requests.get(url=url, headers=headers)
            return req.json().get('card').get('attentions')

        self.all_followed_uid = get_attention(self.uid3, self.cookie3, self.ua3)
        logger.info(f'共{len(self.all_followed_uid)}个关注')
        # self.nlp = Bilibili_methods.paddlenlp.my_paddlenlp()
        os.system(f'cd "{root_dir}github/bili_upload" && git fetch --all && git reset --hard && git pull')

        self.last_order: list[str] = []  # 上次查询过的记录
        self.last_lotid: list[str] = []  # 之前的抽奖动态id 直接丢动态id进去
        self.recorded_dynamic_id: list[str] = []  # 单轮获取[动态id] 记录的动态id，最后需要判断是否是抽奖的动态！
        self.queried_dynamic_id_list: list[str] = []  # 所有查询过的动态id
        self.BAPI = Bilibili_methods.all_methods.methods()
        self.lottery_dynamic_ids: list[str] = []  # [动态链接：https://t.bilibili.com/...]
        self.lottery_dynamic_detail_list = []  # 动态详情，最后写入抽奖文件里的内容！
        self.useless_info = []

    def create_dir(self):
        if not os.path.exists(root_dir + relative_dir + 'log'):
            os.makedirs(root_dir + relative_dir + 'log')
        if not os.path.exists(root_dir + relative_dir + 'log/all_log'):
            os.mkdir(root_dir + relative_dir + 'log/all_log')
        if not os.path.exists(root_dir + relative_dir + 'log/动态响应'):
            os.mkdir(root_dir + relative_dir + 'log/动态响应')

    def file_resolve(self, file_content):
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
                    logger.info(lottery_update_date)
                    break
            if i not in self.recorded_dynamic_id and i != '' and i != ' ' and str.isdigit(i):
                self.recorded_dynamic_id.append(i.strip())  # 从gitee获取别人爬下来的抽奖内容
                self.gitee_dyn_id_list.append(i.strip())

    def remove_list_dict_duplicate(self, list_dict_data):
        """
        对list格式的dict进行去重

        """
        run_function = lambda x, y: x if y in x else x + [y]
        return reduce(run_function, [[], ] + list_dict_data)

    def log_writer(self, filename, content_list: list, write_method):
        try:
            with open(root_dir + relative_dir + f'log/{filename}', write_method, encoding='utf-8') as f:
                for _ in content_list:
                    f.writelines(f'{_}\n')
        except:
            with open(root_dir + relative_dir + f'log/{filename}', 'w', encoding='utf-8') as f:
                for _ in content_list:
                    f.writelines(f'{_}\n')

    async def get_dynamic_detail_with_proxy(self, dynamic_id, _cookie='', _useragent='', dynamic_type=2):
        '''
        使用代理获取动态详情
        :param dynamic_type:
        :param dynamic_id:
        :param _cookie:
        :param _useragent:
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
        '''
        if _cookie == '':
            headers = {
                'Referer': f'https://t.bilibili.com/{dynamic_id}', 'Connection': 'close',
                'User-Agent': random.choice(CONFIG.UA_LIST),
                'cookie': '1'
            }
        else:
            headers = {
                'Referer': f'https://t.bilibili.com/{dynamic_id}', 'Connection': 'close',
                'User-Agent': random.choice(CONFIG.UA_LIST),
                'cookie': _cookie
                # 'X-Forwarded-For': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
                #                                         random.choice(range(0, 255)), random.choice(range(0, 255))),
                # 'X-Real-IP': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
                #                                   random.choice(range(0, 255)), random.choice(range(0, 255))),
                # 'From': 'bingbot(at)microsoft.com',
            }
        url = 'http://api.bilibili.com/x/polymer/web-dynamic/v1/detail?timezone_offset=-480&platform=web&id=' + str(
            dynamic_id) + '&features=itemOpusStyle,opusBigCover,onlyfansVote,endFooterHidden&web_location=444.42'
        if dynamic_type != 2:
            url = f'http://api.bilibili.com/x/polymer/web-dynamic/v1/detail?timezone_offset=-480&rid={dynamic_id}&type={dynamic_type}&features=itemOpusStyle,opusBigCover'
        try:
            async with self.request_sem:
                dynamic_req = await request_proxy.request_with_proxy(method='GET', url=url, headers=headers,
                                                                     mode='single')
        except Exception as e:
            traceback.print_exc()
            return await self.get_dynamic_detail_with_proxy(dynamic_id, _cookie, _useragent)
        try:
            if dynamic_req.get('code') == 4101131:
                logger.info(dynamic_req)
                return None
            async with self.write_in_file_lock:
                self.log_writer('动态响应/resp.csv', [json.dumps(dynamic_req)], 'a+')
            # logger.info(f'获取成功header:{headers}')
            dynamic_dict = dynamic_req
            dynamic_data = dynamic_dict.get('data')
            comment_type = dynamic_data.get('item').get('basic').get('comment_type')
            dynamic_type = '8'
            if str(comment_type) == '17':
                dynamic_type = '4'
            elif str(comment_type) == '1':
                dynamic_type = '8'
            elif str(comment_type) == '11':
                dynamic_type = '2'
            elif str(comment_type) == '12':
                dynamic_type = '64'
            card_stype = dynamic_data.get('item').get('type')
            dynamic_id = dynamic_data.get('item').get('id_str')
            dynamic_rid = dynamic_data.get('item').get('basic').get('comment_id_str')
            relation = dynamic_data.get('item').get('modules').get('module_author').get('following')
            author_uid = dynamic_data.get('item').get('modules').get('module_author').get('mid')
            author_name = dynamic_data.get('item').get('modules').get('module_author').get('name')
            pub_time = dynamic_data.get('item').get('modules').get('module_author').get('pub_time')
            pub_ts = dynamic_data.get('item').get('modules').get('module_author').get('pub_ts')
            try:
                official_verify_type = dynamic_data.get('item').get('modules').get('module_author').get(
                    'official_verify').get('type')
            except:
                official_verify_type = None
            comment_count = dynamic_data.get('item').get('modules').get('module_stat').get('comment').get('count')
            forward_count = dynamic_data.get('item').get('modules').get('module_stat').get('forward').get('count')
            like_count = dynamic_data.get('item').get('modules').get('module_stat').get('like').get('count')
            dynamic_content1 = ''
            if dynamic_data.get('item').get('modules').get('module_dynamic').get('desc'):
                dynamic_content1 += dynamic_data.get('item').get('modules').get('module_dynamic').get('desc').get(
                    'text')
            dynamic_content2 = ''
            if dynamic_data.get('item').get('modules').get('module_dynamic').get('major'):
                if dynamic_data.get('item').get('modules').get('module_dynamic').get('major').get('archive'):
                    dynamic_content2 += dynamic_data.get('item').get('modules').get('module_dynamic').get('major').get(
                        'archive').get('desc') + dynamic_data.get('item').get('modules').get('module_dynamic').get(
                        'major').get(
                        'archive').get('title')
                if dynamic_data.get('item').get('modules').get('module_dynamic').get('major').get('article'):
                    dynamic_content2 += str(
                        dynamic_data.get('item').get('modules').get('module_dynamic').get('major').get(
                            'article').get('desc')) + dynamic_data.get('item').get('modules').get('module_dynamic').get(
                        'major').get(
                        'article').get('title')
                if dynamic_data.get('item').get('modules').get('module_dynamic').get('major').get('opus'):
                    dynamic_content2 += dynamic_data.get('item').get('modules').get('module_dynamic').get('major').get(
                        'opus').get('summary').get('text')
                    if dynamic_data.get('item').get('modules').get('module_dynamic').get('major').get('opus').get(
                            'title'):
                        dynamic_content2 += dynamic_data.get('item').get('modules').get('module_dynamic').get(
                            'major').get('opus').get('title')
            dynamic_content = dynamic_content1 + dynamic_content2
            desc = dynamic_data.get('item').get('modules').get(
                'module_dynamic').get(
                'desc')

            if relation:
                relation = 1
            else:
                relation = 0
            is_liked = dynamic_data.get('item').get('modules').get('module_stat').get('like').get('status')
            if is_liked:
                is_liked = 1
            else:
                is_liked = 0
            if relation != 1:
                logger.info(f'未关注的response\nhttps://space.bilibili.com/{author_uid}\n{dynamic_id}')
        except Exception as e:
            logger.critical(f'https://t.bilibili.com/{dynamic_id}\n{dynamic_req}\n{e}')
            traceback.print_exc()
            if dynamic_req.get('code') == -412:
                logger.info('412风控')
                await asyncio.sleep(10)
                return await self.get_dynamic_detail_with_proxy(dynamic_id, _cookie, _useragent)
            if dynamic_req.get('code') == 4101128:
                logger.info(dynamic_req.get('message'))
            if dynamic_req.get('code') is None:
                return await self.get_dynamic_detail_with_proxy(dynamic_id, _cookie, _useragent)
            if dynamic_req.get('code') == 401:
                logger.critical(dynamic_req)
                await asyncio.sleep(10)
                return await self.get_dynamic_detail_with_proxy(dynamic_id, _cookie, _useragent)
            return None

        top_dynamic = None
        try:
            module_tag = dynamic_data.get('item').get('modules').get('module_tag')
            if module_tag:
                module_tag_text = module_tag.get('text')
                if module_tag_text == "置顶":
                    top_dynamic = True
                else:
                    logger.info(module_tag_text)
                    logger.info('未知动态tag')
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
        try:
            if dynamic_data.get('item').get('orig'):
                orig_dynamic_id = dynamic_data.get('item').get('orig').get('id_str')
                orig_mid = dynamic_data.get('item').get('orig').get('modules').get('module_author').get('mid')
                orig_name = dynamic_data.get('item').get('orig').get('modules').get('module_author').get('name')
                orig_pub_ts = dynamic_data.get('item').get('orig').get('modules').get('module_author').get('pub_ts')
                if dynamic_data.get('item').get('orig').get('modules').get('module_author').get(
                        'official_verify'):
                    orig_official_verify = dynamic_data.get('item').get('orig').get('modules').get('module_author').get(
                        'official_verify').get('type')
                else:
                    orig_official_verify = dynamic_data.get('item').get('orig').get('modules').get('module_author').get(
                        'type')
                # orig_comment_count = dynamic_data.get('item').get('orig').get('modules').get('module_stat').get('comment').get(
                #     'count')
                # orig_forward_count = dynamic_data.get('item').get('orig').get('modules').get('module_stat').get('forward').get(
                #     'count')
                # orig_like_count = dynamic_data.get('item').get('orig').get('modules').get('module_stat').get('like').get('count')
                orig_dynamic_content1 = ''
                if dynamic_data.get('item').get('orig').get('modules').get('module_dynamic').get('desc'):
                    orig_dynamic_content1 = dynamic_data.get('item').get('orig').get('modules').get(
                        'module_dynamic').get(
                        'desc').get('text')
                orig_dynamic_content2 = ''
                if dynamic_data.get('item').get('orig').get('modules').get('module_dynamic').get('major'):
                    if dynamic_data.get('item').get('orig').get('modules').get('module_dynamic').get('major').get(
                            'archive'):
                        orig_dynamic_content2 += dynamic_data.get('item').get('orig').get('modules').get(
                            'module_dynamic').get('major').get('archive').get('desc')
                    if dynamic_data.get('item').get('orig').get('modules').get('module_dynamic').get('major').get(
                            'article'):
                        orig_dynamic_content2 += str(
                            dynamic_data.get('item').get('orig').get('modules').get('module_dynamic').get(
                                'major').get('article').get('desc')) + \
                                                 dynamic_data.get('item').get('orig').get('modules').get(
                                                     'module_dynamic').get('major').get('article').get('title')
                    if dynamic_data.get('item').get('orig').get('modules').get('module_dynamic').get('major').get(
                            'opus'):
                        orig_dynamic_content2 += dynamic_data.get('item').get('orig').get('modules').get(
                            'module_dynamic').get(
                            'major').get('opus').get('summary').get('text')
                orig_dynamic_content = orig_dynamic_content1 + orig_dynamic_content2
                orig_desc = dynamic_data.get('item').get('orig').get('modules').get(
                    'module_dynamic').get(
                    'desc')
                orig_relation = dynamic_data.get('item').get('orig').get('modules').get('module_author').get(
                    'following')
                if orig_relation:
                    orig_relation = 1
                else:
                    orig_relation = 0
                # orig_is_liked = dynamic_data.get('item').get('orig').get('modules').get('module_stat').get('like').get(
                #     'status')
                # if orig_is_liked:
                #     orig_is_liked = 1
                # else:
                #     orig_is_liked = 0
            else:
                logger.info('非转发动态，无原动态')
        except Exception as e:
            logger.info(dynamic_req)
            logger.error(e)
            traceback.print_exc()
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
            'module_dynamic': dynamic_data.get('item').get('modules').get('module_dynamic'),  # 动态模块

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
        return structure

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
            logger.info(pinglunurl)
        except:
            traceback.print_exc()
            logger.info('获取评论失败')
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
                logger.info('获取置顶评论失败')
                message = pinglun_dict.get('message')
                logger.info(pinglun_dict)

                if message != 'UP主已关闭评论区' and message != '啥都木有' and message != '评论区已关闭':
                    while 1:
                        try:
                            await asyncio.sleep(1)
                            break
                        except:
                            continue
                    return 'null'
                else:
                    logger.info(message)
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
            if topreplies != None:
                for tprps in topreplies:
                    topmsg += tprps.get('content').get('message')
                    if tprps.get('replies'):
                        for tprpsrps in tprps.get('replies'):
                            if tprpsrps.get('mid') == mid:
                                iner_replies += tprpsrps.get('content').get('message')
                topmsg += iner_replies
                logger.info('置顶评论：' + topmsg)
            else:
                logger.info('无置顶评论')
                topmsg = 'null' + iner_replies
        except Exception as e:
            logger.info(e)
            logger.info('获取置顶评论失败')
            if pinglunreq.get('code') is None:
                return await self.get_topcomment_with_proxy(dynamicid, rid, pn, _type, mid)
            pinglun_dict = pinglunreq
            data = pinglun_dict.get('data')
            logger.info(pinglun_dict)
            logger.info(data)
            topmsg = 'null'
            logger.info(self.BAPI.timeshift(int(time.time())))
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

    async def judge_lottery(self, dynamic_id, dynamic_type: int = 2, is_lot_orig=False):
        logger.info(f'当前动态：https://t.bilibili.com/{dynamic_id}?type={dynamic_type}')
        async with self.get_dynamic_detail_lock:
            if str(dynamic_id) in self.queried_dynamic_id_list:  # 如果源动态已经被判定为抽奖动态过了的话，就不在加入抽奖列表里
                logger.warning(f'当前动态 {dynamic_id} 已经查询过了，不重复查询')
                return
            self.queried_dynamic_id_list.append(str(dynamic_id))
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
            dynamic_detail = await self.get_dynamic_detail_with_proxy(dynamic_id, fake_cookie_str,
                                                                      random.choice(CONFIG.UA_LIST),
                                                                      dynamic_type=dynamic_type)  # 需要增加假的cookie
        except:
            # await asyncio.sleep(60)
            traceback.print_exc()
            return await self.judge_lottery(dynamic_id, dynamic_type, is_lot_orig)

        suffix = ''
        if dynamic_detail:
            dynamic_detail_dynamic_id = dynamic_detail['dynamic_id']  # 获取正确的动态id，不然可能会是rid或者aid
            dynamic_content = dynamic_detail['dynamic_content']
            author_name = dynamic_detail['author_name']
            pub_time = dynamic_detail['pub_time']
            comment_count = dynamic_detail['comment_count']
            forward_count = dynamic_detail['forward_count']
            official_verify_type = dynamic_detail['official_verify_type']
            author_uid = dynamic_detail['author_uid']
            rid = dynamic_detail['rid']
            _type = dynamic_detail['type']
            module_dynamic: dict = dynamic_detail['module_dynamic']
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
                            if v.get('reserve').get('desc3'):
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
                logger.info(f'https://t.bilibili.com/{dynamic_detail_dynamic_id}?type={dynamic_type}')
                logger.info('动态内容为空')
                deadline = None
            premsg = self.BAPI.pre_msg_processing(dynamic_content)
            if comment_count > 50 or str(dynamic_detail.get('type')) == '8':
                dynamic_content += await self.get_topcomment_with_proxy(str(dynamic_detail_dynamic_id), str(rid),
                                                                        str(0), _type,
                                                                        author_uid)
            if author_uid in self.all_followed_uid:
                suffix = 'followed_uid'
            ret_url = f'https://t.bilibili.com/{dynamic_detail_dynamic_id}'
            if self.BAPI.zhuanfapanduan(dynamic_content):
                ret_url += '?tab=2'
            Manual_judge = ''
            async with self.js_lock:
                if self.manual_reply_judge.call("manual_reply_judge", dynamic_content):
                    Manual_judge = '人工判断'
            high_lights_list = []
            for i in self.highlight_word_list:
                if i in dynamic_content:
                    high_lights_list.append(i)
            format_list = [ret_url, author_name, str(official_verify_type), str(pub_time), repr(dynamic_content),
                           str(comment_count), str(forward_count), Manual_judge,
                           ';'.join(high_lights_list),
                           '官方抽奖' if is_official_lot else '充电抽奖' if is_charge_lot else '预约抽奖' if is_reserve_lot else '',
                           lot_rid, suffix,
                           premsg,
                           str(deadline)
                           ]
            format_str = '\t'.join(map(str, format_list))
            if re.match(r'.*//@.*', str(dynamic_content), re.DOTALL) != None:
                dynamic_content = re.findall(r'(.*?)//@', dynamic_content, re.DOTALL)[0]
            if str(dynamic_detail_dynamic_id) not in self.gitee_dyn_id_list:  # 如果不在gitee里面的动态id需要判断是否是抽奖
                if not is_lot_orig:
                    if self.BAPI.daily_choujiangxinxipanduan(dynamic_content):
                        if comment_count > 2000 or forward_count > 1000:  # 评论或转发超多的就算不是抽奖动态也要加进去凑个数
                            pass
                        else:
                            self.useless_info.append(format_str)
                            return
            async with self.get_dynamic_detail_lock:  # 这个地方一定要加锁保证数据的一致性！！！
                self.lottery_dynamic_ids.append(ret_url)
                self.lottery_dynamic_detail_list.append(format_str)
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
                orig_ret_url = f'https://t.bilibili.com/{orig_dynamic_id}'
                if self.BAPI.zhuanfapanduan(orig_dynamic_content):
                    orig_ret_url += '?tab=2'
                async with self.get_dynamic_detail_lock:  # 这个地方一定要加锁保证数据的一致性！！！
                    if orig_ret_url in self.lottery_dynamic_ids or \
                            str(orig_dynamic_id) in self.last_lotid\
                    or str(orig_dynamic_id) in self.queried_dynamic_id_list:  # 如果源动态已经被判定为抽奖动态过了的话，就不在加入抽奖列表里
                        logger.warning(f'原动态 {orig_ret_url} 已经有过了，不加入抽奖动态中')
                        return
                orig_official_verify = dynamic_detail['orig_official_verify']
                format_list = [orig_ret_url, orig_name, str(orig_official_verify),
                               str(time.strftime("%Y年%m月%d日 %H:%M", time.localtime(orig_pub_ts))),
                               repr(orig_dynamic_content),
                               str(orig_comment_count), str(orig_forward_count), Manual_judge,
                               ';'.join(high_lights_list),
                               '抽奖动态的源动态',
                               lot_rid,
                               suffix,
                               premsg,
                               str(deadline)
                               ]
                format_str = '\t'.join(map(str, format_list))
                async with self.get_dynamic_detail_lock:  # 这个地方一定要加锁保证数据的一致性！！！
                    self.lottery_dynamic_ids.append(orig_ret_url)
                    self.lottery_dynamic_detail_list.append(format_str)

            if dynamic_detail.get('module_dynamic'):
                if dynamic_detail.get('module_dynamic').get('additional'):
                    if dynamic_detail.get('module_dynamic').get('additional').get('type') == 'ADDITIONAL_TYPE_UGC':
                        ugc = dynamic_detail.get('module_dynamic').get('additional').get('ugc')
                        aid_str = ugc.get('id_str')
                        async with self.get_dynamic_detail_lock:  # 这个地方一定要加锁保证数据的一致性！！！
                            isChecked = aid_str in self.aid_list
                            if not isChecked:
                                self.aid_list.append(aid_str)
                        if not isChecked:
                            await self.judge_lottery(dynamic_id=aid_str, dynamic_type=8,
                                                     is_lot_orig=True)

    async def get_space_dynamic_req_with_proxy(self, hostuid, offset):
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
        uid = 0
        dongtaidata = {
            'visitor_uid': uid,
            'host_uid': hostuid,
            'offset_dynamic_id': offset,
            'need_top': '0',
            'platform': 'web'
        }
        url = 'http://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?visitor_uid=' + str(
            uid) + '&host_uid=' + str(hostuid) + '&offset_dynamic_id=' + str(offset) + '&need_top=0'
        try:
            req = await request_proxy.request_with_proxy(method='GET', url=url, headers=headers, data=dongtaidata,
                                                         verify=False, mode='single')
            return req
        except Exception as e:
            logger.critical(f'Exception while getting space history dynamic {uid} {hostuid} {offset}!\n{e}')
            return await self.get_space_dynamic_req_with_proxy(hostuid, offset)

    def get_space_detail(self, space_req_dict: dict):  # 直接处理
        '''
        解析空间动态的json
        :param space_req_dict:
        :return:
        '''
        req_dict = space_req_dict
        if req_dict.get('code') == -412:
            logger.info(req_dict)
            logger.info(req_dict.get('message'))
            # await asyncio.sleep(10 * 60)
        if not req_dict:
            logger.info(f'ERROR{space_req_dict}')
            return 404
        cards_json = req_dict.get('data').get('cards')
        dynamic_id_list = []
        if cards_json:
            for card_dict in cards_json:
                dynamic_id = str(card_dict.get('desc').get('pre_dy_id_str'))  # 判断中转动态id是否重复；非最原始动态id 类型为string
                try:
                    dynamic_repost_content = json.loads(card_dict.get('card')).get('item').get('content')
                except:
                    dynamic_repost_content = None
                logger.info(
                    f"当前动态： https://t.bilibili.com/{card_dict.get('desc').get('dynamic_id')}\t{time.asctime()}\n转发|评论|发布内容：{dynamic_repost_content}")
                if dynamic_repost_content in self.nonLotteryWords:
                    # logger.info('转发评论内容为非抽奖词，跳过')
                    continue
                if dynamic_id in self.recorded_dynamic_id:
                    # logger.info('遇到log文件记录过的动态id')
                    continue
                if dynamic_id == "0":
                    # logger.info('遇到已删除动态')
                    continue
                if dynamic_id in dynamic_id_list:
                    # logger.info('遇到重复动态id')
                    # logger.info('https://t.bilibili.com/{}'.format(dynamic_id))
                    continue
                dynamic_time = card_dict.get('desc').get('timestamp')  # 判断是否超时，超时直接退出
                if time.time() - dynamic_time >= self.SpareTime:
                    # logger.info('遇到超时动态')
                    return 0
                for _ in self.card_detail(card_dict):
                    if _:
                        # logger.info(f'添加进记录：{_}')
                        dynamic_id_list.append(str(_))  # 间接和原始的动态id全部记录
        else:
            logger.info(space_req_dict)
            logger.info('cards_json为None')
        self.recorded_dynamic_id.extend(dynamic_id_list)

        # if not dynamic_id_list:
        #     await asyncio.sleep(2)
        return 0

    def card_detail(self, cards_json):
        """
        返回间接动态和原始动态的动态id
        :param cards_json:
        :return:
        """
        card_json = json.loads(cards_json.get('card'))
        # logger.info(card_json)  # 测试点
        try:
            pre_dy_id = str(card_json.get('item').get('pre_dy_id'))
        except:
            pre_dy_id = None
        try:
            orig_dy_id = str(card_json.get('item').get('orig_dy_id'))
        except:
            orig_dy_id = None
        if pre_dy_id == orig_dy_id:
            pre_dy_id = None
        return [orig_dy_id, pre_dy_id]

    def get_offset(slef, space_req_dict):
        return space_req_dict.get('data').get('next_offset')

    def get_space_dynmaic_time(self, space_req_dict: dict):  # 返回list
        cards_json = space_req_dict.get('data').get('cards')
        dynamic_time_list = []
        if cards_json:
            for card_dict in cards_json:
                dynamic_time = card_dict.get('desc').get('timestamp')
                dynamic_time_list.append(dynamic_time)
        return dynamic_time_list

    def get_space_dynamic_id_list(self, space_req_dict: dict) -> list[str] or bool:
        ret_list = []
        try:
            for dynamic_card in space_req_dict.get('data').get('cards'):
                ret_list.append(str(dynamic_card.get('desc').get('dynamic_id_str')))
            if space_req_dict.get('data').get('inplace_fold'):
                for i in space_req_dict.get('data').get('inplace_fold'):
                    if i.get('dynamic_ids'):
                        for dyn_id in i.get('dynamic_ids'):
                            ret_list.append(dyn_id)
                    logger.debug(f'遇到折叠内容！inplace_fold:{i}')
            if space_req_dict.get('data').get('has_more') == 0 and len(ret_list) == 0:
                return None
            return ret_list
        except Exception as e:
            logger.error(space_req_dict)
            traceback.print_exc()
            raise e

    async def get_user_space_dynamic_id(self, uid):
        '''
        根据时间和获取过的动态来判断是否结束爬取别人的空间主页
        :return:
        '''
        n = 0
        logger.info(
            f'当前UID：https://space.bilibili.com/{uid}/dynamic\t进度：【{self.uidlist.index(uid) + 1}/{len(self.uidlist)}】')
        first_get_dynamic_falg = True
        offset = 0
        timelist = [0]
        while 1:
            dyreq_dict = await self.get_space_dynamic_req_with_proxy(uid, offset)
            try:
                if dyreq_dict.get('data').get('has_more') != 1:
                    logger.info(f'当前用户 https://space.bilibili.com/{uid}/dynamic 无更多动态')
                    break
            except Exception as e:
                logger.critical(f'Error: has_more获取失败\n{dyreq_dict}\n{e}')
            try:
                repost_dynamic_id_list = self.get_space_dynamic_id_list(dyreq_dict)  # 脚本们转发生成的动态id
            except Exception as e:
                logger.critical(f'解析空间动态失败！\n{e}\n{uid} {offset}')
                continue
            if repost_dynamic_id_list is None:
                logger.info(f'{uid}空间动态为0')
                break
            async with self.lock:
                if not first_get_dynamic_falg and repost_dynamic_id_list:
                    if self._获取过动态的b站用户.get(str(uid)):
                        update_num = len(repost_dynamic_id_list) - len(
                            set(repost_dynamic_id_list) & set(self._获取过动态的b站用户.get(str(uid)).latest_dyid_list))
                    else:
                        update_num = len(repost_dynamic_id_list)
                    exist_user_space_dyn_detail = self._最后一次获取过动态的b站用户.get(str(uid))
                    if exist_user_space_dyn_detail:
                        exist_user_space_dyn_detail.update_num += update_num
                if first_get_dynamic_falg and repost_dynamic_id_list:
                    if self._获取过动态的b站用户.get(str(uid)):
                        update_num = len(repost_dynamic_id_list) - len(
                            set(repost_dynamic_id_list) & set(self._获取过动态的b站用户.get(str(uid)).latest_dyid_list))
                    else:
                        update_num = len(repost_dynamic_id_list)
                    self._最后一次获取过动态的b站用户.update(
                        {str(uid): user_space_dyn_detail(repost_dynamic_id_list, update_num)})
                    first_get_dynamic_falg = False
                # await asyncio.sleep(sleeptime)
                n += 1
                if self.get_space_detail(dyreq_dict) != 0:
                    offset = 0
                    continue
                offset = self.get_offset(dyreq_dict)
                timelist = self.get_space_dynmaic_time(dyreq_dict)
                # await asyncio.sleep(5)
                if len(timelist) == 0:
                    logger.info('timelist is empty')
                    continue
                if time.time() - timelist[-1] >= self.SpareTime:
                    logger.info(
                        f'超时动态，当前UID：https://space.bilibili.com/{uid}/dynamic\t获取结束\t{self.BAPI.timeshift(time.time())}')
                    # await asyncio.sleep(60)
                    break
                if self._获取过动态的b站用户.get(str(uid)):
                    logger.info(self._获取过动态的b站用户.get(str(uid)))
                    logger.info(repost_dynamic_id_list)
                    if set(self._获取过动态的b站用户.get(str(uid)).latest_dyid_list) & set(repost_dynamic_id_list):
                        logger.info(
                            f'遇到获取过的动态，当前UID：https://space.bilibili.com/{uid}/dynamic\t获取结束\t{self.BAPI.timeshift(time.time())}')

                        # await asyncio.sleep(60)
                        break
                # if n % 50 == 0:
                #     logger.info('获取了50次，休息个10s')
                #     await asyncio.sleep(10)

        if n <= 4 and time.time() - timelist[-1] >= self.SpareTime:
            # self.uidlist.remove(uid)
            logger.info(f'{uid}\t当前UID获取到的动态太少，前往：\nhttps://space.bilibili.com/{uid}\n查看详情')

    async def thread_judgedynamic(self, write_in_list):
        logger.info('多线程获取动态')
        task_list = []
        for i in write_in_list:
            tk = asyncio.create_task(self.judge_lottery(i))
            task_list.append(tk)

        while True:
            task_doing = [i for i in task_list if not i.done()]
            if len(task_doing) == 0:
                break
            else:
                logger.debug(f'当前正在获取动态的任务数量：{len(task_doing)}/{len(task_list)}')
            await asyncio.sleep(5)

        await asyncio.gather(*task_list, return_exceptions=True)

    # def judgedynamic_without_thread(self, write_in_list):
    #     for i in write_in_list:
    #         logger.info(f'当前进度：{write_in_list.index(i) + 1}/{len(write_in_list)}')
    #         if i in self.last_order:
    #             continue
    #         else:
    #             self.last_order.append(i)
    #         self.judge_lottery(i)

    async def main(self):
        if os.path.exists(root_dir + relative_dir + 'uidlist.json'):
            try:
                with open(root_dir + relative_dir + 'uidlist.json') as f:
                    self.uidlist = json.load(f).get('uidlist')
            except:
                traceback.print_exc()
        get_dyid_path = root_dir + relative_dir + 'get_dyid.txt'
        if os.path.exists(get_dyid_path):
            with open(get_dyid_path, 'r', encoding='utf-8') as f:
                for i in f.readlines():
                    for _i in i.split(','):
                        self.last_order.append(str(_i.strip()))
                        self.queried_dynamic_id_list.append(str(_i.strip()))

        self.last_order = list(set(self.last_order))
        if len(self.last_order) > 100000:
            self.last_order = self.last_order[-100000:]  # 总共容纳10000000条记录，占不了多少空间的
            # self.last_order.sort()  # 排序之前裁剪掉，去掉那些没动静的号的动态id

        lot_dyid_path = root_dir + relative_dir + 'lot_dyid.txt'
        if os.path.exists(lot_dyid_path):
            with open(lot_dyid_path, 'r', encoding='utf-8') as f:
                for i in f.readlines():
                    for _i in i.split(','):
                        self.last_lotid.append(_i.strip())
        self.last_lotid = list(set(self.last_lotid))
        if len(self.last_lotid) > 100000:
            self.last_lotid = self.last_lotid[-100000:]

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
        logger.info(f'共获取{len(path_dir_name)}个文件')
        for i in effective_files_content_list:
            self.file_resolve(i)  # 记录动态id

        task_list = [asyncio.create_task(self.get_user_space_dynamic_id(i)) for i in self.uidlist]
        while True:
            task_doing = [i for i in task_list if not i.done()]
            if len(task_doing) == 0:
                break
            else:
                logger.debug(f'当前正在获取uid数量：{len(task_doing)}')
            await asyncio.sleep(5)
        await asyncio.gather(*task_list)
        logger.info('空间动态id获取完毕')
        write_in_list = list(set(self.recorded_dynamic_id))
        write_in_list.sort()
        for i in self.last_order:
            if i in write_in_list:
                write_in_list.remove(i)
        self.last_order.extend(write_in_list)
        logger.info(f'共获取到{len(write_in_list)}个动态id')
        with open(root_dir + relative_dir + '最后一轮爬取到的动态id.txt', 'w', encoding='utf-8') as f:
            f.writelines(','.join(write_in_list))
        await self.thread_judgedynamic(write_in_list)

        # format_list = [ret_url, author_name, str(official_verify_type), str(pub_time), repr(dynamic_content),
        #                str(comment_count), str(forward_count), suffix, premsg, Manual_judge, ';'.join(high_lights_list),
        #                str(deadline)
        #                ]
        self.lottery_dynamic_detail_list.sort(key=lambda x: x.split('\t')[3])
        self.useless_info.sort(key=lambda x: x[3])

        self.log_writer('过滤抽奖信息.csv', self.lottery_dynamic_detail_list, 'w')
        self.log_writer('无用信息(需要检查).csv', self.useless_info, 'w')
        self.log_writer('all_log/所有抽奖信息记录.csv', self.lottery_dynamic_detail_list, 'a+')
        self.log_writer('all_log/所有无用信息.csv', self.useless_info, 'a+')

        # self.last_order.sort()//不排序直接放进去
        with open(root_dir + relative_dir + 'get_dyid.txt', 'w', encoding='utf-8') as f:
            f.writelines(','.join(self.last_order))

        with open(root_dir + relative_dir + 'lot_dyid.txt', 'w', encoding='utf-8') as f:
            f.writelines(','.join(self.last_lotid))

        with open(root_dir + relative_dir + '获取过动态的b站用户.json', 'w') as f:
            json_dict = dict()
            self._最后一次获取过动态的b站用户 = dict(
                sorted(self._最后一次获取过动态的b站用户.items(), key=lambda x: x[1].update_num))
            for k, v in self._最后一次获取过动态的b站用户.items():
                json_dict.update({k: v.__dict__})
            json.dump(json_dict, f, indent=4)

        with open(root_dir + relative_dir + 'uidlist.json', 'w') as f:
            json.dump({'uidlist': self.uidlist}, f, indent=4)

        logger.info(
            f'任务完成\n获取到共计：\n{len(self.lottery_dynamic_detail_list)}条抽奖动态\n{len(self.useless_info)}条非抽奖动态！',
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()))))


class GET_OTHERS_LOT_DYN:
    """
        获取更新的抽奖，如果时间在1天之内，那么直接读取文件获取结果，将结果返回回去
    """

    def __init__(self):
        self.is_getting_dyn_flag_lock = asyncio.Lock()
        self.save_lock = asyncio.Lock()
        if os.path.exists(root_dir + relative_dir + 'get_dyn_ts.txt'):
            with open(root_dir + relative_dir + 'get_dyn_ts.txt', 'r', encoding='utf-8') as f:
                try:
                    self.get_dyn_ts: int = int(f.read())
                except Exception as e:
                    logger.error(f'读取上次获取动态时间戳失败！\n{e}')
                    self.get_dyn_ts = 0
                if not isinstance(self.get_dyn_ts, int):
                    self.get_dyn_ts: int = 0
        else:
            self.get_dyn_ts: int = 0
        self.is_getting_dyn_flag = False

    async def save_now_get_dyn_ts(self, ts: int):
        async with self.save_lock:
            with open(root_dir + relative_dir + 'get_dyn_ts.txt', 'w', encoding='utf-8') as f:
                self.get_dyn_ts = ts
                f.writelines(f'{ts}')

    # <editor-fold desc="主函数">
    async def get_new_dyn(self) -> list[str]:
        """
        主函数
        :return:
        """
        while self.is_getting_dyn_flag:
            await asyncio.sleep(30)
        if os.path.exists(root_dir + relative_dir + 'get_dyn_ts.txt'):
            with open(root_dir + relative_dir + 'get_dyn_ts.txt', 'r', encoding='utf-8') as f:
                try:
                    self.get_dyn_ts: int = int(f.read())
                    if not isinstance(self.get_dyn_ts, int):
                        self.get_dyn_ts: int = 0
                except:
                    self.get_dyn_ts: int = 0
        else:
            self.get_dyn_ts: int = 0
        logger.debug(f'上次获取别人B站动态空间抽奖时间：{datetime.datetime.fromtimestamp(self.get_dyn_ts)}')
        if int(time.time()) - self.get_dyn_ts >= 0.8 * 24 * 3600:
            start_ts = int(time.time())
            async with self.is_getting_dyn_flag_lock:
                self.is_getting_dyn_flag = True
            ___ = renew()
            await ___.main()
            await self.save_now_get_dyn_ts(start_ts)
            async with self.is_getting_dyn_flag_lock:
                self.is_getting_dyn_flag = False

        return self.solve_lot_csv()

    def get_official_lot_dyn(self) -> list[str]:
        '''
        返回官方抽奖信息，结尾是tab=1
        :return:
        '''

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
            if official_lot_desc == '官方抽奖':
                if int(rep_count_str) < 200:
                    if int(self.get_dyn_ts - pub_ts) <= 2 * 3600:  # 获取时间和发布时间间隔小于2小时的不按照评论转发数量过滤
                        return True
                    return False
                return True
            return False

        all_lot_det = []
        with open(root_dir + relative_dir + 'log/过滤抽奖信息.csv', 'r', encoding='utf-8') as f:
            for i in f.readlines():
                all_lot_det.append(i.strip())
        filtered_list: list[str] = list(filter(is_official_lot, all_lot_det))
        filtered_list.sort(key=lambda x: try_parse_int(x.split("\t")[5]), reverse=True)
        self.push_lot_csv(f"官方抽奖信息", filtered_list[0:10])  # {datetime.datetime.now().strftime('%m月%d日')}
        filtered_list.sort(key=lambda x: x.split("\t")[0], reverse=True)  # 按照降序排序
        ret_list = [x.split('\t')[0].replace('?tab=2', '') + '?tab=1' for x in filtered_list]
        return ret_list

    # </editor-fold>

    def push_lot_csv(self, title: str, content_list: list):
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

        url = CONFIG.pushnotify.pushme.url
        token = CONFIG.pushnotify.pushme.token
        data = {
            "push_key": token,
            "title": title,
            "content": content,
            'type': 'markdata'
        }
        req = requests.post(url=url, data=data)
        logger.debug(data)
        logger.debug(req.text)

    # <editor-fold desc="获取抽奖csv里的数据">
    def is_need_lot(self, lot_det: str):
        """
        过滤抽奖函数
        :param lot_det:
        :return:
        """
        lot_det_sep = lot_det.split('\t')
        pubtime_str = lot_det_sep[3]
        comment_count_str = lot_det_sep[5]
        rep_count_str = lot_det_sep[6]
        lot_type = lot_det_sep[9]
        if lot_type == '抽奖动态的源动态':
            return True
        dt = datetime.datetime.strptime(pubtime_str, '%Y年%m月%d日 %H:%M')
        if dt.year < 2000:
            return False
        pub_ts = int(datetime.datetime.timestamp(datetime.datetime.strptime(pubtime_str, '%Y年%m月%d日 %H:%M')))
        official_verify = lot_det_sep[2]
        official_lot_desc = lot_det_sep[9]
        if official_lot_desc in ['预约抽奖', '官方抽奖', '充电抽奖']:
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
        with open(root_dir + relative_dir + 'log/过滤抽奖信息.csv', 'r', encoding='utf-8') as f:
            for i in f.readlines():
                all_lot_det.append(i.strip())
        filtered_list: list = list(filter(self.is_need_lot, all_lot_det))
        filtered_list.sort(key=lambda x: try_parse_int(x.split("\t")[5]), reverse=True)
        self.push_lot_csv(f"动态抽奖信息", filtered_list[0:10])  # {datetime.datetime.now().strftime('%m月%d日')}
        filtered_list.sort(key=lambda x: x.split("\t")[0], reverse=True)  # 按照降序排序
        return [x.split('\t')[0] for x in filtered_list]
    # </editor-fold>


if __name__ == '__main__':
    # 获取官方抽奖
    # a = GET_OTHERS_LOT_DYN()
    # resp = a.get_official_lot_dyn()
    # print(resp)


    b= GET_OTHERS_LOT_DYN()
    asyncio.run(b.get_new_dyn())
