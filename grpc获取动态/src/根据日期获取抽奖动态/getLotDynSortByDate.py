# -*- coding: utf-8 -*-
import datetime
# -*- coding: utf-8 -*-
import json
import time
from typing import Generator
import subprocess
from functools import partial
subprocess.Popen = partial(subprocess.Popen, encoding="utf-8")
import execjs
import pandas as pd
import Bilibili_methods.all_methods
from grpc获取动态.src.DynObjectClass import lotDynData
from grpc获取动态.src.SqlHelper import SQLHelper
"""
使用reg查询动态保存下来
"""
import os


class LotDynSortByDate:
    def __init__(self, ):
        self.path = os.path.dirname(os.path.abspath(__file__))
        if not os.path.exists(os.path.join(self.path,'result')):
            os.makedirs(os.path.join(self.path,'result'))
        self.sql = SQLHelper()
        self.BAPI = Bilibili_methods.all_methods.methods()
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
            'ns',
            'NS',
            'switch',
            'Switch'
        ]  # 需要重点查看的关键词列表
        self.manual_reply_judge = execjs.compile("""
                manual_reply_judge= function (dynamic_content) {
                            //判断是否需要人工回复 返回true需要人工判断  返回null不需要人工判断
                            //64和67用作判断是否能使用关键词回复
                            let none_lottery_word1 = /.*测试.{0,5}gua/gmi.test(dynamic_content)
                            if (none_lottery_word1) {
                                return true
                            }
                            dynamic_content = dynamic_content.replaceAll(/〖/gmi, '【')
                            dynamic_content = dynamic_content.replaceAll(/“/gmi, '"')
                            dynamic_content = dynamic_content.replaceAll(/”/gmi, '"')
                            dynamic_content = dynamic_content.replaceAll(/＠/gmi, '@')
                            dynamic_content = dynamic_content.replaceAll(/@.{0,8} /gmi, '')
                            dynamic_content = dynamic_content.replaceAll(/好友/gmi, '朋友')
                            dynamic_content = dynamic_content.replaceAll(/伙伴/gmi, '朋友')
                            dynamic_content = dynamic_content.replaceAll(/安利/gmi, '分享')
                            dynamic_content = dynamic_content.replaceAll(/【关注】/gmi, '')
                            dynamic_content = dynamic_content.replaceAll(/\?/gmi, '？')
                            let manual_re1 = /.*评论.{0,20}告诉|.*有关的评论|.*告诉.{0,20}留言/gmi.test(dynamic_content)
                            let manual_re2 = /.*评论.{0,20}理由|.*参与投稿.{0,30}有机会获得/gmi.test(dynamic_content)
                            let manual_re3 = /.*评论.{0,10}对|.*造.{0,3}句子/gmi.test(dynamic_content)
                            let manual_re4 = /.*猜赢|.*猜对|.*答对|.*猜到.{0,5}答案/gmi.test(dynamic_content)
                            let manual_re5 = /.*说.{0,10}说|.*谈.{0,10}谈|.*夸.{0,10}夸|评论.{0,10}写.{0,10}写|.*写下.{0,5}假如.{0,5}是|.*讨论.{0,10}怎么.{0,10}？/gmi.test(dynamic_content)
                            let manual_re7 = /.*最先猜中|.*带文案|.*许.{0,5}愿望/gmi.test(dynamic_content)
                            let manual_re8 = /.*新衣回/gmi.test(dynamic_content)
                            let manual_re9 = /.*留言.{0,10}建议|.*评论.{0,10}答|.*一句话证明|.*留言.{0,10}得分|.*有趣.{0,3}留言|.*有趣.{0,3}评论|.*留言.{0,3}晒出|.*评论.{0,3}晒出/gmi.test(dynamic_content)
                            let manual_re11 = /.*评论.{0,10}祝福|.*评论.{0,10}意见|.*意见.{0,10}评论|.*留下.{0,10}意见|.*留下.{0,15}印象|.*意见.{0,10}留下/gmi.test(dynamic_content)
                            let manual_re12 = /.*评论.{0,10}讨论|.*话题.{0,10}讨论|.*参与.{0,5}讨论/gmi.test(dynamic_content)
                            let manual_re14 = /.*评论.{0,10}说出|,*留言.{0,5}身高/gmi.test(dynamic_content)
                            let manual_re15 = /.*评论.{0,20}分享|.*评论.{0,20}互动((?!抽奖|,|，|来).)*$|.*评论.{0,20}提问|.*想问.{0,20}评论|.*想说.{0,20}评论|.*想问.{0,20}留言|.*想说.{0,20}留言/gmi.test(dynamic_content)
                            let manual_re16 = /.*评论.{0,10}聊.{0,10}聊/gmi.test(dynamic_content)
                            let manual_re17 = /.*评.{0,10}接力/gmi.test(dynamic_content)
                            let manual_re18 = /.*聊.{0,10}聊/gmi.test(dynamic_content)
                            let manual_re19 = /.*评论.{0,10}扣|.*评论.{0,5}说.{0,3}下/gmi.test(dynamic_content)
                            let manual_re20 = /.*转发.{0,10}分享/gmi.test(dynamic_content)
                            let manual_re21 = /.*评论.{0,10}告诉/gmi.test(dynamic_content)
                            let manual_re22 = /.*评论.{0,10}唠.{0,10}唠/gmi.test(dynamic_content)
                            let manual_re23 = /.*今日.{0,5}话题|.*参与.{0,5}话题|.*参与.{0,5}答题/gmi.test(dynamic_content)
                            let manual_re24 = /.*说.*答案|.*评论.{0,15}答案/gmi.test(dynamic_content)
                            let manual_re25 = /.*说出/gmi.test(dynamic_content)
                            let manual_re26 = /.*为.{0,10}加油/gmi.test(dynamic_content)
                            let manual_re27 = /.*评论.{0,10}话|.*你中意的|.*评.{0,10}你.{0,5}的|.*写上.{0,10}你.{0,5}的|.*写下.{0,10}你.{0,5}的/gmi.test(dynamic_content)
                            let manual_re28 = /.*评论.{0,15}最想做7的事|.*评.{0,15}最喜欢|.*评.{0,15}最.{0,7}的事|.*最想定制的画面/gmi.test(dynamic_content)
                            let manual_re29 = /.*分享.{0,20}经历|.*经历.{0,20}分享/gmi.test(dynamic_content)
                            let manual_re30 = /.*分享.{0,20}心情/gmi.test(dynamic_content)
                            let manual_re31 = /.*评论.{0,10}句/gmi.test(dynamic_content)
                            let manual_re32 = /.*转关评下方视频/gmi.test(dynamic_content)
                            let manual_re33 = /.*分享.{0,10}美好/gmi.test(dynamic_content)
                            let manual_re34 = /.*视频.{0,10}弹幕/gmi.test(dynamic_content)
                            let manual_re35 = /.*生日快乐/gmi.test(dynamic_content)
                            let manual_re36 = /.*一句话形容/gmi.test(dynamic_content)
                            let manual_re38 = /.*分享.{0,10}喜爱|.*分享.{0,10}最爱|.*推荐.{0,10}最爱|.*推荐.{0,10}喜爱/gmi.test(dynamic_content)
                            let manual_re39 = /.*分享((?!,|，).){0,10}最|.*评论((?!,|，).){0,10}最/gmi.test(dynamic_content)
                            let manual_re40 = /.*带话题.{0,15}晒|.*带话题.{0,15}讨论/gmi.test(dynamic_content)
                            let manual_re41 = /.*分享.{0,15}事|点赞.{0,3}数.{0,3}前/gmi.test(dynamic_content)
                            let manual_re42 = /.*送出.{0,15}祝福/gmi.test(dynamic_content)
                            let manual_re43 = /.*评论.{0,30}原因/gmi.test(dynamic_content)
                            let manual_re47 = /.*答案.{0,10}参与/gmi.test(dynamic_content)
                            let manual_re48 = /.*唠.{0,5}唠/gmi.test(dynamic_content)
                            let manual_re49 = /.*分享一下/gmi.test(dynamic_content)
                            let manual_re50 = /.*评论.{0,30}故事/gmi.test(dynamic_content)
                            let manual_re51 = /.*告诉.{0,30}什么|.*告诉.{0,30}最/gmi.test(dynamic_content)
                            let manual_re53 = /.*发布.{0,20}图.{0,5}动态/gmi.test(dynamic_content)
                            let manual_re54 = /.*视频.{0,20}评论/gmi.test(dynamic_content)
                            let manual_re55 = /.*复zhi|.*长按/gmi.test(dynamic_content)
                            let manual_re56 = /.*多少.{0,10}合适/gmi.test(dynamic_content)
                            let manual_re57 = /.*喜欢.{0,5}哪/gmi.test(dynamic_content)
                            let manual_re58 = /.*多少.{0,15}？|.*多少.{0,15}\?|.*有没有.{0,15}？|.*有没有.{0,15}\?|.*是什么.{0,15}？|.*是什么.{0,15}\?/gmi.test(dynamic_content)
                            let manual_re61 = /.*看.{0,10}猜/gmi.test(dynamic_content)
                            let manual_re63 = /.*评论.{0,10}猜|.*评论.{0,15}预测/gmi.test(dynamic_content)
                            let manual_re65 = /.*老规矩你们懂的/gmi.test(dynamic_content)
                            let manual_re67 = /.*[评|带]((?!抽奖|,|，|来).){0,7}“|.*[评|带]((?!抽奖|,|，|来).){0,7}"|.*[评|带]((?!抽奖|,|，|来).){0,7}【|.*[评|带]((?!抽奖|,|，|来).){0,7}:|.*[评|带]((?!抽奖|,|，|来).){0,7}：|.*[评|带]((?!抽奖|,|，|来).){0,7}「|.*带关键词.{0,7}"|.*评论关键词[“”‘’"']|.*留言((?!抽奖|,|，|来).){0,7}“|.*对出.{0,10}下联.{0,5}横批|.*回答.{0,8}问题|.*留下.{0,10}祝福语|.*留下.{0,10}愿望|.*找到.{0,10}不同的.{0,10}留言|.*答案放在评论区|.*几.{0,5}呢？|.*有奖问答|.*想到.{0,19}关于.{0,20}告诉|.*麻烦大伙评论这个|报暗号【.{0,4}】/gmi.test(dynamic_content)
                            let manual_re76 = /.*留言((?!抽奖|,|，|来).).{0,7}"|.*留下((?!抽奖|,|，|来).){0,5}“|.*留下((?!抽奖|,|，|来).){0,5}【|.*留下((?!抽奖|,|，|来).){0,5}:|.*留下((?!抽奖|,|，|来).){0,5}：|.*留下((?!抽奖|,|，|来).){0,5}「/gmi.test(dynamic_content)
                            let manual_re77 = /.*留言((?!抽奖|,|，|来).).{0,7}"|.*留言((?!抽奖|,|，|来).).{0,7}“|.*留言((?!抽奖|,|，|来).){0,7}【|.*留言((?!抽奖|,|，|来).){0,7}:|.*留言((?!抽奖|,|，|来).){0,7}：|.*留言((?!抽奖|,|，|来).){0,7}「/gmi.test(dynamic_content)
                            let manual_re64 = /和.{0,5}分享.{0,5}的|.*分享.{0,10}你的|.*正确回答|.*回答正确|.*评论.{0,10}计划|.*定.{0,10}目标.{0,5}？|.*定.{0,10}目标.{0,5}?|.*评论.{0,7}看的电影|.*如果.{0,20}觉得.{0,10}？|.*如果.{0,20}觉得.{0,10}\?|评论.{0,7}希望.{0,5}|.*竞猜[\s\S]{0,15}[答评]|.*把喜欢的.{0,10}评论|.*评论.{0,5}解.{0,5}密|.*这款.{0,10}怎么.{0,3}？|.*最喜欢.{0,5}的.*为什么？|.*留下.{0,15}的.{0,5}疑问|.*写下.{0,10}的.{0,5}问题/gmi.test(dynamic_content)
                            let manual_re6 = /.*@TA|.*@.{0,15}朋友|.*艾特|.*@.{0,3}你的|.*标记.{0,10}朋友|.*@{0,15}赞助商|.*发表你的新年愿望\+个人的昵称|.*抽奖规则请仔细看图片|.*带上用户名|.*活动详情请戳图片|.*@个人用户名|评论.{0,5}附带.{0,10}相关内容|回复.{0,5}视频.{0,10}相关内容|.*评论.{0,5}昵称/gmi.test(dynamic_content)
                            let manual_re62 = /.*评论.{0,10}#.*什么|.*转评.{0,3}#.*(?<=，)/gmi.test(dynamic_content)
                            let manual_re68 = /.*将.{0,10}内容.{0,10}评|.*打几分？/gmi.test(dynamic_content)
                            let manual_re70 = /.*会不会.{0,20}？|.*会不会.{0,20}\?|如何.{0,20}？|如何.{0,20}\?/gmi.test(dynamic_content)
                            let manual_re71 = /.*猜.{0,10}猜|.*猜.{0,10}比分|.*猜中.{0,10}获得|.*猜中.{0,10}送出/gmi.test(dynamic_content)
                            let manual_re72 = /.*生日|.*新年祝福/gmi.test(dynamic_content)
                            let manual_re73 = /.*知道.{0,15}什么.{0,15}？|.*知道.{0,15}什么.{0,15}\?|.*用什么|.*评.{0,10}收.{0,5}什么.{0.7}\?|.*评.{0,10}收.{0,5}什么.{0,7}？/gmi.test(dynamic_content)
                            let manual_re74 = /.*领.{0,10}红包.{0,5}大小|.*领.{0,10}多少.{0,10}红包|.*红包金额/gmi.test(dynamic_content)
                            let manual_re75 = /.*本周话题|.*互动话题|.*互动留言|.*互动时间|.*征集.{0,10}名字|.*投票.{0,5}选.{0,10}最.{0,5}的|.*一人说一个谐音梗|帮.{0,5}想想.{0,5}怎么/gmi.test(dynamic_content)

                            return manual_re1 || manual_re2 || manual_re3 || manual_re4 || manual_re5 || manual_re6 || manual_re7 || manual_re8 || manual_re9 ||
                                manual_re11 || manual_re12 || manual_re14 || manual_re15 || manual_re16 || manual_re17 || manual_re18 || manual_re19 || manual_re20 || manual_re21 || manual_re22 || manual_re23 || manual_re24 || manual_re25 ||
                                manual_re26 || manual_re27 || manual_re28 || manual_re29 || manual_re30 ||
                                manual_re31 || manual_re32 || manual_re33 || manual_re34 || manual_re35 ||
                                manual_re36 || manual_re38 || manual_re39 || manual_re40 ||
                                manual_re41 || manual_re42 || manual_re43 || manual_re76 ||
                                manual_re47 || manual_re48 || manual_re49 || manual_re50 || manual_re51 ||
                                manual_re53 || manual_re54 || manual_re58 || manual_re55 || manual_re56 ||
                                manual_re57 || manual_re61 || manual_re62 || manual_re63 || manual_re64 ||
                                manual_re65 || manual_re67 || manual_re68 || manual_re70 || manual_re71 || manual_re72 || manual_re73 ||
                                manual_re74 || manual_re75 || manual_re77 || manual_re77
                        }

                    """)

    def get_split_ts(self, between_ts: list[int]) -> list[list]:
        """
        根据日期划分时间戳，不包括当天的，到最后一天的前一天的时间戳为止
        :param between_ts:
        :return:
        """
        start_date_time = datetime.date.fromtimestamp(between_ts[0])
        end_date_time = datetime.date.fromtimestamp(between_ts[1])
        ret_list = []
        while end_date_time - start_date_time > datetime.timedelta(0):
            start_date_ts = int(time.mktime(time.strptime(str(start_date_time), '%Y-%m-%d')))
            end_date_ts = int(time.mktime(time.strptime(str(start_date_time + datetime.timedelta(1)), '%Y-%m-%d'))) - 1
            ret_list.append([start_date_ts, end_date_ts])
            start_date_time += datetime.timedelta(1)
        return ret_list

    def solve_dyn_gen(self, dyn_gen: Generator) -> list[lotDynData]:
        lot_data: list[lotDynData] = []
        for dyn in dyn_gen:
            dynData = json.loads(dyn.get('dynData'), strict=False)
            if not dynData.get('extend').get('origDesc'):
                continue
            # dynamic_content = ''.join([x.get('text') for x in dynData.get('extend').get('origDesc')])
            dynamic_content = ''
            if dynData.get('extend').get('onlyFansProperty').get('isOnlyFans'):
                continue
            if dynData.get('extend').get('opusSummary').get('title'):
                dynamic_content += ''.join([x.get('rawText') for x in
                                            dynData.get('extend').get('opusSummary').get('title').get('text').get(
                                                'nodes')])
            if dynData.get('extend').get('opusSummary').get('summary'):
                dynamic_content += ''.join([x.get('rawText') for x in
                                            dynData.get('extend').get('opusSummary').get('summary').get('text').get(
                                                'nodes')])
            author_name = dynData.get('extend').get('origName')
            author_space = f"https://space.bilibili.com/{dynData.get('extend').get('uid')}/dynamic"
            if self.BAPI.daily_choujiangxinxipanduan(dynamic_content):
                continue
            dyn_url = f"https://t.bilibili.com/{dynData.get('extend').get('dynIdStr')}"
            if self.BAPI.zhuanfapanduan(dynamic_content):
                dyn_url += '?tab=2'
            moduels = dynData.get('modules')
            lot_rid = ''
            lot_type = ''
            forward_count = '0'
            comment_count = '0'
            like_count = '0'
            official_verify_type = ''
            for module in moduels:
                if module.get('moduleAdditional'):
                    moduleAdditional = module.get('moduleAdditional')
                    if moduleAdditional.get('type') == 'additional_type_up_reservation':
                        # lot_id不能在这里赋值，需要在底下判断是否为抽奖之后再赋值
                        cardType = moduleAdditional.get('up').get('cardType')
                        if cardType == 'upower_lottery':  # 12是充电抽奖
                            lot_rid = moduleAdditional.get('up').get('dynamicId')
                            lot_type = '充电抽奖'
                        elif cardType == 'reserve':  # 所有的预约
                            if moduleAdditional.get('up').get('lotteryType') is not None:  # 10是预约抽奖
                                lot_rid = moduleAdditional.get('up').get('rid')
                                lot_type = '预约抽奖'
                if module.get('moduleButtom'):
                    moduleState = module.get('moduleButtom').get('moduleStat')
                    if moduleState:
                        forward_count = moduleState.get('repost') if moduleState.get('repost') else '0'
                        like_count = moduleState.get('like') if moduleState.get('like') else '0'
                        comment_count = moduleState.get('reply') if moduleState.get('reply') else '0'
                if module.get('moduleAuthor'):
                    author = module.get('moduleAuthor').get('author')
                    if author:
                        official_verify_type = str(author.get('official').get('type')) if author.get(
                            'official') and author.get('official').get('type') else '0'
                if module.get('moduleDesc'):
                    moduleDesc = module.get('moduleDesc')
                    desc = moduleDesc.get('desc')
                    if desc:
                        for descNode in desc:
                            if descNode.get('type') == 'desc_type_lottery':  # 获取官方抽奖，这里的比较全
                                lot_rid = dynData.get('extend').get('businessId')
                                lot_type = '官方抽奖'
            if dynData.get('extend').get('origDesc') and not lot_rid:
                for descNode in dynData.get('extend').get('origDesc'):
                    if descNode.get('type') == 'desc_type_lottery':
                        lot_rid = dynData.get('extend').get('businessId')
                        lot_type = '官方抽奖'

            premsg = self.BAPI.pre_msg_processing(dynamic_content)
            dynamic_calculated_ts = int(
                (int(dynData.get('extend').get('dynIdStr')) + 6437415932101782528) / 4294939971.297)
            pub_time = self.BAPI.timeshift(dynamic_calculated_ts)

            high_lights_list = []
            for i in self.highlight_word_list:
                if i in dynamic_content:
                    high_lights_list.append(i)

            LotDynData = lotDynData()
            LotDynData.dyn_url = dyn_url
            LotDynData.lot_rid = str(lot_rid)
            LotDynData.dynamic_content = repr(dynamic_content)
            LotDynData.lot_type = str(lot_type)
            LotDynData.premsg = premsg
            LotDynData.forward_count = str(forward_count)
            LotDynData.comment_count = str(comment_count)
            LotDynData.like_count = str(like_count)
            LotDynData.high_lights_list = high_lights_list
            LotDynData.Manual_judge = '人工判断' if self.manual_reply_judge.call("manual_reply_judge",
                                                                                 dynamic_content) else ''
            LotDynData.pub_time = str(pub_time)
            LotDynData.official_verify_type = str(official_verify_type)
            LotDynData.author_name = author_name
            LotDynData.author_space = author_space
            lot_data.append(LotDynData)

        return lot_data

    def main(self, between_ts=[int(time.time()) - 7 * 24 * 3600, int(time.time())],GenWordCloud=False):
        print('开始获取所有动态的抽奖信息')
        if between_ts[1] > int(time.time()):  # 确保最大时间到当前时间截止
            between_ts[1] = int(time.time())
        ts_list = self.get_split_ts(between_ts)
        for ts in ts_list:
            print(f'当前进度【{ts_list.index(ts) + 1}/{len(ts_list)}】:{datetime.date.fromtimestamp(ts[0])}')
            dyn_gen = self.sql.query_dynData_by_date(ts)
            lot_data: [lotDynData] = self.solve_dyn_gen(dyn_gen)
            df = pd.DataFrame(
                [x.author_space, x.dyn_url, x.author_name, x.official_verify_type, x.pub_time, x.dynamic_content,
                 x.comment_count, x.forward_count, x.like_count, x.Manual_judge,
                 ';'.join(x.high_lights_list),
                 x.lot_type,
                 x.lot_rid,
                 x.premsg,
                 ]
                for x in lot_data
            )
            df.columns = ['发布者空间', '动态链接', 'up昵称', '账号类型', '发布时间', '动态内容', '评论数', '转发数',
                          '点赞数',
                          '是否需要人工判断', '高亮关键词', '抽奖类型', '抽奖id', '需要携带的词']
            date_start = datetime.date.fromtimestamp(ts[0])
            if not os.path.exists(os.path.join(self.path , f'result/{date_start.year}/{date_start.month}')):
                os.makedirs(os.path.join(self.path , f'result/{date_start.year}/{date_start.month}'))
            df.to_csv(
                os.path.join(self.path , f'result/{date_start.year}/{date_start.month}/{date_start.year}_{date_start.month}_{date_start.day}_抽奖信息.csv'),
                index=False, sep='\t', encoding='utf-8')
            print(f'{datetime.date.fromtimestamp(ts[0])}的动态处理完成，总计{len(df)}条！')


if __name__ == '__main__':
    a = LotDynSortByDate()
    a.main([int(time.time()) - 60 * 3600 * 24, int(time.time())])
