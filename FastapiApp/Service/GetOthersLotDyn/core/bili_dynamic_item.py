import asyncio
import datetime
import json
import os
import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Union

from log.base_log import get_others_lot_logger as get_others_lot_log
from Models.lottery_database.bili.LotteryDataModels import OfficialLotType
from Service.GetOthersLotDyn.parser.dynamic_detail_parsed import DynamicDetailParsed
from Service.GetOthersLotDyn.parser.dynamic_detail_parser import parse_dynamic_item
from Service.GetOthersLotDyn.filter.manual_reply_judge import manual_reply_judge
from Service.GetOthersLotDyn.parser.prize_extractor import extract_prize_info
from Service.MQ.base.MQClient.BiliLotDataPublisher import BiliLotDataPublisher
from Service.GetOthersLotDyn.Sql.models import TLotdyninfo
from Service.GetOthersLotDyn.Sql.sql_helper import SqlHelper
from Service.GrpcModule.Grpc.Bapi.BiliApi import get_polymer_web_dynamic_detail
from Utils.推送.PushMe import a_pushme
from Utils.代理.mdoel.RequestConf import RequestConf

_is_use_available_proxy = True


class FileMap(StrEnum):
    current_file_path = os.path.dirname(os.path.abspath(__file__))
    github_bili_upload = os.path.join(
        current_file_path, '../../../../github/bili_upload')


@dataclass
class BiliDynamicItemJudgeLotteryResult:
    cur_dynamic: TLotdyninfo | None = field(
        default=None)  # 如果是本来就判断过的，那么同样设置成None
    orig_dynamic: TLotdyninfo | None = field(default=None)
    attached_card: TLotdyninfo | None = field(default=None)


@dataclass
class BiliDynamicItem:
    dynamic_id: int | str = field(default=0, )  # 动态类型
    dynamic_type: int | str = field(default=2, )  # 动态类型
    dynamic_rid: int | str = field(default=0, )  # 动态rid
    dynamic_raw_resp: dict = field(
        default_factory=dict, )  # 返回的响应，带code和data的dict
    dynamic_raw_detail: DynamicDetailParsed = field(
        default_factory=DynamicDetailParsed)  # 动态详情解析结果模型
    bili_judge_lottery_result: BiliDynamicItemJudgeLotteryResult = field(
        default_factory=BiliDynamicItemJudgeLotteryResult)
    is_lot_orig: bool = field(default=False)  # 是否是抽奖动态的原动态
    is_use_available_proxy: bool = field(default=_is_use_available_proxy)

    def __post_init__(self):
        if not self.dynamic_id and not (self.dynamic_rid and self.dynamic_type):
            get_others_lot_log.critical('BiliDynamicItem初始化失败：缺少有效的动态标识（需要dynamic_id或dynamic_rid+dynamic_type）')
            raise ValueError('没有有效的动态信息！')

    def __hash__(self):
        if self.dynamic_id:
            return hash(int(self.dynamic_id))
        return hash(- int(self.dynamic_type) - int(self.dynamic_rid))

    async def _init(self):
        if not self.dynamic_id and self.dynamic_rid and self.dynamic_type:
            self.dynamic_id = await SqlHelper.getDynIdByRidType(self.dynamic_rid, self.dynamic_type)

    async def __solve_dynamic_item_detail(self, dynamic_detail_resp: dict) -> DynamicDetailParsed:
        """
        使用代理获取动态详情，传入空间的动态响应前，需要先构建成单个动态的响应！！！
        委托给 dynamic_detail_parser.parse_dynamic_item 进行纯数据解析，
        本方法仅负责网络重试逻辑（412/None/动态ID不匹配等）。
        :param dynamic_detail_resp: 动态详情响应字典
        :return: DynamicDetailParsed 解析结果模型
        """
        get_others_lot_log.debug(f'正在解析动态详情：{self.dynamic_id}')
        try:
            result = parse_dynamic_item(self.dynamic_id, dynamic_detail_resp)
            if not result.is_valid():
                code = dynamic_detail_resp.get('code')
                # 动态不存在 (4101131) 或 data 为 None，parse_dynamic_item 已处理，不重试
                if code == 4101131 or dynamic_detail_resp.get('data') is None:
                    return result
                # 动态ID不匹配，重新获取
                get_others_lot_log.critical(
                    f"API返回的动态ID与期望的不匹配，将强制通过API重新获取，dynamic_id={self.dynamic_id}")
                new_req = await self._get_dyn_detail_resp(force_api=True)
                return await self.__solve_dynamic_item_detail(new_req)
            return result
        except Exception as e:
            get_others_lot_log.exception(
                f'解析动态详情失败，dynamic_id={self.dynamic_id}，动态链接=https://t.bilibili.com/{self.dynamic_id}\nerror={e}\nresp={dynamic_detail_resp}')
            code = dynamic_detail_resp.get('code')
            if code == -412:
                get_others_lot_log.info('触发B站412风控，等待10秒后重试')
                await asyncio.sleep(10)
                new_req = await self._get_dyn_detail_resp(force_api=True)
                return await self.__solve_dynamic_item_detail(new_req)
            elif code == 4101128:
                get_others_lot_log.info(f'动态被B站屏蔽或不可见，code=4101128，msg={dynamic_detail_resp.get("message")}')
            elif code is None:
                get_others_lot_log.info('动态响应中缺少code字段，可能响应格式异常，将重新获取')
                new_req = await self._get_dyn_detail_resp(force_api=True)
                return await self.__solve_dynamic_item_detail(new_req)
            else:
                get_others_lot_log.critical(
                    f'动态详情解析失败，未知错误码code={code}，dynamic_id={self.dynamic_id}，等待10秒后重试')
                await asyncio.sleep(10)
                new_req = await self._get_dyn_detail_resp(force_api=True)
                return await self.__solve_dynamic_item_detail(new_req)
            return DynamicDetailParsed()

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
            # 看动态数据库里面有没有
            is_dyn_exist = await SqlHelper.isExistDynInfoByDynId(self.dynamic_id)
            if is_dyn_exist:
                dynamic_detail_resp = is_dyn_exist.rawJsonStr
                if dynamic_detail_resp is not None:
                    get_others_lot_log.debug(
                        f'动态【{self.dynamic_id}】在动态数据库中已存在，直接使用数据库缓存数据')
                    dynamic_req = {
                        'code': 0,
                        'data': {
                            "item": dynamic_detail_resp
                        }
                    }
                else:
                    get_others_lot_log.debug(
                        f'动态【{self.dynamic_id}】在动态数据库中存在但officialLotType={is_dyn_exist.officialLotType}，需要通过API重新获取完整数据')
            else:
                get_others_lot_log.warning(
                    f'动态【{self.dynamic_id}】不在动态数据库中，尝试从空间数据库查找')

            if not bool(dynamic_detail_resp):  # 如果动态数据库里面的还是需要获取api，那就查看空间数据库的内容
                # 看空间里面有没有
                is_space_exist = await SqlHelper.isExistSpaceInfoByDynId(self.dynamic_id)
                if is_space_exist:
                    # get_others_lot_log.critical(f'存在过的动态！！！{isDynExist.__dict__}')
                    dynamic_detail_resp = is_space_exist.spaceRespJson
                    if dynamic_detail_resp is not None:
                        get_others_lot_log.debug(
                            f'动态【{self.dynamic_id}】在空间数据库中已存在，直接使用数据库缓存数据')
                        dynamic_req = {
                            'code': 0,
                            'data': {
                                "item": dynamic_detail_resp
                            }
                        }
                    else:
                        get_others_lot_log.warning(
                            f'动态【{self.dynamic_id}】在空间数据库中存在但spaceRespJson为None，需要通过API获取')
                else:
                    get_others_lot_log.warning(
                        f'动态【{self.dynamic_id}】不在空间数据库中，需要通过API获取')

        force_api = not bool(dynamic_detail_resp)  # 查看是否缺少模块，缺少模块就强制重新获取
        try:
            if not dynamic_req or force_api:
                get_others_lot_log.debug(
                    f'动态【{self.dynamic_id}】数据库中无缓存或数据不完整，通过B站API获取动态详情')
                if str(self.dynamic_type) != '2' and not self.dynamic_id:
                    dynamic_req = await get_polymer_web_dynamic_detail(
                        rid=self.dynamic_rid,
                        dynamic_type=self.dynamic_type,
                        request_conf=RequestConf(
                            is_use_available_proxy=self.is_use_available_proxy)
                    )
                else:
                    dynamic_req = await get_polymer_web_dynamic_detail(
                        dynamic_id=self.dynamic_id,
                        request_conf=RequestConf(
                            is_use_available_proxy=self.is_use_available_proxy)
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
                raise ValueError(f'未知的官方抽奖类型：{lot_type}，无法确定business_type和business_id')
            await BiliLotDataPublisher.pub_official_reserve_charge_lot(
                business_type=business_type,
                business_id=business_id,
                origin_dynamic_id=dyn_id,
                extra_routing_key='GetOthersLotDyn.solve_official_lot_data'
            )
        except Exception as e:
            get_others_lot_log.exception(f'官方抽奖数据提取并发布到MQ失败，dyn_id={dyn_id}，lot_type={lot_type}，official_lot_id={official_lot_id}\nerror={e}')

    async def judge_lottery(self,
                            lotRound_id: int
                            ) -> BiliDynamicItemJudgeLotteryResult:
        """
        判断是否是抽奖 并且存储到数据库
        :param lotRound_id:
        :return:
        """
        await self._init()
        get_others_lot_log.debug(f'正在判断抽奖动态：{self.dynamic_id}')
        cur_dynamic = None
        orig_dynamic = None
        attached_card = None
        is_lot = True
        if self.dynamic_id:
            t_lot_dyn_info = await SqlHelper.getDynInfoByDynamicId(self.dynamic_id)
            if t_lot_dyn_info:  # 如果是本轮没有跑完的，那就添加进去
                if t_lot_dyn_info.dynLotRound_id == lotRound_id:
                    self.bili_judge_lottery_result = BiliDynamicItemJudgeLotteryResult(
                        cur_dynamic=t_lot_dyn_info)
                # else:
                #     self.bili_judge_lottery_result = BiliDynamicItemJudgeLotteryResult()  # 这个是以前的动态，不加进去了
                #     return self.bili_judge_lottery_result
        await self._solve_dynamic_item_detail()
        dynamic_detail = self.dynamic_raw_detail
        try:
            if dynamic_detail and dynamic_detail.dynamic_id:
                # 获取正确的动态id，不然可能会是rid或者aid
                dynamic_detail_dynamic_id = dynamic_detail.dynamic_id
                dynamic_content = dynamic_detail.dynamic_content
                author_name = dynamic_detail.author_name
                pub_time = dynamic_detail.pub_time
                pub_ts = dynamic_detail.pub_ts
                comment_count = dynamic_detail.comment_count
                forward_count = dynamic_detail.forward_count
                like_count = dynamic_detail.like_count
                official_verify_type = dynamic_detail.official_verify_type
                author_uid = dynamic_detail.author_uid
                rid = dynamic_detail.rid
                _type = dynamic_detail.type
                module_dynamic: dict = dynamic_detail.module_dynamic
                rawJSON = dynamic_detail.rawJSON
                is_official_lot = False
                is_charge_lot = False
                is_reserve_lot = False
                lot_rid = ''
                # O(1) 直接按键取值，替代原先 O(n) 遍历 module_dynamic.items()
                # 原逻辑：additional 命中 charge/reserve 时 break，major/desc 仅在未命中时检查
                additional = module_dynamic.get('additional')
                if additional:
                    upower_lottery = additional.get('upower_lottery')
                    if upower_lottery:
                        lot_rid = str(upower_lottery.get('rid'))
                        is_charge_lot = True
                    else:
                        reserve = additional.get('reserve')
                        if reserve and 'lottery/result' in json.dumps(reserve):
                            lot_rid = reserve.get('rid')
                            is_reserve_lot = True
                # 仅在未命中 charge/reserve 时检查 official lot
                if not is_charge_lot and not is_reserve_lot:
                    major = module_dynamic.get('major')
                    if major and major.get('type') == 'MAJOR_TYPE_OPUS':
                        for nodes in (major.get('opus') or {}).get('summary', {}).get('rich_text_nodes', []) or []:
                            if nodes.get('type') == 'RICH_TEXT_NODE_TYPE_LOTTERY':
                                is_official_lot = True
                                lot_rid = str(nodes.get('rid'))
                                break
                    if not is_official_lot:
                        desc_md = module_dynamic.get('desc')
                        if desc_md:
                            for nodes in desc_md.get('rich_text_nodes', []) or []:
                                if nodes.get('type') == 'RICH_TEXT_NODE_TYPE_LOTTERY':
                                    is_official_lot = True
                                    lot_rid = str(nodes.get('rid'))
                                    break
                if dynamic_content != '':
                    # deadline = self.nlp.information_extraction(dynamic_content, ['开奖日期'])['开奖日期']
                    deadline = None
                else:
                    get_others_lot_log.info(
                        f'动态内容为空，无法提取抽奖信息，动态链接=https://t.bilibili.com/{dynamic_detail_dynamic_id}?type={self.dynamic_type}')
                    deadline = None
                prize_result = await extract_prize_info(dyn_content=dynamic_content)
                premsg = prize_result.result.required_topic_text
                need_repost = prize_result.result.need_repost
                ret_url = f'https://t.bilibili.com/{dynamic_detail_dynamic_id}'
                if need_repost:
                    ret_url += '?tab=2'
                manual_judge = False
                if await asyncio.to_thread(manual_reply_judge.call, 'manual_reply_judge', dynamic_content):
                    manual_judge = True
                if re.match(r'.*//@.*', str(dynamic_content), re.DOTALL) is not None:
                    dynamic_content = re.findall(
                        r'(.*?)//@', dynamic_content, re.DOTALL)[0]
                # is_lot 逻辑：官方抽奖=1，预约/充电=0，其他用 extract_prize_info
                if is_official_lot:
                    is_lot = True
                elif is_reserve_lot or is_charge_lot:
                    is_lot = False
                elif not self.is_lot_orig:
                    if not prize_result.result.is_lot:
                        if comment_count > 2000 or forward_count > 1000:  # 评论或转发超多的就算不是抽奖动态也要加进去凑个数
                            pass
                        else:
                            is_lot = False
                else:
                    is_lot = True
                official_lot_type = OfficialLotType.official_lot if is_official_lot else OfficialLotType.charge_lot if is_charge_lot else OfficialLotType.reserve_lot if is_reserve_lot else None
                cur_dynamic = TLotdyninfo(dynId=dynamic_detail_dynamic_id,
                                          dynamicUrl=ret_url,
                                          authorName=author_name,
                                          up_uid=author_uid,
                                          pubTime=datetime.datetime.fromtimestamp(
                                              int(pub_ts)),
                                          dynContent=dynamic_content,
                                          commentCount=comment_count,
                                          repostCount=forward_count,
                                          likeCount=like_count,
                                          officialLotType=official_lot_type,
                                          officialLotId=str(lot_rid),
                                          isOfficialAccount=int(
                                              official_verify_type if official_verify_type else 0),
                                          isManualReply=int(manual_judge),
                                          isLot=int(is_lot),
                                          hashTag=premsg,
                                          dynLotRound_id=lotRound_id,
                                          rawJsonStr=rawJSON)
                await SqlHelper.addDynInfo(
                    cur_dynamic
                )

                try:
                    if is_official_lot or is_reserve_lot or is_charge_lot:
                        await self._solve_official_lot_data(str(dynamic_detail_dynamic_id), official_lot_type, lot_rid)
                except Exception as e:
                    get_others_lot_log.exception(f'提交官方/预约/充电抽奖数据到MQ失败，dynamic_id={dynamic_detail_dynamic_id}，lot_type={official_lot_type}，lot_rid={lot_rid}\nerror={e}')
                if dynamic_detail.orig_dynamic_id:
                    orig_dynamic_id = dynamic_detail.orig_dynamic_id
                    orig_name = dynamic_detail.orig_name
                    orig_pub_ts = dynamic_detail.orig_pub_ts
                    orig_dynamic_content = dynamic_detail.orig_dynamic_content
                    orig_comment_count = dynamic_detail.orig_comment_count
                    orig_forward_count = dynamic_detail.orig_forward_count
                    orig_official_verify = dynamic_detail.orig_official_verify
                    dynamic_orig = dynamic_detail.dynamic_orig
                    orig_ret_url = f'https://t.bilibili.com/{orig_dynamic_id}'
                    if 'tab=2' in ret_url:
                        orig_ret_url += '?tab=2'
                    elif orig_dynamic_content and (await extract_prize_info(dyn_content=orig_dynamic_content)).result.need_repost:
                        orig_ret_url += '?tab=2'
                    orig_dynamic = TLotdyninfo(
                        dynId=orig_dynamic_id,
                        dynamicUrl=orig_ret_url,
                        authorName=orig_name,
                        up_uid=author_uid,
                        pubTime=datetime.datetime.fromtimestamp(
                            int(orig_pub_ts)),
                        dynContent=orig_dynamic_content,
                        commentCount=orig_comment_count,
                        repostCount=orig_forward_count,
                        likeCount=like_count,
                        officialLotType=OfficialLotType.lot_dyn_origin_dyn,
                        officialLotId=None,
                        isOfficialAccount=orig_official_verify if type(
                            orig_official_verify) is int else 0,
                        isManualReply=int(manual_judge),
                        isLot=int(is_lot),
                        hashTag=premsg,
                        dynLotRound_id=lotRound_id,
                        rawJsonStr=dynamic_orig
                    )
                    await SqlHelper.addDynInfo(
                        orig_dynamic
                    )
                if is_lot:
                    if dynamic_detail.module_dynamic:
                        if dynamic_detail.module_dynamic.get('additional'):
                            if dynamic_detail.module_dynamic.get('additional').get(
                                    'type') == 'ADDITIONAL_TYPE_UGC':
                                ugc = dynamic_detail.module_dynamic.get(
                                    'additional').get('ugc')
                                aid_str = ugc.get('id_str')
                                if aid_str:
                                    aid_dynamic_item = BiliDynamicItem(
                                        dynamic_rid=aid_str,
                                        dynamic_type=8,
                                        is_lot_orig=True,
                                        is_use_available_proxy=self.is_use_available_proxy
                                    )
                                    await aid_dynamic_item.judge_lottery(lotRound_id)
                                    attached_card = aid_dynamic_item.bili_judge_lottery_result.cur_dynamic if aid_dynamic_item.bili_judge_lottery_result else None
                                else:
                                    get_others_lot_log.critical(
                                        f'附加视频(UGC)动态缺少id_str字段，无法进一步获取抽奖信息\ndynamic_detail={dynamic_detail}')
            else:
                get_others_lot_log.info(
                    f'动态已失效（被删除或不可见），记录为失效动态，dynamic_id={self.dynamic_id}，链接=https://t.bilibili.com/{self.dynamic_id}')
                cur_dynamic = TLotdyninfo(
                    dynId=str(self.dynamic_id) if self.dynamic_id else 0,
                    dynamicUrl=f'https://t.bilibili.com/{self.dynamic_id}',
                    authorName='',
                    up_uid=-1,
                    pubTime=datetime.datetime.fromtimestamp(86400),
                    dynContent='',
                    commentCount=-1,
                    repostCount=-1,
                    likeCount=-1,
                    officialLotType=None,
                    officialLotId=None,
                    isOfficialAccount=-1,
                    isManualReply=0,
                    isLot=-1,
                    hashTag='',
                    dynLotRound_id=lotRound_id,
                    rawJsonStr=dynamic_detail.rawJSON
                )
                await SqlHelper.addDynInfo(
                    cur_dynamic
                )
        except Exception as e:
            get_others_lot_log.exception(
                f'判断抽奖动态时发生异常，dynamic_id={dynamic_detail.dynamic_id if dynamic_detail else "None"}\nerror={e}')
            await a_pushme(f'【fastapi】判断抽奖动态异常', f"dynamic_id={dynamic_detail.dynamic_id if dynamic_detail else 'None'}\nerror={e}")
            await asyncio.sleep(30)
            return await self.judge_lottery(lotRound_id)
        judge_result = BiliDynamicItemJudgeLotteryResult(
            cur_dynamic=cur_dynamic,
            orig_dynamic=orig_dynamic,
            attached_card=attached_card,
        )
        self.bili_judge_lottery_result = judge_result
        return judge_result
