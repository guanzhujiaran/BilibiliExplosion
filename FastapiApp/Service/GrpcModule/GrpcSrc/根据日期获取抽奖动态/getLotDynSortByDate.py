# -*- coding: utf-8 -*-
import datetime
import json
import time
from typing import Sequence
from Service.GetOthersLotDyn import manual_reply_judge
from Service.GrpcModule.GrpcSrc.SQLObject.models import Bilidyndetail
import pandas as pd
from log.base_log import myfastapi_logger
from Service.GrpcModule.Models.getLotDynSortByDate import MainConf
from Utils.通用.CommMethods import methods
from Service.GrpcModule.GrpcSrc.DynObjectClass import lotDynData
from Service.GrpcModule.GrpcSrc.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
from Utils.数据库.SqlalchemyTool import sqlalchemy_model_2_dict
import os


class LotDynSortByDate:
    def __init__(self, ):
        self.path = os.path.dirname(os.path.abspath(__file__))
        if not os.path.exists(os.path.join(self.path, 'result')):
            os.makedirs(os.path.join(self.path, 'result'))
        self.sql = grpc_sql_helper
        self.BAPI = methods()
        self.manual_reply_judge = manual_reply_judge

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

    def solve_dyn_gen(self, dyn_gen: Sequence[Bilidyndetail]) -> list[lotDynData]:
        lot_data: list[lotDynData] = []
        myfastapi_logger.debug(f"共需要判断{len(dyn_gen)}条动态")
        for idx,dyn in enumerate(dyn_gen):
            # myfastapi_logger.debug(f"正在判断第{idx + 1}条动态")
            try:
                dynData = json.loads(dyn.dynData if dyn.dynData else 'null', strict=False)
                # dynamic_content = ''.join([x.get('text') for x in dynData.get('extend').get('origDesc')])
                dynamic_content = ''

                # 安全检查：确保dynData有extend字段
                extend = dynData.get('extend')
                if not extend:
                    continue

                # 安全检查：onlyFansProperty可能不存在
                onlyFansProperty = extend.get('onlyFansProperty')
                if onlyFansProperty and onlyFansProperty.get('isOnlyFans'):
                    continue

                # 安全检查：opusSummary可能不存在
                opusSummary = extend.get('opusSummary')
                if opusSummary:
                    if opusSummary.get('title'):
                        title_text = opusSummary.get('title').get('text')
                        if title_text:
                            nodes = title_text.get('nodes')
                            if nodes:
                                dynamic_content += ''.join([x.get('rawText') for x in nodes])
                    if opusSummary.get('summary'):
                        summary_text = opusSummary.get('summary').get('text')
                        if summary_text:
                            nodes = summary_text.get('nodes')
                            if nodes:
                                dynamic_content += ''.join([x.get('rawText') for x in nodes])

                author_name = extend.get('origName')
                author_space = f"https://space.bilibili.com/{extend.get('uid')}/dynamic"
                if self.BAPI.daily_choujiangxinxipanduan(dynamic_content):
                    # myfastapi_logger.debug(f"忽略日常抽奖信息{dynamic_content}")
                    continue
                dyn_url = f"https://t.bilibili.com/{extend.get('dynIdStr')}"
                if self.BAPI.zhuanfapanduan(dynamic_content):
                    dyn_url += '?tab=2'
                moduels = dynData.get('modules')
                if not moduels:
                    continue
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
                            up = moduleAdditional.get('up')
                            if up:
                                cardType = up.get('cardType')
                                if cardType == 'upower_lottery':  # 12是充电抽奖
                                    lot_rid = up.get('dynamicId')
                                    lot_type = '充电抽奖'
                                elif cardType == 'reserve':  # 所有的预约
                                    if up.get('lotteryType') is not None:  # 10是预约抽奖
                                        lot_rid = up.get('rid')
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
                                    businessId = extend.get('businessId')
                                    if businessId:
                                        lot_rid = businessId
                                        lot_type = '官方抽奖'
                # 安全检查：origDesc可能不存在
                origDesc = extend.get('origDesc')
                if origDesc and not lot_rid:
                    for descNode in origDesc:
                        if descNode.get('type') == 'desc_type_lottery':
                            lot_rid = extend.get('businessId')
                            lot_type = '官方抽奖'

                premsg = self.BAPI.pre_msg_processing(dynamic_content)
                dynIdStr = extend.get('dynIdStr')
                if dynIdStr:
                    dynamic_calculated_ts = int(
                        (int(dynIdStr) + 6437415932101782528) / 4294939971.297)
                    pub_time = self.BAPI.timeshift(dynamic_calculated_ts)
                else:
                    pub_time = ''

                lot_dyn_data = lotDynData()
                lot_dyn_data.dyn_url = dyn_url
                lot_dyn_data.lot_rid = str(lot_rid)
                lot_dyn_data.dynamic_content = repr(dynamic_content)
                lot_dyn_data.lot_type = str(lot_type)
                lot_dyn_data.premsg = premsg
                lot_dyn_data.forward_count = str(forward_count)
                lot_dyn_data.comment_count = str(comment_count)
                lot_dyn_data.like_count = str(like_count)
                if self.manual_reply_judge.call('manual_reply_judge',dynamic_content):
                    lot_dyn_data.Manual_judge = True
                else:
                    lot_dyn_data.Manual_judge = False
                lot_dyn_data.pub_time = str(pub_time)
                lot_dyn_data.official_verify_type = str(official_verify_type)
                lot_dyn_data.author_name = author_name
                lot_dyn_data.author_space = author_space
                lot_data.append(lot_dyn_data)
            except Exception as e:
                myfastapi_logger.exception(f'解析数据出错：{e}\n原始数据：\n{dyn.dynData}')
        return lot_data

    async def main(self, conf: MainConf = MainConf()):
        """
        默认保留最近一个月的数据
        """
        if conf.between_ts is None:
            conf.between_ts = [int(time.time()) - 30 * 24 * 3600, int(time.time())]
        if conf.between_ts[1] > int(time.time()):  # 确保最大时间到当前时间截止
            conf.between_ts[1] = int(time.time())
        if conf.between_ts[0] >= conf.between_ts[1]:
            myfastapi_logger.error('开始时间必须小于结束时间')
            return
        myfastapi_logger.info('开始获取所有动态的抽奖信息')
        ts_list = self.get_split_ts(conf.between_ts)
        if conf.is_gen_zip:
            os.makedirs(conf.gen_zip_path, exist_ok=True)
        for ts in ts_list:
            date_start = datetime.date.fromtimestamp(ts[0])

            myfastapi_logger.info(
                f'当前进度【{ts_list.index(ts) + 1}/{len(ts_list)}】:{date_start}')
            dyn_gen: Sequence[Bilidyndetail] = await self.sql.query_dynData_by_date(ts)
            lot_data: list[lotDynData] = self.solve_dyn_gen(dyn_gen)
            df = pd.DataFrame(
                [x.author_space, x.dyn_url, x.author_name, x.official_verify_type, x.pub_time, x.dynamic_content,
                 x.comment_count, x.forward_count, x.like_count, x.Manual_judge,
                 x.lot_type,
                 x.lot_rid,
                 x.premsg,
                 ]
                for x in lot_data
            )
            if not df.empty:
                df.columns = ['发布者空间', '动态链接', 'up昵称', '账号类型', '发布时间', '动态内容', '评论数',
                              '转发数',
                              '点赞数',
                              '是否需要人工判断', '抽奖类型', '抽奖id', '需要携带的词']
                if not os.path.exists(os.path.join(self.path, f'result/{date_start.year}/{date_start.month}')):
                    os.makedirs(os.path.join(self.path, f'result/{date_start.year}/{date_start.month}'))
                df.to_csv(
                    os.path.join(self.path,
                                 f'result/{date_start.year}/{date_start.month}/{date_start.year}_{date_start.month}_{date_start.day}_抽奖信息.csv'),
                    index=False, sep='\t', encoding='utf-8')
            myfastapi_logger.info(f'{datetime.date.fromtimestamp(ts[0])}的动态处理完成，总计{df.columns}条属于抽奖动态！')
            if dyn_gen:
                if conf.is_gen_zip:
                    all_df = pd.DataFrame.from_records([sqlalchemy_model_2_dict(x) for x in dyn_gen])
                    myfastapi_logger.info(f'正在压缩{date_start}的文件，共{len(all_df)}条动态数据')
                    all_df.to_csv(
                        os.path.join(
                            conf.gen_zip_path,
                            f'{datetime.date.fromtimestamp(ts[0])}_bili_dyn_data.csv.gz'
                            .replace('/', '_')
                            .replace('-',
                                     '_')
                        ),
                        index=False,
                        compression='gzip'
                    )
                if conf.is_delete_generated_data:
                    myfastapi_logger.info('正在删除已生成的数据')
                    await self.sql.delete_dyn_detail_by_dyn_rids([x.rid for x in dyn_gen])
            else:
                myfastapi_logger.error(f'{date_start}没有动态数据，不进行数据库的切割备份操作！')


if __name__ == '__main__':
    a = LotDynSortByDate()
    b = a.manual_reply_judge.call('manual_reply_judge',"2025 小刘的生日会哈喽大家~\n3.2是我的生日 在此邀请各位参加3.2晚七点的生日会\n服务器 - 南亚关跨\n除了狗运笨蛋球 本次还增加了新项目 滚轮背背平冠挑战\n大家都有机会夺冠\n\n当晚kook语音频道: 81354114\n活动将")

    print(b)