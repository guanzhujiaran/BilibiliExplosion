import time
from dataclasses import dataclass, field
from datetime import datetime


# region 描述动态数据类
@dataclass
class DynStat:
    like: int = 0
    repost: int = 0
    reply: int = 0


@dataclass
class ObjDynCard:
    uid: str = ""
    uname: str = ""
    officialVerify: int = -1
    dynamicContent: str = ""
    dynType: str = ""
    dynamicId: str = ""
    businessId: str = ""
    isOfficialLot: bool = False
    pubTs: int = 0
    pubDateTime: datetime = datetime(1970, 1, 1, 0, 0, 0, 0)
    pubDateTimeStr: str = ""
    dynStat: DynStat = DynStat()
    origDynItem: dict = field(default_factory=dict)


@dataclass
class ObjDynInfo:
    cardType: str = ""
    itemType: str = ""
    uid: str = ""
    uname: str = ""
    dynamicId: str = ""
    dynCard: ObjDynCard = ObjDynCard()
    origDyn: ObjDynCard = ObjDynCard()


@dataclass
class ObjSpaceDyn:
    DynList: list[ObjDynInfo]
    historyOffset: str
    hasMore: bool


# endregion


class DynTool:
    @staticmethod
    def timeunshift(datetime_str: str) -> int:
        # 帮我写这个函数的注释
        timeArray = time.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        timeStamp = int(time.mktime(timeArray))
        return timeStamp

    @staticmethod
    def timeshift(timestamp: int) -> str:
        '''
        时间戳转换日期
        :param timestamp:
        :return:
        '''
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    @staticmethod
    def __solveDynItem(dynamic_item: dict) -> ObjDynCard:
        """
        解析动态item
        :param dynamic_item: 
        :return: 
        """
        if not dynamic_item.get('extend'):
            return ObjDynCard()
        uid: str = ""
        uname: str = ""
        officialVerify: int = -1
        dynamicContent: str = ""
        dynType: str = ""
        dynamicId: str = dynamic_item.get('extend').get('dynIdStr')
        businessId: str = dynamic_item.get('extend').get('businessId')
        isOfficialLot: bool = False
        pubTs: int = int((int(dynamicId) + 6437415932101782528) / 4294939971.297)
        pubDateTime: datetime = datetime.utcfromtimestamp(pubTs)
        pubDateTimeStr: str = DynTool.timeshift(pubTs)  # 通过公式获取大致的时间，误差大概20秒左右
        dynStat: DynStat = DynStat()
        origDynItem = dict()
        moduels = dynamic_item.get('modules')
        for module_item in moduels:
            if module_item.get('moduleAuthor'):
                module_author = module_item.get('moduleAuthor')
                uid = module_author.get('mid')
                uname = module_author.get('author').get('name')
                officialVerify = module_author.get('author').get('official').get('type') if module_author.get(
                    'author').get('official').get('type') else "0"
            if module_item.get('moduleDispute'):
                module_dispute = module_item.get('moduleDispute')
                dynamicContent += module_dispute.get('title', '') + module_dispute.get(
                    'desc', '')
            if module_item.get('moduleDesc'):
                moduleDesc = module_item.get('moduleDesc')
                desc = moduleDesc.get('desc')
                if desc:
                    for descNode in desc:
                        if descNode.get('type') == 'desc_type_lottery':  # 获取官方抽奖，这里的比较全
                            isOfficialLot = True
                        dynamicContent += descNode.get('text', '')
            if module_item.get('moduleDynamic'):
                module_dynamic = module_item.get('moduleDynamic')
                if module_dynamic.get('dynArchive'):
                    dynArchive = module_dynamic.get('dynArchive')
                    title = dynArchive.get('title', '')
                    cover = dynArchive.get('cover', '')
                    uri = dynArchive.get('uri', '')
                    coverLeftText1 = dynArchive.get('coverLeftText1', '')
                    coverLeftText2 = dynArchive.get('coverLeftText2', '')
                    coverLeftText3 = dynArchive.get('coverLeftText3', '')
                    avid = dynArchive.get('avid', '')
                    cid = dynArchive.get('cid', '')
                    duration = dynArchive.get('duration', '')
                    if title not in dynamicContent:
                        dynamicContent += title
                if module_dynamic.get('dynPgc'):
                    dyn_pgc = module_dynamic.get('dynPgc')
                    title = dyn_pgc.get('title', '')
                    cover = dyn_pgc.get('cover', '')
                    uri = dyn_pgc.get('uri', '')
                    coverLeftText1 = dyn_pgc.get('coverLeftText1', '')
                    coverLeftText2 = dyn_pgc.get('coverLeftText2', '')
                    coverLeftText3 = dyn_pgc.get('coverLeftText3', '')
                    cid = dyn_pgc.get('cid', '')
                    seasonId = dyn_pgc.get('seasonId', '')
                    epid = dyn_pgc.get('epid', '')
                    aid = dyn_pgc.get('aid', '')
                    if title not in dynamicContent:
                        dynamicContent += title
                if module_dynamic.get('dynCourSeason'):
                    dyn_cour_season = module_dynamic.get('dynCourSeason')
                    title = dyn_cour_season.get('title', '')
                    cover = dyn_cour_season.get('cover', '')
                    uri = dyn_cour_season.get('uri', '')
                    text1 = dyn_cour_season.get('text1', '')
                    desc = dyn_cour_season.get('desc', '')
                    avid = dyn_cour_season.get('avid', '')
                    cid = dyn_cour_season.get('cid', '')
                    epid = dyn_cour_season.get('epid', '')
                    duration = dyn_cour_season.get('duration', '')
                    seasonId = dyn_cour_season.get('seasonId', '')
                    if title not in dynamicContent:
                        dynamicContent += title
                    if text1 not in dynamicContent:
                        dynamicContent += text1
                    if desc not in dynamicContent:
                        dynamicContent += desc
                if module_dynamic.get('dynCourBatch'):
                    dyn_cour_batch = module_dynamic.get('dynCourBatch')
                    title = dyn_cour_batch.get('title', '')
                    cover = dyn_cour_batch.get('cover', '')
                    uri = dyn_cour_batch.get('uri', '')
                    text1 = dyn_cour_batch.get('text1', '')
                    text2 = dyn_cour_batch.get('text2', '')
                    avid = dyn_cour_batch.get('avid', '')
                    cid = dyn_cour_batch.get('cid', '')
                    epid = dyn_cour_batch.get('epid', '')
                    duration = dyn_cour_batch.get('duration', '')
                    seasonId = dyn_cour_batch.get('seasonId', '')
                    if title not in dynamicContent:
                        dynamicContent += title
                    if text1 not in dynamicContent:
                        dynamicContent += text1
                    if text2 not in dynamicContent:
                        dynamicContent += text2
                if module_dynamic.get('dynForward'):
                    # 套娃
                    dynForward = module_dynamic.get('dynForward')
                    origDynItem = dynForward.get('item')
                if module_dynamic.get('dynDraw'):
                    dyn_draw = module_dynamic.get('dynDraw')
                    uri = dyn_draw.get('uri', '')
                    cover = dyn_draw.get('cover', '')
                    id = dyn_draw.get('id', '')
                    isDrawFirst = dyn_draw.get('isDrawFirst', '')
                    isBigCover = dyn_draw.get('isBigCover', '')
                    isArticleCover = dyn_draw.get('isArticleCover', '')
                if module_dynamic.get('dynArticle'):
                    dyn_article = module_dynamic.get('dynArticle')
                    id = dyn_article.get('id', '')
                    uri = dyn_article.get('uri', '')
                    title = dyn_article.get('title', '')
                    desc = dyn_article.get('desc', '')
                    label = dyn_article.get('label', '')
                    templateID = dyn_article.get('templateID', '')
                    if title not in dynamicContent:
                        dynamicContent += title
                    if desc not in dynamicContent:
                        dynamicContent += desc
                if module_dynamic.get('dynMusic'):
                    dyn_music = module_dynamic.get('dynMusic')
                    id = dyn_music.get('id', '')
                    uri = dyn_music.get('uri', '')
                    upId = dyn_music.get('upId', '')
                    title = dyn_music.get('title', '')
                    cover = dyn_music.get('cover', '')
                    label1 = dyn_music.get('label1', '')
                    upper = dyn_music.get('upper', '')
                    if title not in dynamicContent:
                        dynamicContent += title
                if module_dynamic.get('dynCommon'):
                    dyn_common = module_dynamic.get('dynCommon')
                    oid = dyn_common.get('oid', '')
                    uri = dyn_common.get('uri', '')
                    title = dyn_common.get('title', '')
                    desc = dyn_common.get('desc', '')
                    cover = dyn_common.get('cover', '')
                    label = dyn_common.get('label', '')
                    bizType = dyn_common.get('bizType', '')
                    sketchID = dyn_common.get('sketchID', '')
                    if title not in dynamicContent:
                        dynamicContent += title
                    if desc not in dynamicContent:
                        dynamicContent += desc
                    if label not in dynamicContent:
                        dynamicContent += label
                if module_dynamic.get('dynCommonLive'):
                    dyn_common_live = module_dynamic.get('dynCommonLive')
                    id = dyn_common_live.get('id', '')
                    uri = dyn_common_live.get('uri', '')
                    title = dyn_common_live.get('title', '')
                    cover = dyn_common_live.get('cover', '')
                    cover_label = dyn_common_live.get('coverLabel', '')
                    cover_label2 = dyn_common_live.get('coverLabel2', '')
                    if title not in dynamicContent:
                        dynamicContent += title
                    if cover_label not in dynamicContent:
                        dynamicContent += cover_label
                    if cover_label2 not in dynamicContent:
                        dynamicContent += cover_label2
                if module_dynamic.get('dynMedialist'):
                    dynMedialist = module_dynamic.get('dynMedialist')
                    id = dynMedialist.get('id', '')
                    uri = dynMedialist.get('uri', '')
                    title = dynMedialist.get('title', '')
                    subTitle = dynMedialist.get('subTitle', '')
                    cover = dynMedialist.get('cover', '')
                    coverType = dynMedialist.get('coverType', '')
                    if title not in dynamicContent:
                        dynamicContent += title
                    if subTitle not in dynamicContent:
                        dynamicContent += subTitle
                if module_dynamic.get('dynApplet'):
                    dynApplet = module_dynamic.get('dynApplet')
                    id = dynApplet.get('id', '')
                    uri = dynApplet.get('uri', '')
                    title = dynApplet.get('title', '')
                    subTitle = dynApplet.get('subTitle', '')
                    cover = dynApplet.get('cover', '')
                    icon = dynApplet.get('icon', '')
                    label = dynApplet.get('label', '')
                    buttonTitle = dynApplet.get('buttonTitle', '')
                    if title not in dynamicContent:
                        dynamicContent += title
                    if subTitle not in dynamicContent:
                        dynamicContent += subTitle
                if module_dynamic.get('dynSubscription'):
                    dynSubscription = module_dynamic.get('dynSubscription')
                    id = dynSubscription.get('id', '')
                    adId = dynSubscription.get('adId', '')
                    uri = dynSubscription.get('uri', '')
                    title = dynSubscription.get('title', '')
                    cover = dynSubscription.get('cover', '')
                    adTitle = dynSubscription.get('adTitle', '')
                    tips = dynSubscription.get('tips', '')
                    if title not in dynamicContent:
                        dynamicContent += title
                    if adTitle not in dynamicContent:
                        dynamicContent += adTitle
                    if tips not in dynamicContent:
                        dynamicContent += tips
                if module_dynamic.get('dynLiveRcmd'):
                    dynLiveRcmd = module_dynamic.get('dynLiveRcmd')
                    content = dynLiveRcmd.get('content', '')
                    if content not in dynamicContent:
                        dynamicContent += content
                if module_dynamic.get('dynUgcSeason'):
                    dynUgcSeason = module_dynamic.get('dynUgcSeason')
                    title = dynUgcSeason.get('content', '')
                    cover = dynUgcSeason.get('cover', '')
                    uri = dynUgcSeason.get('uri', '')
                    coverLeftText1 = dynUgcSeason.get('coverLeftText1', '')
                    coverLeftText2 = dynUgcSeason.get('coverLeftText2', '')
                    coverLeftText3 = dynUgcSeason.get('coverLeftText3', '')
                    id = dynUgcSeason.get('id', '')
                    inlineURL = dynUgcSeason.get('inlineURL', '')
                    avid = dynUgcSeason.get('avid', '')
                    cid = dynUgcSeason.get('cid', '')
                    duration = dynUgcSeason.get('duration', '')
                    jumpUrl = dynUgcSeason.get('jumpUrl', '')
                    if title not in dynamicContent:
                        dynamicContent += title
                if module_dynamic.get('dynSubscriptionNew'):
                    dynSubscriptionNew = module_dynamic.get('dynSubscriptionNew')
                    if dynSubscriptionNew.get('item'):
                        if dynSubscriptionNew.get('item').get('dyn_subscription'):
                            dynSubscription = dynSubscriptionNew.get('item').get('dynSubscription')
                            id = dynSubscription.get('id', '')
                            adId = dynSubscription.get('adId', '')
                            uri = dynSubscription.get('uri', '')
                            title = dynSubscription.get('title', '')
                            cover = dynSubscription.get('cover', '')
                            adTitle = dynSubscription.get('adTitle', '')
                            tips = dynSubscription.get('tips', '')
                            if title not in dynamicContent:
                                dynamicContent += title
                            if adTitle not in dynamicContent:
                                dynamicContent += adTitle
                            if tips not in dynamicContent:
                                dynamicContent += tips
                        if dynSubscriptionNew.get('item').get('dynLiveRcmd'):
                            dynLiveRcmd = dynSubscriptionNew.get('item').get('dynLiveRcmd')
                            content = dynLiveRcmd.get('content', '')
                            if content not in dynamicContent:
                                dynamicContent += content
                if module_dynamic.get('dynCourBatchUp'):
                    dynCourBatchUp = module_item.get('dynCourBatchUp')
                    title = dynCourBatchUp.get('title', '')
                    desc = dynCourBatchUp.get('desc', '')
                    cover = dynCourBatchUp.get('cover', '')
                    uri = dynCourBatchUp.get('uri', '')
                    text1 = dynCourBatchUp.get('text1', '')
                    avid = dynCourBatchUp.get('avid', '')
                    cid = dynCourBatchUp.get('cid', '')
                    epid = dynCourBatchUp.get('epid', '')
                    duration = dynCourBatchUp.get('duration', '')
                    seasonId = dynCourBatchUp.get('seasonId', '')
                    if title not in dynamicContent:
                        dynamicContent += title
                    if desc not in dynamicContent:
                        dynamicContent += desc
                if module_dynamic.get('dynTopicSet'):
                    # 话题集合
                    pass
            if module_item.get('moduleAdditional'):
                moduleAdditional = module_item.get('moduleAdditional')
                # AdditionalType
                # additional_none = 0; // 占位
                # additional_type_pgc = 1; // 附加卡 - 追番
                # additional_type_goods = 2; // 附加卡 - 商品
                # additional_type_vote = 3; // 附加卡投票
                # additional_type_common = 4; // 附加通用卡
                # additional_type_esport = 5; // 附加电竞卡
                # additional_type_up_rcmd = 6; // 附加UP主推荐卡
                # additional_type_ugc = 7; // 附加卡 - ugc
                # additional_type_up_reservation = 8; // UP主预约卡
                if moduleAdditional.get('type') == 'additional_type_up_reservation':  # UP主预约卡
                    # lot_id不能在这里赋值，需要在底下判断是否为抽奖之后再赋值
                    cardType = moduleAdditional.get('up').get('cardType')
                    if cardType == 'upower_lottery':  # 12是充电抽奖
                        # lot_rid = moduleAdditional.get('up').get('dynamicId')
                        # lot_notice_res = self.get_lot_notice(12, lot_rid)
                        # lot_data = lot_notice_res.get('data')
                        # lot_id = lot_data.get('lottery_id')
                        isOfficialLot = True
                    elif cardType == 'reserve':  # 所有的预约
                        if moduleAdditional.get('up').get('lotteryType') is not None:  # 10是预约抽奖
                            isOfficialLot = True
                            # lot_rid = moduleAdditional.get('up').get('rid')
                            # lot_notice_res = self.get_lot_notice(10, lot_rid)
                            # lot_data = lot_notice_res.get('data')
                            # lot_id = lot_data.get('lottery_id')
                elif moduleAdditional.get('type') == 'additional_type_ugc':
                    pass
                elif moduleAdditional.get('type') == 'additional_type_common':
                    pass
                elif moduleAdditional.get('type') == 'additional_type_goods':
                    pass
                elif moduleAdditional.get('type') == 'additional_type_vote':
                    pass
                elif moduleAdditional.get('type') == 'addition_vote_type_word':
                    pass
                elif moduleAdditional.get('type') == 'addition_vote_type_default':
                    pass
                else:
                    pass
            if module_item.get('moduleStat'):
                moduleStat = module_item.get('moduleStat')
                repost = int(moduleStat.get('repost', '0'))
                like = int(moduleStat.get('like', '0'))
                reply = int(moduleStat.get('reply', '0'))
                dynStat = DynStat(like=like, repost=repost, reply=reply)
            if module_item.get('moduleOpusSummary'):
                moduleOpusSummary = module_item.get('moduleOpusSummary')
                title = moduleOpusSummary.get('title',{})
                title_text = title.get('text', {})
                if title_text:
                    for textNode in title_text.get('nodes'):
                        dynamicContent += textNode.get('rawText', '')
                summary = moduleOpusSummary.get('summary')
                summary_text = summary.get('text')
                if summary_text:
                    for textNode in summary_text.get('nodes'):
                        dynamicContent += textNode.get('rawText', '')
            if module_item.get('moduleParagraph'):
                moduleParagraph = module_item.get('moduleParagraph')
                para_text = moduleParagraph.get('paragraph')
                if para_text:
                    for textNode in para_text.get('nodes'):
                        dynamicContent += textNode.get('rawText', '')
            # 获取原动态的信息

            # 转发模块
            if module_item.get('moduleAuthorForward'):
                moduleAuthorForward = module_item.get('moduleAuthorForward')
                title = moduleAuthorForward.get('title')
                for moduleAuthorForwardTitle in title:
                    uname = moduleAuthorForwardTitle.get('text').replace('@', '')
                url = moduleAuthorForward.get('url')
                uid = moduleAuthorForward.get('uid')
                ptime_label_text = moduleAuthorForward.get('ptime_label_text')
                show_follow = moduleAuthorForward.get('show_follow')
                face_url = moduleAuthorForward.get('face_url')
            if module_item.get('moduleStatForward'):
                moduleStatForward = module_item.get('moduleStatForward')
                repost = int(moduleStatForward.get('repost', '0'))
                like = int(moduleStatForward.get('like', '0'))
                reply = int(moduleStatForward.get('reply', '0'))
                dynStat = DynStat(like=like, repost=repost, reply=reply)

        return ObjDynCard(
            uid=uid,
            uname=uname,
            officialVerify=officialVerify,
            dynamicContent=dynamicContent,
            dynType=dynType,
            dynamicId=dynamicId,
            businessId=businessId,
            isOfficialLot=isOfficialLot,
            pubTs=pubTs,
            pubDateTime=pubDateTime,
            pubDateTimeStr=pubDateTimeStr,
            dynStat=dynStat,
            origDynItem=origDynItem,
        )

    @staticmethod
    def solve_space_dyn(resp: dict) -> ObjSpaceDyn:
        historyOffset = resp.get("historyOffset")
        hasMore = resp.get("hasMore")
        if not resp.get('list'):
            return ObjSpaceDyn(
                DynList=[],
                historyOffset=historyOffset,
                hasMore=hasMore
            )
        DynList = []
        for DynamicItem in resp.get('list'):
            cardType = DynamicItem.get('cardType')
            itemType = DynamicItem.get('itemType')
            uid = DynamicItem.get('extend').get('uid')
            dynamicId = DynamicItem.get('extend').get('dynIdStr')
            dynCard = DynTool.__solveDynItem(DynamicItem)
            origDyn = ObjDynCard()
            if dynCard.origDynItem:
                origDyn = DynTool.__solveDynItem(dynCard.origDynItem)
            DynList.append(
                ObjDynInfo(
                    cardType=cardType,
                    itemType=itemType,
                    uid=uid,
                    uname=dynCard.uname,
                    dynamicId=dynamicId,
                    dynCard=dynCard,
                    origDyn=origDyn,
                )
            )

        return ObjSpaceDyn(
            DynList=DynList,
            historyOffset=historyOffset,
            hasMore=hasMore
        )
