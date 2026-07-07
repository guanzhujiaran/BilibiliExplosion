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
            timeout=30.0,
        )
        logger.debug(f"LLM 提取抽奖信息结果: {result}")
        return PrizeExtractResp(
            dyn_content=text,
            consume_time=time.time() - start_ts,
            result=result)
    except asyncio.TimeoutError:
        logger.error("LLM extract_prize_info 超时（30s），回退到正则判断")
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
        text = "点赞 评论 转发本期视频，送一盒同款传奇版TV零号机改，6月24日开奖，祝小伙伴们都有好运"
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
