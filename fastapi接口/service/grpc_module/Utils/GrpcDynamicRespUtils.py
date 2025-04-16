#-*- coding:utf-8 -*-
import time
from dataclasses import dataclass, field
from datetime import datetime

from fastapi接口.log.base_log import BiliGrpcUtils_logger


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
        dynType = dynamic_item.get('cardType')
        moduels = dynamic_item.get('modules')
        for module_item in moduels:
            if module_item.get('moduleAuthor'):
                module_author = module_item.get('moduleAuthor')
                uid = module_author.get('mid')
                uname = module_author.get('author').get('name')
                officialVerify = module_author.get('author').get('official').get('type') if module_author.get(
                    'author').get('official').get('type') else "0"
                level = module_author.get('author').get('level')
            if module_item.get('moduleBlocked'):
                moduleBlocked = module_item.get('moduleBlocked')
                subHintMessage = moduleBlocked.get('subHintMessage')
                hintMessage = moduleBlocked.get('hintMessage')
                archiveTitle = moduleBlocked.get('archiveTitle')
                if hintMessage:
                    dynamicContent += hintMessage
                if subHintMessage:
                    dynamicContent += subHintMessage
                if archiveTitle:
                    dynamicContent += archiveTitle
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
                dynArchive = module_dynamic.get('dynArchive')
                if dynArchive:
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
                    dynCourBatchUp = module_dynamic.get('dynCourBatchUp')
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
                title = moduleOpusSummary.get('title', {})
                title_text = title.get('text', {})
                if title_text:
                    for textNode in title_text.get('nodes'):
                        dynamicContent += textNode.get('rawText', '')
                summary = moduleOpusSummary.get('summary')

                summary_text = summary.get('text', '') if summary else {}
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

            # 折叠模块
            if module_item.get('moduleFold'):
                moduleFold = module_item.get('moduleFold')
                foldType = moduleFold.get('foldType')
                text = moduleFold.get('text')
                foldUsers = moduleFold.get('foldUsers')
                for user in foldUsers:
                    uname = user.get('name')
                    officialVerify = user.get('official').get('type') if user.get('official').get('type') else "0"
                    level = user.get('level')
                    uid = user.get('mid')
                if text:
                    dynamicContent += text
        if not dynamicContent.strip():
            extend = dynamic_item.get('extend')
            if extend:
                origDesc = extend.get('origDesc')
                if origDesc:
                    for i in origDesc:
                        dynamicContent += i.get('text', '')
        if not dynamicContent.strip():
            BiliGrpcUtils_logger.critical(f'动态内容获取为空！检查一下解析响应的函数！\n{dynamic_item}')
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


if __name__ == '__main__':
    a = {'cardType': 'av', 'modules': [{'moduleType': 'module_author_forward', 'moduleAuthorForward': {'title': [{'text': '@DAME_ovo_', 'url': 'bilibili://space/33461313?defaultTab=dynamic'}], 'uid': '33461313', 'ptimeLabelText': '1月22日 · 发布了动态视频', 'showFollow': True, 'faceUrl': 'https://i0.hdslb.com/bfs/face/560b1516b2bd05910776b889e88cd74362f03875.jpg', 'relation': {'status': 'relation_status_nofollow', 'title': '未关注'}, 'tpList': [{'type': 'report', 'default': {'icon': 'https://i0.hdslb.com/bfs/feed-admin/d2a0449e705dcdeac1d2ac1e9da7e05d06b73dee.png', 'title': '举报', 'uri': 'bilibili://following/report?dynamicId=889384123832991766&uid=33461313&title=DAME_ovo_%3A%20%E8%A7%86%E9%A2%91'}}]}}, {'moduleType': 'module_dynamic', 'moduleDynamic': {'dynArchive': {'cover': 'http://i0.hdslb.com/bfs/archive/6e5bbf864dece212f03d12ef014aac78db8c23ad.jpg', 'uri': 'bilibili://video/284051701?aid=284051701&cid=1415455372&player_height=2200&player_preload=%7B%22expire_time%22%3A1706424442%2C%22cid%22%3A1415455372%2C%22quality%22%3A16%2C%22file_info%22%3A%7B%2216%22%3A%7B%22infos%22%3A%5B%7B%22filesize%22%3A218132%2C%22timelength%22%3A5461%7D%5D%7D%2C%2264%22%3A%7B%22infos%22%3A%5B%7B%22filesize%22%3A477800%2C%22timelength%22%3A5397%7D%5D%7D%7D%2C%22video_codecid%22%3A7%2C%22video_project%22%3Atrue%2C%22url%22%3A%22http%3A%2F%2Fupos-hz-mirrorakam.akamaized.net%2Fupgcxcode%2F72%2F53%2F1415455372%2F1415455372-1-16.mp4%3Fe%3Dig8euxZM2rNcNbRVhwdVhwdlhWdVhwdVhoNvNC8BqJIzNbfqXBvEuENvNC8aNEVEtEvE9IMvXBvE2ENvNCImNEVEIj0Y2J_aug859r1qXg8xNEVE5XREto8GuFGv2U7SuxI72X6fTr859IB_%5Cu0026uipk%3D5%5Cu0026nbs%3D1%5Cu0026deadline%3D1706428042%5Cu0026gen%3Dplayurlv2%5Cu0026os%3Dakam%5Cu0026oi%3D2076707406%5Cu0026trid%3D4664da9440e44628aa0655d21967e585U%5Cu0026mid%3D0%5Cu0026platform%3Dandroid%5Cu0026upsig%3Da56e92bd8b9b7ad96f0ca351bc8685ac%5Cu0026uparams%3De%2Cuipk%2Cnbs%2Cdeadline%2Cgen%2Cos%2Coi%2Ctrid%2Cmid%2Cplatform%5Cu0026hdnts%3Dexp%3D1706428042~hmac%3D654b9cdf0cea08688f1e950750ce46be8444ca07971cbb79ef8c9a3419823142%5Cu0026bvc%3Dvod%5Cu0026nettype%3D1%5Cu0026orderid%3D0%2C1%5Cu0026buvid%3DXY085C207BFE333828DA1B5803C5364615CE9%5Cu0026build%3D7630200%5Cu0026f%3DU_0_0%5Cu0026bw%3D43626%5Cu0026logo%3D80000000%22%2C%22accept_formats%22%3A%5B%7B%22quality%22%3A64%2C%22format%22%3A%22mp4720%22%2C%22description%22%3A%22%E9%AB%98%E6%B8%85%20720P%22%2C%22new_description%22%3A%22720P%20%E9%AB%98%E6%B8%85%22%2C%22display_desc%22%3A%22720P%22%2C%22need_login%22%3Atrue%7D%2C%7B%22quality%22%3A16%2C%22format%22%3A%22mp4%22%2C%22description%22%3A%22%E6%B5%81%E7%95%85%20360P%22%2C%22new_description%22%3A%22360P%20%E6%B5%81%E7%95%85%22%2C%22display_desc%22%3A%22360P%22%7D%5D%2C%22union_player%22%3A%7B%22biz_type%22%3A1%2C%22dimension%22%3A%7B%22width%22%3A3000%2C%22height%22%3A2200%7D%2C%22aid%22%3A284051701%7D%7D&player_rotate=0&player_width=3000', 'coverLeftText1': '00:06', 'coverLeftText2': '1290观看', 'coverLeftText3': '-弹幕', 'avid': '284051701', 'cid': '1415455372', 'mediaType': 'MediaTypeUGC', 'dimension': {'height': '2200', 'width': '3000'}, 'badge': [{'text': '动态视频', 'textColor': '#FFFFFF', 'textColorNight': '#E5E5E5', 'bgColor': '#FB7299', 'bgColorNight': '#BB5B76', 'borderColor': '#FB7299', 'borderColorNight': '#BB5B76', 'bgStyle': 1}], 'canPlay': True, 'stype': 'video_type_story', 'playIcon': 'https://i0.hdslb.com/bfs/feed-admin/2269afa7897830b397797ebe5f032b899b405c67.png', 'duration': '6', 'bvid': 'BV1dc411s7HP'}}}, {'moduleType': 'module_stat_forward', 'moduleStatForward': {'repost': '1', 'like': '335', 'reply': '34', 'likeInfo': {}, 'noCommentText': '这条动态已被封印，当前不可评论╮(๑•́ ₃•̀๑)╭', 'noForwardText': '这条动态已被封印，当前不可转发╮(๑•́ ₃•̀๑)╭'}}], 'extend': {'dynIdStr': '889384123832991766', 'businessId': '284051701', 'origName': 'DAME_ovo_', 'origImgUrl': 'http://i0.hdslb.com/bfs/archive/6e5bbf864dece212f03d12ef014aac78db8c23ad.jpg', 'origDesc': [{'text': '莉尔老师生日快乐~[Muse Dash_起飞][Muse Dash_欧拉欧拉]（来晚了！）@莉莉莉莉尔', 'type': 'desc_type_text', 'origText': '莉尔老师生日快乐~[Muse Dash_起飞][Muse Dash_欧拉欧拉]（来晚了！）@莉莉莉莉尔'}], 'shareType': '3', 'shareScene': 'dynamic', 'isFastShare': True, 'dynType': '8', 'uid': '33461313', 'cardUrl': 'bilibili://story/284051701?aid=284051701&cid=1415455372&offset=889384123832991766&player_height=2200&player_rotate=0&player_width=3000&scene=dynamic_space&story_item=%7B%22uri%22%3A%22bilibili%3A%2F%2Fstory%2F284051701%3Faid%3D284051701%5Cu0026cid%3D1415455372%5Cu0026offset%3D889384123832991766%5Cu0026player_height%3D2200%5Cu0026player_preload%3D%257B%2522expire_time%2522%253A1706424442%252C%2522cid%2522%253A1415455372%252C%2522quality%2522%253A16%252C%2522file_info%2522%253A%257B%252216%2522%253A%257B%2522infos%2522%253A%255B%257B%2522filesize%2522%253A218132%252C%2522timelength%2522%253A5461%257D%255D%257D%252C%252264%2522%253A%257B%2522infos%2522%253A%255B%257B%2522filesize%2522%253A477800%252C%2522timelength%2522%253A5397%257D%255D%257D%257D%252C%2522video_codecid%2522%253A7%252C%2522video_project%2522%253Atrue%252C%2522url%2522%253A%2522http%253A%252F%252Fupos-hz-mirrorakam.akamaized.net%252Fupgcxcode%252F72%252F53%252F1415455372%252F1415455372-1-16.mp4%253Fe%253Dig8euxZM2rNcNbRVhwdVhwdlhWdVhwdVhoNvNC8BqJIzNbfqXBvEuENvNC8aNEVEtEvE9IMvXBvE2ENvNCImNEVEIj0Y2J_aug859r1qXg8xNEVE5XREto8GuFGv2U7SuxI72X6fTr859IB_%255Cu0026uipk%253D5%255Cu0026nbs%253D1%255Cu0026deadline%253D1706428042%255Cu0026gen%253Dplayurlv2%255Cu0026os%253Dakam%255Cu0026oi%253D2076707406%255Cu0026trid%253D4664da9440e44628aa0655d21967e585U%255Cu0026mid%253D0%255Cu0026platform%253Dandroid%255Cu0026upsig%253Da56e92bd8b9b7ad96f0ca351bc8685ac%255Cu0026uparams%253De%252Cuipk%252Cnbs%252Cdeadline%252Cgen%252Cos%252Coi%252Ctrid%252Cmid%252Cplatform%255Cu0026hdnts%253Dexp%253D1706428042~hmac%253D654b9cdf0cea08688f1e950750ce46be8444ca07971cbb79ef8c9a3419823142%255Cu0026bvc%253Dvod%255Cu0026nettype%253D1%255Cu0026orderid%253D0%252C1%255Cu0026buvid%253DXY085C207BFE333828DA1B5803C5364615CE9%255Cu0026build%253D7630200%255Cu0026f%253DU_0_0%255Cu0026bw%253D43626%255Cu0026logo%253D80000000%2522%252C%2522accept_formats%2522%253A%255B%257B%2522quality%2522%253A64%252C%2522format%2522%253A%2522mp4720%2522%252C%2522description%2522%253A%2522%25E9%25AB%2598%25E6%25B8%2585%2520720P%2522%252C%2522new_description%2522%253A%2522720P%2520%25E9%25AB%2598%25E6%25B8%2585%2522%252C%2522display_desc%2522%253A%2522720P%2522%252C%2522need_login%2522%253Atrue%257D%252C%257B%2522quality%2522%253A16%252C%2522format%2522%253A%2522mp4%2522%252C%2522description%2522%253A%2522%25E6%25B5%2581%25E7%2595%2585%2520360P%2522%252C%2522new_description%2522%253A%2522360P%2520%25E6%25B5%2581%25E7%2595%2585%2522%252C%2522display_desc%2522%253A%2522360P%2522%257D%255D%252C%2522union_player%2522%253A%257B%2522biz_type%2522%253A1%252C%2522dimension%2522%253A%257B%2522width%2522%253A3000%252C%2522height%2522%253A2200%257D%252C%2522aid%2522%253A284051701%257D%257D%5Cu0026player_rotate%3D0%5Cu0026player_width%3D3000%5Cu0026scene%3Ddynamic_space%5Cu0026vmid%3D2473680%22%2C%22ff_cover%22%3A%22http%3A%2F%2Fi0.hdslb.com%2Fbfs%2Fstoryff%2Fn240122sa1cbw1snn2s7js3pfxsdd3q1_firsti.jpg%22%2C%22player_args%22%3A%7B%22duration%22%3A6%2C%22aid%22%3A284051701%2C%22type%22%3A%22av%22%2C%22cid%22%3A1415455372%7D%2C%22dimension%22%3A%7B%22width%22%3A3000%2C%22height%22%3A2200%7D%7D&vmid=2473680', 'origFace': 'https://i0.hdslb.com/bfs/face/560b1516b2bd05910776b889e88cd74362f03875.jpg', 'reply': {'uri': 'bilibili://story/284051701?aid=284051701&cid=1415455372&offset=889384123832991766&player_height=2200&player_rotate=0&player_width=3000&scene=dynamic_space&story_item=%7B%22uri%22%3A%22bilibili%3A%2F%2Fstory%2F284051701%3Faid%3D284051701%5Cu0026cid%3D1415455372%5Cu0026offset%3D889384123832991766%5Cu0026player_height%3D2200%5Cu0026player_rotate%3D0%5Cu0026player_width%3D3000%5Cu0026scene%3Ddynamic_space%5Cu0026vmid%3D2473680%22%2C%22ff_cover%22%3A%22http%3A%2F%2Fi0.hdslb.com%2Fbfs%2Fstoryff%2Fn240122sa1cbw1snn2s7js3pfxsdd3q1_firsti.jpg%22%2C%22player_args%22%3A%7B%22duration%22%3A6%2C%22aid%22%3A284051701%2C%22type%22%3A%22av%22%2C%22cid%22%3A1415455372%7D%2C%22dimension%22%3A%7B%22width%22%3A3000%2C%22height%22%3A2200%7D%7D&vmid=2473680', 'params': [{'key': 'comment_on', 'value': '1'}, {'key': 'comment_state', 'value': '1'}, {'key': 'reply_id', 'value': '-1'}, {'key': 'auto_float_layer', 'value': '99'}]}, 'onlyFansProperty': {'hasPrivilege': True}, 'featureGate': {'enhancedInteraction': True}}}

    b = DynTool.solve_space_dyn({"list": [a]})
    print(b)
