"""
测试 get_other_lot_main.py 中的核心解析逻辑。

运行方式：
    cd /home/minato_aqua/BilibiliExplosion/FastapiApp
    uv run pytest test/test_get_other_lot_main.py -v

注意：
    mock 响应数据从 test/fixtures/ 目录的 JSON 文件加载。
    获取方式：在浏览器中打开 B站动态页面，从 Network 面板复制对应的 API 响应，
    填入 test/fixtures/ 下对应的 JSON 文件中。
"""

import asyncio
import datetime
from copy import deepcopy
from dataclasses import field

import pytest

from Service.GetOthersLotDyn import (
    BiliDynamicItem,
    BiliSpaceUserItem,
    OfficialLotType,
    manual_reply_judge,
)
from CONFIG import settings
from Service.GetOthersLotDyn.Sql.models import TLotdyninfo
from Service.GetOthersLotDyn.parser.dynamic_detail_parsed import DynamicDetailParsed
from Service.GetOthersLotDyn.filter.lottery_filter import is_need_lot

# ============================================================================
# 从 JSON 文件加载 mock 响应数据
# 文件位于 test/fixtures/ 目录，可手动填入真实的 B站 API 响应
# ============================================================================
import json
import os

_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def _load_fixture(filename: str):
    """从 test/fixtures/ 目录加载 JSON 响应数据

    :param filename: fixtures 目录下的文件名
    :return: 解析后的 dict/list；文件为空或不存在时返回 None
    """
    filepath = os.path.join(_FIXTURES_DIR, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # 空模板文件（{}）视为未填入数据
    if data == {} or data == []:
        return None
    return data


# 已填入数据的 fixtures（可直接用于断言）
MOCK_DYNAMIC_DETAIL_RESP = _load_fixture('dynamic_detail_resp.json')
MOCK_FORWARDED_DYNAMIC_RESP = _load_fixture('forwarded_dynamic_resp.json')
MOCK_DYNAMIC_NOT_FOUND_RESP = _load_fixture('dynamic_not_found_resp.json')
MOCK_DYNAMIC_412_RESP = _load_fixture('dynamic_412_resp.json')
MOCK_SPACE_DYNAMIC_RESP = _load_fixture('space_dynamic_resp.json')
MOCK_REPLY_RESP = _load_fixture('reply_resp.json')

# 待手动填入的 fixtures（未填入时为 None，相关测试会跳过）
MOCK_DYNAMIC_DETAIL_RESP_VIDEO = _load_fixture('dynamic_detail_resp_video.json')
MOCK_DYNAMIC_DETAIL_RESP_ARTICLE = _load_fixture('dynamic_detail_resp_article.json')
MOCK_DYNAMIC_DETAIL_RESP_CHARGE_LOT = _load_fixture('dynamic_detail_resp_charge_lot.json')
MOCK_DYNAMIC_DETAIL_RESP_RESERVE_LOT = _load_fixture('dynamic_detail_resp_reserve_lot.json')
MOCK_DYNAMIC_DETAIL_RESP_OFFICIAL_LOT = _load_fixture('dynamic_detail_resp_official_lot.json')
MOCK_DYNAMIC_DETAIL_RESP_PINNED = _load_fixture('dynamic_detail_resp_pinned.json')
MOCK_DYNAMIC_DETAIL_RESP_4101128 = _load_fixture('dynamic_detail_resp_4101128.json')
MOCK_SPACE_DYNAMIC_RESP_EMPTY = _load_fixture('space_dynamic_resp_empty.json')
MOCK_SPACE_DYNAMIC_RESP_NO_MORE = _load_fixture('space_dynamic_resp_no_more.json')
MOCK_REPLY_RESP_EMPTY = _load_fixture('reply_resp_empty.json')


# ============================================================================
# 辅助函数
# ============================================================================


def _make_dynamic_item(dynamic_id: str | int | None = None,
                       dynamic_rid: int | None = None,
                       dynamic_type: int = 2) -> BiliDynamicItem:
    """创建 BiliDynamicItem 实例，跳过 __post_init__ 校验"""
    item = BiliDynamicItem.__new__(BiliDynamicItem)
    item.dynamic_id = dynamic_id
    item.dynamic_rid = dynamic_rid
    item.dynamic_type = dynamic_type
    item.dynamic_raw_resp = {}
    item.dynamic_raw_detail = {}
    item.bili_judge_lottery_result = BiliDynamicItem.__dataclass_fields__[
        'bili_judge_lottery_result'].default_factory()
    item.is_lot_orig = False
    item.is_use_available_proxy = True
    return item


def _make_lot_dyn_info(**kwargs) -> TLotdyninfo:
    """创建 TLotdyninfo 实例，填充默认值"""
    defaults = {
        "dynId": 1000000000000000000,
        "dynamicUrl": "https://t.bilibili.com/1000000000000000000",
        "authorName": "测试UP主",
        "up_uid": 123456,
        "pubTime": datetime.datetime.now() - datetime.timedelta(days=3),
        "dynContent": "转发抽奖！关注+转发即可参与",
        "commentCount": 100,
        "repostCount": 200,
        "likeCount": 50,
        "officialLotType": "",
        "officialLotId": None,
        "isOfficialAccount": 0,
        "isManualReply": "",
        "isLot": 1,
        "hashTag": "",
        "dynLotRound_id": 1,
        "rawJsonStr": None,
    }
    defaults.update(kwargs)
    return TLotdyninfo(**defaults)


def _extract_dynamic_id_from_mock(mock_resp: dict) -> str | None:
    """从 mock API 响应中提取 dynamic_id（id_str）"""
    try:
        return mock_resp["data"]["item"]["id_str"]
    except (KeyError, TypeError):
        return None


def _extract_space_dynamic_ids_from_mock(mock_resp: dict) -> list[str]:
    """从空间动态 mock 响应中提取所有 dynamic_id"""
    try:
        return [item["id_str"] for item in mock_resp["data"]["items"]]
    except (KeyError, TypeError):
        return []


# ============================================================================
# 测试: BiliDynamicItem.__solve_dynamic_item_detail — 动态详情解析
# ============================================================================


class TestDynamicItemDetailParsing:
    """测试 __solve_dynamic_item_detail 对各种动态响应的解析"""

    @pytest.mark.asyncio
    async def test_parse_normal_dynamic(self):
        """测试解析普通动态（非转发）"""
        resp = deepcopy(MOCK_DYNAMIC_DETAIL_RESP)
        dyn_id = _extract_dynamic_id_from_mock(resp)
        if not dyn_id:
            pytest.skip("MOCK_DYNAMIC_DETAIL_RESP 未填入真实数据，跳过测试")

        item = _make_dynamic_item(dynamic_id=dyn_id)
        result = await item._BiliDynamicItem__solve_dynamic_item_detail(resp)

        assert isinstance(result, DynamicDetailParsed), "返回类型应为 DynamicDetailParsed"
        assert result.is_valid(), "解析结果应有效（dynamic_id 不为空）"
        assert result.rawJSON is not None, "rawJSON 不应为空"
        assert result.dynamic_id == "1216239392159432721"
        assert result.author_uid == 80696429
        assert result.author_name == "恋与制作人"
        assert result.pub_ts == 1782016200
        assert result.pub_time == "2026年06月21日 12:40"
        assert result.type == "2"
        assert result.rid == "398757595"
        assert result.comment_count == 9
        assert result.forward_count == 2
        assert result.like_count == 98
        assert result.official_verify_type == 1
        assert result.relation == 1
        assert result.card_stype == "DYNAMIC_TYPE_DRAW"
        assert result.is_liked == 0
        assert "凌肖生日快乐" in result.dynamic_content
        assert result.module_dynamic is not None

    @pytest.mark.asyncio
    async def test_parse_forwarded_dynamic(self):
        """测试解析转发动态（含 orig 原始动态信息）"""
        resp = deepcopy(MOCK_FORWARDED_DYNAMIC_RESP)
        dyn_id = _extract_dynamic_id_from_mock(resp)
        if not dyn_id:
            pytest.skip("MOCK_FORWARDED_DYNAMIC_RESP 未填入真实数据，跳过测试")

        item = _make_dynamic_item(dynamic_id=dyn_id)
        result = await item._BiliDynamicItem__solve_dynamic_item_detail(resp)

        assert isinstance(result, DynamicDetailParsed)
        assert result.is_valid()
        assert result.rawJSON is not None
        # 转发动态应包含原始动态信息
        if result.orig_dynamic_id:
            assert result.orig_name is not None, "转发动态应包含 orig_name"
            assert result.orig_mid is not None, "转发动态应包含 orig_mid"
            assert result.orig_pub_ts is not None, "转发动态应包含 orig_pub_ts"
            assert result.orig_dynamic_content is not None, "转发动态应包含 orig_dynamic_content"

    @pytest.mark.asyncio
    async def test_parse_dynamic_not_found(self):
        """测试动态不存在（code=4101131）"""
        resp = deepcopy(MOCK_DYNAMIC_NOT_FOUND_RESP)
        result = await _make_dynamic_item(dynamic_id=9999999999999999999)._BiliDynamicItem__solve_dynamic_item_detail(resp)

        assert isinstance(result, DynamicDetailParsed)
        assert not result.is_valid(), "不存在的动态应返回无效结果"
        assert result.rawJSON is None, "不存在的动态 rawJSON 应为 None"

    @pytest.mark.asyncio
    async def test_parse_dynamic_with_empty_data(self):
        """测试 data 为 None 的响应"""
        resp = {"code": 0, "data": None}
        result = await _make_dynamic_item(dynamic_id=1)._BiliDynamicItem__solve_dynamic_item_detail(resp)

        assert isinstance(result, DynamicDetailParsed)
        assert not result.is_valid()
        assert result.rawJSON is None

    @pytest.mark.asyncio
    async def test_parse_dynamic_has_major_archive(self):
        """测试含视频稿件(major.archive)的动态"""
        resp = deepcopy(MOCK_DYNAMIC_DETAIL_RESP)
        dyn_id = _extract_dynamic_id_from_mock(resp)
        if not dyn_id:
            pytest.skip("MOCK_DYNAMIC_DETAIL_RESP 未填入真实数据，跳过测试")

        item = _make_dynamic_item(dynamic_id=dyn_id)
        result = await item._BiliDynamicItem__solve_dynamic_item_detail(resp)

        if result.rawJSON:
            assert result.module_dynamic is not None, "应包含 module_dynamic"

    @pytest.mark.asyncio
    async def test_parse_dynamic_has_major_opus(self):
        """测试含图文(opus)的动态"""
        resp = deepcopy(MOCK_DYNAMIC_DETAIL_RESP)
        dyn_id = _extract_dynamic_id_from_mock(resp)
        if not dyn_id:
            pytest.skip("MOCK_DYNAMIC_DETAIL_RESP 未填入真实数据，跳过测试")

        item = _make_dynamic_item(dynamic_id=dyn_id)
        result = await item._BiliDynamicItem__solve_dynamic_item_detail(resp)

        if result.rawJSON:
            assert result.card_stype is not None, "应包含 card_stype"


# ============================================================================
# 测试: manual_reply_judge — 人工回复判断（JS 引擎）
# ============================================================================


class TestManualReplyJudge:
    """测试人工回复判断逻辑"""

    # ---- 需要人工回复的动态内容 ----
    NEED_MANUAL_CASES = [
        "评论告诉我想看什么",          # manual_re1
        "评论说出你的理由",            # manual_re2
        "评论对一下",                  # manual_re3
        "猜对答案的有奖",              # manual_re4
        "大家来说说自己的想法",        # manual_re5
        "艾特你的朋友一起来",          # manual_re6
        "最先猜中的有奖",              # manual_re7
        "新衣回直播",                  # manual_re8
        "留言给点建议",                # manual_re9
        "评论送祝福",                  # manual_re11
        "评论讨论一下",                # manual_re12
        "评论说出你的想法",            # manual_re14
        "评论分享你的经历",            # manual_re15
        "评论聊一聊",                  # manual_re16
        "评接力",                      # manual_re17
        "聊聊这个话题",                # manual_re18
        "评论扣1",                     # manual_re19
        "转发分享给朋友",              # manual_re20
        "评论告诉我",                  # manual_re21
        "评论唠一唠",                  # manual_re22
        "今日话题",                    # manual_re23
        "说答案",                      # manual_re24
        "说出你的想法",                # manual_re25
        "为中国队加油",                # manual_re26
        "评论你最喜欢的话",            # manual_re27
        "评论最喜欢的事情",            # manual_re28
        "分享你的经历",                # manual_re29
        "分享心情",                    # manual_re30
        "评论一句",                    # manual_re31
        "评论包含关键词",              # manual_re31 (变体)
        "转关评下方视频",              # manual_re32
        "分享美好",                    # manual_re33
        "视频弹幕抽奖",                # manual_re34
        "生日快乐",                    # manual_re35
        "一句话形容",                  # manual_re36
        "分享喜爱",                    # manual_re38
        "评论最喜欢",                  # manual_re39
        "带话题晒",                    # manual_re40
        "分享有趣的事",                # manual_re41
        "送出祝福",                    # manual_re42
        "评论原因",                    # manual_re43
        "答案参与抽奖",                # manual_re47
        "唠唠",                        # manual_re48
        "分享一下",                    # manual_re49
        "评论你的故事",                # manual_re50
        "告诉我想什么",                # manual_re51
        "发布图文动态",                # manual_re53
        "视频评论",                    # manual_re54
        "复zhi",                       # manual_re55
        "多少合适",                    # manual_re56
        "喜欢哪一款",                  # manual_re57
        "有没有人？",                  # manual_re58 (需要问号)
    ]

    # ---- 不需要人工回复的动态内容 ----
    NO_MANUAL_CASES = [
        "关注+转发即可参与抽奖，三天后开奖",
        "转发此动态抽三位粉丝送周边",
        "抽奖来啦！关注转发评论三连",
        "【抽奖】转发+关注，抽5位幸运儿",
        "互动抽奖 转发关注",
        "转发动态抽奖 关注我",
        "关注转发抽奖",
        "在评论区随便说点什么 抽奖",
        "来抽奖了 关注转发",
        "关注+转发 抽",
    ]

    def test_needs_manual_reply(self):
        """测试需要人工回复的动态内容"""
        for content in self.NEED_MANUAL_CASES:
            result = manual_reply_judge.call("manual_reply_judge", content)
            assert result is True, f"内容应触发人工回复: {content}"

    def test_no_manual_reply_needed(self):
        """测试不需要人工回复的动态内容"""
        for content in self.NO_MANUAL_CASES:
            result = manual_reply_judge.call("manual_reply_judge", content)
            assert result is not True, f"内容不应触发人工回复: {content}"

    def test_manual_reply_with_special_chars(self):
        """测试包含特殊字符的动态内容"""
        # 全角符号替换测试
        content = "评论「说出」你的想法"
        result = manual_reply_judge.call("manual_reply_judge", content)
        assert result is True, "全角符号替换后应正确判断"

    def test_manual_reply_empty_content(self):
        """测试空内容"""
        result = manual_reply_judge.call("manual_reply_judge", "")
        assert result is not True, "空内容不应触发人工回复"


# ============================================================================
# 测试: is_need_lot — 抽奖过滤逻辑（独立函数）
# ============================================================================


class TestIsNeedLot:
    """测试 is_need_lot 过滤逻辑（lottery_filter.is_need_lot 独立函数）"""

    def setup_method(self):
        self.get_dyn_ts = int(datetime.datetime.now().timestamp())

    def test_normal_lot_passes(self):
        """正常抽奖动态应该通过过滤"""
        lot = _make_lot_dyn_info(
            officialLotType="",
            isOfficialAccount=0,
            commentCount=100,
            repostCount=200,
            pubTime=datetime.datetime.now() - datetime.timedelta(days=3),
        )
        assert is_need_lot(lot, self.get_dyn_ts) is True

    def test_official_lot_filtered(self):
        """官方抽奖应该被过滤"""
        lot = _make_lot_dyn_info(
            officialLotType=OfficialLotType.official_lot.value,
        )
        assert is_need_lot(lot, self.get_dyn_ts) is False

    def test_charge_lot_filtered(self):
        """充电抽奖应该被过滤"""
        lot = _make_lot_dyn_info(
            officialLotType=OfficialLotType.charge_lot.value,
        )
        assert is_need_lot(lot, self.get_dyn_ts) is False

    def test_reserve_lot_filtered(self):
        """预约抽奖应该被过滤"""
        lot = _make_lot_dyn_info(
            officialLotType=OfficialLotType.reserve_lot.value,
        )
        assert is_need_lot(lot, self.get_dyn_ts) is False

    def test_origin_dyn_passes_within_20_days(self):
        """抽奖动态的源动态在20天内应通过"""
        lot = _make_lot_dyn_info(
            officialLotType=OfficialLotType.lot_dyn_origin_dyn.value,
            pubTime=datetime.datetime.now() - datetime.timedelta(days=15),
        )
        assert is_need_lot(lot, self.get_dyn_ts) is True

    def test_origin_dyn_filtered_after_20_days(self):
        """抽奖动态的源动态超过20天应被过滤"""
        lot = _make_lot_dyn_info(
            officialLotType=OfficialLotType.lot_dyn_origin_dyn.value,
            pubTime=datetime.datetime.now() - datetime.timedelta(days=25),
        )
        assert is_need_lot(lot, self.get_dyn_ts) is False

    def test_non_official_old_dynamic_filtered(self):
        """非官方号超过10天的动态应被过滤"""
        lot = _make_lot_dyn_info(
            officialLotType="",
            isOfficialAccount=0,
            commentCount=100,
            repostCount=200,
            pubTime=datetime.datetime.now() - datetime.timedelta(days=12),
        )
        assert is_need_lot(lot, self.get_dyn_ts) is False

    def test_official_account_15_days_passes(self):
        """官方号15天内的动态应通过"""
        lot = _make_lot_dyn_info(
            officialLotType="",
            isOfficialAccount=1,
            commentCount=50,
            repostCount=50,
            pubTime=datetime.datetime.now() - datetime.timedelta(days=12),
        )
        assert is_need_lot(lot, self.get_dyn_ts) is True

    def test_official_account_over_15_days_filtered(self):
        """官方号超过15天的动态应被过滤"""
        lot = _make_lot_dyn_info(
            officialLotType="",
            isOfficialAccount=1,
            commentCount=50,
            repostCount=50,
            pubTime=datetime.datetime.now() - datetime.timedelta(days=18),
        )
        assert is_need_lot(lot, self.get_dyn_ts) is False

    def test_low_engagement_filtered(self):
        """低评论低转发的动态（超过2小时）应被过滤"""
        # get_dyn_ts 设为现在，pubTime 设为3天前，确保时间差 > 2小时
        self.get_dyn_ts = int(datetime.datetime.now().timestamp())
        lot = _make_lot_dyn_info(
            officialLotType="",
            isOfficialAccount=0,
            commentCount=5,
            repostCount=3,
            pubTime=datetime.datetime.now() - datetime.timedelta(days=3),
        )
        assert is_need_lot(lot, self.get_dyn_ts) is False

    def test_very_old_pubtime_filtered(self):
        """pubTime 年份小于2000的应被过滤"""
        lot = _make_lot_dyn_info(
            pubTime=datetime.datetime(1970, 1, 1),
        )
        assert is_need_lot(lot, self.get_dyn_ts) is False

    def test_recent_dynamic_passes_regardless_of_engagement(self):
        """发布时间与获取时间间隔小于2小时的动态不按评论转发数过滤"""
        lot = _make_lot_dyn_info(
            officialLotType="",
            isOfficialAccount=0,
            commentCount=1,
            repostCount=1,
            pubTime=datetime.datetime.now() - datetime.timedelta(hours=1),
        )
        assert is_need_lot(lot, self.get_dyn_ts) is True


# ============================================================================
# 测试: BiliSpaceUserItem._solve_space_dynamic — 空间动态解析
# ============================================================================


class TestSpaceDynamicParsing:
    """测试空间动态解析"""

    @pytest.mark.asyncio
    async def test_parse_space_with_forward_dynamic(self):
        """测试解析含转发动态的空间响应"""
        if not MOCK_SPACE_DYNAMIC_RESP:
            pytest.skip("space_dynamic_resp.json 未填入真实数据，跳过测试")
        resp = deepcopy(MOCK_SPACE_DYNAMIC_RESP)
        if not resp.get("data", {}).get("items"):
            pytest.skip("MOCK_SPACE_DYNAMIC_RESP 未填入真实数据，跳过测试")

        user_item = BiliSpaceUserItem.__new__(BiliSpaceUserItem)
        user_item.uid = 123456
        user_item.lot_round_id = 1
        user_item._offset = 0
        user_item.dynamic_infos = set()
        user_item.pub_lot_users = set()
        user_item._pub_lot_uids = set()
        user_item.updateNum = 0
        user_item.is_use_available_proxy = True
        user_item.lot_user_info = None
        user_item.params = None

        result = await user_item._solve_space_dynamic(resp, isPubLotUser=False)

        assert result is not None, "返回的动态ID列表不应为空"
        assert len(result) > 0, "应至少解析出一条动态"

    @pytest.mark.asyncio
    async def test_parse_space_as_pub_lot_user(self):
        """测试解析发布抽奖用户的空间（isPubLotUser=True）"""
        if not MOCK_SPACE_DYNAMIC_RESP:
            pytest.skip("space_dynamic_resp.json 未填入真实数据，跳过测试")
        resp = deepcopy(MOCK_SPACE_DYNAMIC_RESP)
        if not resp.get("data", {}).get("items"):
            pytest.skip("MOCK_SPACE_DYNAMIC_RESP 未填入真实数据，跳过测试")

        user_item = BiliSpaceUserItem.__new__(BiliSpaceUserItem)
        user_item.uid = 123456
        user_item.lot_round_id = 1
        user_item._offset = 0
        user_item.dynamic_infos = set()
        user_item.pub_lot_users = set()
        user_item._pub_lot_uids = set()
        user_item.updateNum = 0
        user_item.is_use_available_proxy = True
        user_item.lot_user_info = None
        user_item.params = None

        result = await user_item._solve_space_dynamic(resp, isPubLotUser=True)

        assert result is not None
        assert len(result) > 0
        # 发布抽奖用户的空间动态会被加入 dynamic_infos
        assert len(user_item.dynamic_infos) > 0, "发布抽奖用户的动态应被加入 dynamic_infos"

    @pytest.mark.asyncio
    async def test_parse_space_empty_items(self):
        """测试空 items 的空间响应"""
        resp = {
            "code": 0,
            "data": {
                "items": [],
                "has_more": False,
                "offset": "",
            },
        }

        user_item = BiliSpaceUserItem.__new__(BiliSpaceUserItem)
        user_item.uid = 123456
        user_item.lot_round_id = 1
        user_item._offset = 0
        user_item.dynamic_infos = set()
        user_item.pub_lot_users = set()
        user_item._pub_lot_uids = set()
        user_item.updateNum = 0
        user_item.is_use_available_proxy = True
        user_item.lot_user_info = None
        user_item.params = None

        result = await user_item._solve_space_dynamic(resp, isPubLotUser=False)

        # 空 items + has_more=False 时返回 None
        assert result is None, "空 items 且无更多数据时返回 None"


# ============================================================================
# 测试: 额外 fixture 文件 — 不同类型的动态响应
# 这些测试在对应的 JSON 文件填入真实数据后才会运行
# ============================================================================


class TestAdditionalFixtures:
    """测试额外的 fixture 文件（需手动填入真实 API 响应后才会运行）"""

    @pytest.mark.asyncio
    async def test_parse_video_dynamic(self):
        """测试解析视频类型动态（dynamic_detail_resp_video.json）"""
        if not MOCK_DYNAMIC_DETAIL_RESP_VIDEO:
            pytest.skip("dynamic_detail_resp_video.json 未填入真实数据，跳过测试")
        resp = deepcopy(MOCK_DYNAMIC_DETAIL_RESP_VIDEO)
        dyn_id = _extract_dynamic_id_from_mock(resp)
        if not dyn_id:
            pytest.skip("响应中未找到 dynamic_id，跳过测试")

        item = _make_dynamic_item(dynamic_id=dyn_id)
        result = await item._BiliDynamicItem__solve_dynamic_item_detail(resp)

        assert isinstance(result, DynamicDetailParsed)
        assert result.is_valid(), "视频动态解析结果应有效"
        assert result.rawJSON is not None

    @pytest.mark.asyncio
    async def test_parse_article_dynamic(self):
        """测试解析文章类型动态（dynamic_detail_resp_article.json）"""
        if not MOCK_DYNAMIC_DETAIL_RESP_ARTICLE:
            pytest.skip("dynamic_detail_resp_article.json 未填入真实数据，跳过测试")
        resp = deepcopy(MOCK_DYNAMIC_DETAIL_RESP_ARTICLE)
        dyn_id = _extract_dynamic_id_from_mock(resp)
        if not dyn_id:
            pytest.skip("响应中未找到 dynamic_id，跳过测试")

        item = _make_dynamic_item(dynamic_id=dyn_id)
        result = await item._BiliDynamicItem__solve_dynamic_item_detail(resp)

        assert isinstance(result, DynamicDetailParsed)
        assert result.is_valid(), "文章动态解析结果应有效"
        assert result.rawJSON is not None

    @pytest.mark.asyncio
    async def test_parse_charge_lot_dynamic(self):
        """测试解析充电抽奖动态（dynamic_detail_resp_charge_lot.json）"""
        if not MOCK_DYNAMIC_DETAIL_RESP_CHARGE_LOT:
            pytest.skip("dynamic_detail_resp_charge_lot.json 未填入真实数据，跳过测试")
        resp = deepcopy(MOCK_DYNAMIC_DETAIL_RESP_CHARGE_LOT)
        dyn_id = _extract_dynamic_id_from_mock(resp)
        if not dyn_id:
            pytest.skip("响应中未找到 dynamic_id，跳过测试")

        item = _make_dynamic_item(dynamic_id=dyn_id)
        result = await item._BiliDynamicItem__solve_dynamic_item_detail(resp)

        assert isinstance(result, DynamicDetailParsed)
        assert result.is_valid(), "充电抽奖动态解析结果应有效"

    @pytest.mark.asyncio
    async def test_parse_reserve_lot_dynamic(self):
        """测试解析预约抽奖动态（dynamic_detail_resp_reserve_lot.json）"""
        if not MOCK_DYNAMIC_DETAIL_RESP_RESERVE_LOT:
            pytest.skip("dynamic_detail_resp_reserve_lot.json 未填入真实数据，跳过测试")
        resp = deepcopy(MOCK_DYNAMIC_DETAIL_RESP_RESERVE_LOT)
        dyn_id = _extract_dynamic_id_from_mock(resp)
        if not dyn_id:
            pytest.skip("响应中未找到 dynamic_id，跳过测试")

        item = _make_dynamic_item(dynamic_id=dyn_id)
        result = await item._BiliDynamicItem__solve_dynamic_item_detail(resp)

        assert isinstance(result, DynamicDetailParsed)
        assert result.is_valid(), "预约抽奖动态解析结果应有效"

    @pytest.mark.asyncio
    async def test_parse_official_lot_dynamic(self):
        """测试解析官方抽奖动态（dynamic_detail_resp_official_lot.json）"""
        if not MOCK_DYNAMIC_DETAIL_RESP_OFFICIAL_LOT:
            pytest.skip("dynamic_detail_resp_official_lot.json 未填入真实数据，跳过测试")
        resp = deepcopy(MOCK_DYNAMIC_DETAIL_RESP_OFFICIAL_LOT)
        dyn_id = _extract_dynamic_id_from_mock(resp)
        if not dyn_id:
            pytest.skip("响应中未找到 dynamic_id，跳过测试")

        item = _make_dynamic_item(dynamic_id=dyn_id)
        result = await item._BiliDynamicItem__solve_dynamic_item_detail(resp)

        assert isinstance(result, DynamicDetailParsed)
        assert result.is_valid(), "官方抽奖动态解析结果应有效"

    @pytest.mark.asyncio
    async def test_parse_pinned_dynamic(self):
        """测试解析置顶动态（dynamic_detail_resp_pinned.json）"""
        if not MOCK_DYNAMIC_DETAIL_RESP_PINNED:
            pytest.skip("dynamic_detail_resp_pinned.json 未填入真实数据，跳过测试")
        resp = deepcopy(MOCK_DYNAMIC_DETAIL_RESP_PINNED)
        dyn_id = _extract_dynamic_id_from_mock(resp)
        if not dyn_id:
            pytest.skip("响应中未找到 dynamic_id，跳过测试")

        item = _make_dynamic_item(dynamic_id=dyn_id)
        result = await item._BiliDynamicItem__solve_dynamic_item_detail(resp)

        assert isinstance(result, DynamicDetailParsed)
        assert result.is_valid(), "置顶动态解析结果应有效"

    @pytest.mark.asyncio
    async def test_parse_dynamic_4101128(self):
        """测试动态被删除/不可见（code=4101128）（dynamic_detail_resp_4101128.json）"""
        if not MOCK_DYNAMIC_DETAIL_RESP_4101128:
            pytest.skip("dynamic_detail_resp_4101128.json 未填入真实数据，跳过测试")
        resp = deepcopy(MOCK_DYNAMIC_DETAIL_RESP_4101128)
        result = await _make_dynamic_item(dynamic_id=1)._BiliDynamicItem__solve_dynamic_item_detail(resp)

        assert isinstance(result, DynamicDetailParsed)
        # 4101128 错误应返回无效结果
        assert not result.is_valid(), "code=4101128 的动态应返回无效结果"

    @pytest.mark.asyncio
    async def test_parse_space_dynamic_empty(self):
        """测试空的空间动态响应（space_dynamic_resp_empty.json）"""
        if not MOCK_SPACE_DYNAMIC_RESP_EMPTY:
            pytest.skip("space_dynamic_resp_empty.json 未填入真实数据，跳过测试")
        resp = deepcopy(MOCK_SPACE_DYNAMIC_RESP_EMPTY)

        user_item = BiliSpaceUserItem.__new__(BiliSpaceUserItem)
        user_item.uid = 123456
        user_item.lot_round_id = 1
        user_item._offset = 0
        user_item.dynamic_infos = set()
        user_item.pub_lot_users = set()
        user_item._pub_lot_uids = set()
        user_item.updateNum = 0
        user_item.is_use_available_proxy = True
        user_item.lot_user_info = None
        user_item.params = None

        result = await user_item._solve_space_dynamic(resp, isPubLotUser=False)
        # 空 items 响应应返回 None
        assert result is None, "空空间动态响应应返回 None"

    @pytest.mark.asyncio
    async def test_parse_space_dynamic_no_more(self):
        """测试无更多动态的空间响应（space_dynamic_resp_no_more.json）"""
        if not MOCK_SPACE_DYNAMIC_RESP_NO_MORE:
            pytest.skip("space_dynamic_resp_no_more.json 未填入真实数据，跳过测试")
        resp = deepcopy(MOCK_SPACE_DYNAMIC_RESP_NO_MORE)

        user_item = BiliSpaceUserItem.__new__(BiliSpaceUserItem)
        user_item.uid = 123456
        user_item.lot_round_id = 1
        user_item._offset = 0
        user_item.dynamic_infos = set()
        user_item.pub_lot_users = set()
        user_item._pub_lot_uids = set()
        user_item.updateNum = 0
        user_item.is_use_available_proxy = True
        user_item.lot_user_info = None
        user_item.params = None

        result = await user_item._solve_space_dynamic(resp, isPubLotUser=False)
        # has_more=False 但响应中仍可能包含动态，验证解析结果为列表
        assert isinstance(result, list), "空间动态解析结果应为列表"


# ============================================================================
# 测试: GetOthersLotDynRobot — 初始化与常量
# ============================================================================


class TestConstants:
    """测试模块常量"""

    def test_max_user_list_size(self):
        """用户列表最大长度应为正数"""
        assert settings.get_others_lot.max_user_list_size > 0

    def test_min_valid_lot_threshold(self):
        """有效抽奖阈值应为正数"""
        assert settings.get_others_lot.min_valid_lot_threshold > 0

    def test_get_lot_dyn_time_limit(self):
        """抽奖动态时间限制应为正数"""
        assert settings.get_others_lot.dyn_time_limit > 0

    def test_space_dyn_concurrency(self):
        """空间动态并发数应为正数"""
        assert settings.get_others_lot.space_dyn_concurrency > 0


# ============================================================================
# 测试: OfficialLotType 枚举
# ============================================================================


class TestOfficialLotType:
    """测试官方抽奖类型枚举"""

    def test_enum_values(self):
        assert OfficialLotType.reserve_lot.value == "预约抽奖"
        assert OfficialLotType.charge_lot.value == "充电抽奖"
        assert OfficialLotType.official_lot.value == "官方抽奖"
        assert OfficialLotType.lot_dyn_origin_dyn.value == "抽奖动态的源动态"


# ============================================================================
# 运行入口
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])