"""基于 Qwen + LangChain Ollama 的抽奖信息提取器

使用 ChatOllama.with_structured_output() 进行结构化信息提取，LLM 直接返回 Pydantic 模型。

提供两个入口函数，分别对应 biliopusdb 和 dyndetail 两个数据库的 t_lot_extra_info 需求:
- extract_prize_info_for_biliopusdb() → 适用于普通抽奖动态 (ref_id + lot_type)
- extract_prize_info_for_dyndetail()  → 适用于官方/充电抽奖 (lottery_id)

核心特性：
- with_structured_output 驱动 LLM 调用，无需 agent 层
- LLM 调用有 30s 超时保护，超时/失败自动回退到 CommMethods 正则判断
- 采样参数通过 get_llm() 关键字参数传入
"""
import asyncio
import json
import time
import re
from datetime import datetime
import opencc
from loguru import logger
from pydantic import BaseModel, Field
from Service.llm_service import get_llm, SamplingPreset
from Utils.通用.CommMethods import methods

# 繁体转简体转换器（线程安全，可全局复用）
_t2s_converter = opencc.OpenCC('t2s.json')

# 正则回退方法实例
_fallback = methods()


class PrizeExtractResult(BaseModel):
    """抽奖信息提取结果"""
    prize_names: list[str] = Field(default_factory=list, description="奖品名称列表")
    lottery_time: str | None = Field(
        default=None, description="开奖时间，格式YYYY-MM-DD，没有则为None")
    is_lot: bool = Field(default=False, description="是否是抽奖动态")
    need_repost: bool = Field(default=False, description="是否需要转发")
    required_topic_text: str = Field(
        default="", description="需要携带的话题文本，如 #抽奖#，无则为空字符串")
    is_grand_prize: bool = Field(
        default=False, description="是否大奖，奖品价值高/知名品牌/电子产品")


class PrizeExtractResp(BaseModel):
    """抽奖信息提取返回内容"""
    dyn_content: str = Field(description="原始文本内容")
    consume_time: float = Field(description="处理耗时，单位秒")
    result: PrizeExtractResult = Field(description="抽奖信息提取结果")

    def __post_init__(self):
        self.dyn_content = json.dumps(self.dyn_content)


# ============ System Prompt ============

_AGENT_SYSTEM_PROMPT = """从文本中提取抽奖信息。
规则：
1. prize_names: 奖品名称列表，没有则为空列表
2. lottery_time: 开奖时间，格式YYYY-MM-DD，没有则为null
3. is_lot: 是否抽奖，true/false
4. need_repost: 是否需要转发，true/false
5. required_topic_text: 需要携带的话题文本，如 #抽奖#，无则为空字符串
6. is_grand_prize: 是否大奖，奖品价值高/数量多/知名品牌即为大奖，true/false"""


def _build_system_prompt(pub_time: datetime | None) -> str:
    """构建系统提示词，可选附加动态发布时间作为时间参考"""
    if pub_time:
        return _AGENT_SYSTEM_PROMPT + f"\n\n动态发布时间：{pub_time.strftime('%Y-%m-%d')}，开奖时间应不早于此时间。"
    return _AGENT_SYSTEM_PROMPT


def _preprocess_text(dyn_content: str) -> str:
    """文本预处理：去除链接、繁体转简体"""
    removed_links = re.findall(r'https?://[^\s\u4e00-\u9fff]*', dyn_content)
    if removed_links:
        logger.debug(f"去除链接: {removed_links}")
    text = re.sub(r'https?://[^\s\u4e00-\u9fff]*', '', dyn_content)
    return _t2s_converter.convert(text)


def _fallback_extract(text: str) -> PrizeExtractResult:
    """LLM 失败时的正则回退判断，基于 CommMethods 的方法"""
    is_lot = _fallback.choujiangxinxipanduan(text) is None
    need_repost = _fallback.zhuanfapanduan(text) == 1
    pre_msg = _fallback.pre_msg_processing(text)
    required_topic_text = pre_msg if "#" in pre_msg else ""
    return PrizeExtractResult(
        is_lot=is_lot,
        need_repost=need_repost,
        required_topic_text=required_topic_text,
    )


# ================================================================
# 核心提取逻辑（共享）
# ================================================================

async def _do_extract(*, dyn_content: str, dyn_publish_time: datetime | None = None, force_local: bool = False) -> PrizeExtractResp:
    """一次性提取所有抽奖相关信息（内部共享实现）"""
    start_ts = time.time()
    if not dyn_content or not dyn_content.strip():
        return PrizeExtractResp(
            dyn_content=dyn_content,
            consume_time=time.time() - start_ts,
            result=PrizeExtractResult(),
        )

    text = _preprocess_text(dyn_content)
    if not text:
        return PrizeExtractResp(
            dyn_content=text,
            consume_time=time.time() - start_ts,
            result=PrizeExtractResult(),
        )

    try:
        logger.debug(f"开始调用 LLM 提取抽奖信息，文本: {text}")
        llm = get_llm(
            force_local=force_local,
            **SamplingPreset.TEXT_NON_THINKING.to_kwargs(num_predict=256),
        )
        structured_llm = llm.with_structured_output(PrizeExtractResult)
        messages = [
            {"role": "system", "content": _build_system_prompt(dyn_publish_time)},
            {"role": "user", "content": text},
        ]
        result: PrizeExtractResult = await asyncio.wait_for(
            structured_llm.ainvoke(messages),
            timeout=600.0,
        )
        logger.debug(f"LLM 提取抽奖信息结果: {result}")
        return PrizeExtractResp(
            dyn_content=text,
            consume_time=time.time() - start_ts,
            result=result)
    except asyncio.TimeoutError:
        logger.error("LLM extract_prize_info 超时（600s），回退到正则判断")
        return PrizeExtractResp(
            dyn_content=dyn_content,
            consume_time=time.time() - start_ts,
            result=_fallback_extract(text),
        )
    except Exception as e:
        logger.error(f"LLM extract_prize_info failed: {e}, falling back to regex")
        return PrizeExtractResp(
            dyn_content=dyn_content,
            consume_time=time.time() - start_ts,
            result=_fallback_extract(text),
        )


# ================================================================
# 公开入口 — 分别对应 biliopusdb / dyndetail 的 t_lot_extra_info 需求
# ================================================================

async def extract_prize_info_for_biliopusdb(
    *,
    dyn_content: str,
    dyn_publish_time: datetime | None = None,
    force_local: bool = False,
) -> PrizeExtractResp:
    """
    面向 biliopusdb (普通抽奖动态) 的抽奖信息提取。

    返回的 PrizeExtractResult 包含完整字段:
      - prize_names, lottery_time → 用于 t_others_lot_info 表缓存
      - is_lot, need_repost, required_topic_text → 用于抽奖判断
      - is_grand_prize → 用于 t_lot_extra_info (ref_id + lot_type='common')

    调用方通常进一步通过 SqlHelper.save_prize() / save_extra_info() 入库。
    """
    return await _do_extract(
        dyn_content=dyn_content,
        dyn_publish_time=dyn_publish_time,
        force_local=force_local,
    )


async def extract_prize_info_for_dyndetail(
    *,
    dyn_content: str,
    force_local: bool = False,
) -> PrizeExtractResp:
    """
    面向 dyndetail (官方/充电抽奖) 的抽奖信息提取。

    侧重于 is_grand_prize 判断，用于 t_lot_extra_info (lottery_id 关联 lotdata)。
    不关注 prize_names / lottery_time（官方抽奖已有固定字段）。

    调用方通常通过 grpc_sql_helper._upsert_extra_info() / batch_save_extra_info() 入库。
    """
    return await _do_extract(
        dyn_content=dyn_content,
        dyn_publish_time=None,  # 官方抽奖不传发布时间
        force_local=force_local,
    )


# ================================================================
# 向后兼容别名
# ================================================================

# extract_prize_info 保持向后兼容，指向 biliopusdb 版本
extract_prize_info = extract_prize_info_for_biliopusdb


if __name__ == "__main__":

    async def _test():
        text = """准备开韩国文学的坑了！大家有没有好看的韩国小说推荐？视频来源：
书：《明亮的夜晚》（译者：叶蕾；出版社：台海出版社；出品方: 磨铁·大鱼读品）；《对我无害之人》（译者：徐丽红；出版社：中国友谊出版公司；出品方: 磨铁·大鱼读品）；《福柯读本》（作者/译者：米歇尔·福柯 / 汪民安；出版社：北京大学出版社；丛书: 培文读本丛书）；《第二性》（译者：郑克鲁；出版社：上海译文出版社；丛书: 西蒙娜·德·波伏瓦系列）。部分文案由译林出版社编辑老师提供；图片来自于网络，部分图片来自于上述参考书目。

电影：《82年生的金智英 82년생 김지영 (2019)》、《悲伤崔恩荣：消解父权，如何祛魅、僭越、割裂观念歧视？自我存在感与可能性，痛苦与新生…《明亮的夜晚》（首先我没看过这边书）观看时脑子里一直是歌德曾经说过的那句“我可以确保正直，但不能保证没有偏见。”文中主人公的遭遇是否就是正直的离席导致偏见的过度纵横。从三代人的视角来看，作为受害者的女性始终受到社会偏见的影响，都处在一种不正直的权力约束下，也即因社会关系网中每一个人的“失智”导致了受害者的人生悲剧。up于视频3min左右处抛出的一系列性别疑惑，主观上我认为是对“正直”问题的思索以及随后对自我存在意义和自性的探寻。4min处则是up认为的本文对“正直”作出的两大呼唤（另一个在下面）：对男性祛魅，对人际关系祛魅。只有祛魅之后才有正直可言，而正直的指引能将所谓偏见归束在一个不那么僭越乃至伤害他人的位置。
    让我意想不到的是，在最后还有一组更深的向内探寻自性的过程，更多地从羞耻感着笔，从对自己的欺瞒着笔，把自己的天真和幻象剖开，认真地和自己的困厄相联系。这一点和《没有人给他写信的上校》中那个上校完全不同，然而最开始的欺骗是相通的：一个选择抓住缥缈的斗鸡大赛作为活下去的新希望，一个选择投奔本就不是真实的爱着的新家庭。欺骗引发的必然结果是二者同样惨淡的终局：“那我们这些天吃什么呢？”“吃屎！”；“他对我来说真的是有意义又有分量的人吗？”“在知道他有外遇之前，我眞的像一直以来坚信的那样没有那么痛苦，也没有那么病态吗? 我想通过和他结婚逃避自己存在的问题和具有的可能性。”
    “不能保证没有偏见”，就是个人对自己的部分行为没有正确认知，或者已经意识到问题所在却有意逃避，都将在随后引发“欺瞒”，因此不能保证个人无偏见。无论是意识到还是没意识到，无意义的希望本身就是一种欺瞒，两个人都因为羞耻感，因为面子，失去了方方面面而言都更加重要的东西。这一点上，“正直”不能解决羞耻感的问题，因为正直能解决是更加广泛的社会性问题，而不能处理好自性这一更加内化的问题。而作者给出了自己的答复：对羞耻感除魅。在最后以一种托马斯泰式的自我心理剖析，直接点出韩国人在自性方面，尤其是羞耻感方面的问题，解决正直无法解决的问题。
    而根据韩国情况，“正直”能做到的东西需要更大的力量，需要政府能力的全方位进步，这除了（）基本难以实现。然而本文重在提供了一种新出路，完善自性，自我接纳，独立成长，在更加小处，抚青萍而后起微澜，我认为这才是这本书好的地方（第一部分）

非常感谢小伙伴的长评，很棒很棒！！！这期视频会因为你的长评而更有意义（更重要的是你看到了视频最后，发现了我提出羞耻感祛魅这个观点，而不是只看到了视频里性别处境、男女地位等浮于表面的话题）。对了，先说一下《明亮的夜晚》这本书在豆瓣上的评分：9.0，超过2万5千人的给出了评价，还能有9分这样的高分，相当了不起，所以你说你还没看这本书——可以看一下，很值得！

不得不说，你看完你的评论我就知道你基本理解了本期视频及文案想要表达的内容，那么就就着视频尾部的“羞耻感祛魅”这个话题延伸再分享一下看完《明亮的夜晚》时，为什么突然有了这个理解，崔恩荣在小说里几乎没有提到“羞耻感”，但那一段——“我不想经历真心实意地深爱一个人的那种撕心裂肺的痛苦。我想远离这种感情上的可能性，在不冷不热的关系中安全地生活。还有比欺骗自己更容易的事吗？离婚后我经历的痛苦时光不只是因为丈夫的欺骗，也是我欺骗自己的结果。扪心自问，其中更让我痛苦的正是我对自己的欺骗。”要留意这一段，明明女主经历了那么多不公平的事情，读者的情绪和同理心也都站到了女主那边去，这一段的出现却着实在引导读者思考女主的问题，跟着她的内心一同回顾结婚动机，也就是造成离婚局面的最初决定，然后得出“不只是丈夫的欺骗，也是我欺骗自己的结果”，这个“自省”的逻辑是很有深意的，崔恩荣为什么要这么做？为什么女主会有一个这样的表态？"""
        result = await extract_prize_info_for_biliopusdb(dyn_content=text, force_local=True)
        print(f"biliopusdb 提取结果: {result}")

        result2 = await extract_prize_info_for_dyndetail(dyn_content=text, force_local=True)
        print(f"dyndetail 提取结果: {result2}")

    async def _to_csv():
        import csv
        from Service.GetOthersLotDyn.Sql.sql_helper import SqlHelper
        from Service.GetOthersLotDyn.Sql.models import TLotdyninfo
        from pandas import DataFrame
        from sqlalchemy import select, func
        async with SqlHelper.async_session() as session:
            sql = (
                select(TLotdyninfo)
                .where(TLotdyninfo.isLot == 1)
                .order_by(func.char_length(TLotdyninfo.dynContent).desc())
                .limit(10)
            )
            res = await session.execute(sql)
            da: list[TLotdyninfo] = res.scalars().all()
        prize_extract_results = []
        for d in da:
            result = await extract_prize_info_for_biliopusdb(
                dyn_content=d.dynContent,
                dyn_publish_time=d.pubTime,
                force_local=True,
            )
            prize_extract_results.append(result)
        pd = DataFrame([r.model_dump() for r in prize_extract_results])
        pd.to_csv("dyn_content_result.csv", index=False, encoding="utf-8",
                   quoting=csv.QUOTE_NONNUMERIC)

    asyncio.run(_test())
