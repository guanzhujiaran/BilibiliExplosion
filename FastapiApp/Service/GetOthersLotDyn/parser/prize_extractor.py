"""基于 Qwen3.5-0.8B + vLLM 的抽奖信息提取器

使用 vLLM 加载 Qwen3.5-0.8B 模型进行信息提取，int4 量化极致节省资源。
提取内容包括：奖品名称、开奖时间、是否抽奖、是否需要转发、是否需要带话题、是否大奖。

模型生命周期由 LLMService 单例管理：
- 首次调用时懒加载模型
- 空闲超时自动卸载，释放显存
"""
import json
import re

import opencc
from pydantic import BaseModel, Field

from Service.GetOthersLotDyn.parser.llm_service import LLMService, SamplingPreset
# 繁体转简体转换器（线程安全，可全局复用）
_t2s_converter = opencc.OpenCC('t2s.json')

# 采样参数（文本非思考模式，max_tokens=256 保证 JSON 输出完整）
_SAMPLING_PARAMS = SamplingPreset.TEXT_NON_THINKING.to_params(
    max_tokens=256,
    stop=["<|im_end|>", "<|endoftext|>"],
)

# 提示词模板
_PROMPT_TEMPLATE = """从文本中提取抽奖信息，以JSON格式返回。

规则：
1. prize_names: 奖品名称列表，没有则为空列表
2. lottery_time: 开奖时间，没有则为null
3. is_lot: 是否抽奖，true/false
4. need_repost: 是否需要转发，true/false
5. need_topic: 是否需要带话题，true/false
6. is_grand_prize: 是否大奖，奖品价值高/数量多/知名品牌即为大奖，true/false

示例：
文本：点赞评论转发，送手机壳，6月24日开奖
输出：{{"prize_names": ["手机壳"], "lottery_time": "6月24日", "is_lot": true, "need_repost": true, "need_topic": false, "is_grand_prize": false}}

文本：转发抽送iPhone 15 Pro Max一台，5月1日开奖
输出：{{"prize_names": ["iPhone 15 Pro Max"], "lottery_time": "5月1日", "is_lot": true, "need_repost": true, "need_topic": false, "is_grand_prize": true}}

文本：今天天气真好
输出：{{"prize_names": [], "lottery_time": null, "is_lot": false, "need_repost": false, "need_topic": false, "is_grand_prize": false}}

文本：{text}
输出："""

# 模型服务单例
_llm_service = LLMService()


class PrizeExtractResult(BaseModel):
    """抽奖信息提取结果，一次模型调用提取所有字段"""
    prize_names: list[str] = Field(default_factory=list, description="奖品名称列表")
    lottery_time: str | None = Field(default=None, description="开奖时间")
    is_lot: bool = Field(default=False, description="是否是抽奖动态")
    need_repost: bool = Field(default=False, description="是否需要转发")
    need_topic: bool = Field(default=False, description="是否需要带话题")
    is_grand_prize: bool = Field(default=False, description="是否大奖")


def _preprocess_text(dyn_content: str) -> str:
    """文本预处理：繁体转简体"""
    return _t2s_converter.convert(dyn_content)


def _parse_model_output(output: str) -> PrizeExtractResult:
    """解析模型输出，提取 JSON 结果"""
    json_match = re.search(r'\{[^{}]*\}', output)
    if not json_match:
        return PrizeExtractResult()

    try:
        data = json.loads(json_match.group())
        prize_names = data.get("prize_names", [])
        if isinstance(prize_names, list):
            prize_names = [p for p in prize_names if isinstance(p, str) and len(p) >= 2]
        else:
            prize_names = []
        return PrizeExtractResult(
            prize_names=prize_names,
            lottery_time=data.get("lottery_time"),
            is_lot=bool(data.get("is_lot", False)),
            need_repost=bool(data.get("need_repost", False)),
            need_topic=bool(data.get("need_topic", False)),
            is_grand_prize=bool(data.get("is_grand_prize", False)),
        )
    except (json.JSONDecodeError, TypeError):
        return PrizeExtractResult()


async def extract_prize_info(dyn_content: str) -> PrizeExtractResult:
    """一次性提取所有抽奖相关信息

    只调用一次模型，同时提取奖品名称、开奖时间、是否抽奖、是否需要转发、是否需要带话题。

    :param dyn_content: 动态文本内容
    :return: PrizeExtractResult 包含所有提取结果
    """
    if not dyn_content or not dyn_content.strip():
        return PrizeExtractResult()

    text = _preprocess_text(dyn_content)
    if not text:
        return PrizeExtractResult()

    prompt = _PROMPT_TEMPLATE.format(text=text)
    generated_text = await _llm_service.generate(prompt, _SAMPLING_PARAMS)

    return _parse_model_output(generated_text)


if __name__ == "__main__":
    class TestItem(BaseModel):
        text: str
        expected: PrizeExtractResult
    test_arr :list[TestItem] = [

    ]
    async def _test():
        text = "点赞 评论 转发本期视频，送一盒同款传奇版TV零号机改，6月24日开奖，祝小伙伴们都有好运"
        result: PrizeExtractResult = await extract_prize_info(text)
        print(f"完整提取结果: {result}")
    
    async def _to_csv():
        from Service.GetOthersLotDyn.Sql.sql_helper import SqlHelper
        from Service.GetOthersLotDyn.Sql.models import TLotdyninfo
        from pandas import DataFrame
        from sqlalchemy import select,func
        async with SqlHelper.async_session() as session:
            sql = (
                select(TLotdyninfo.dynContent)
                .order_by(func.char_length(TLotdyninfo.dynContent).desc())
                .limit(100)
            )
            res = await session.execute(sql)
            da = res.scalars().all()
        prize_extract_results:list[PrizeExtractResult] = []
        for d in da:
            result: PrizeExtractResult = await extract_prize_info(d)
            prize_extract_results.append(result)
        df = DataFrame(prize_extract_results, columns=["result"])
        df.to_csv("dyn_content_result.csv", index=False, encoding="utf-8-sig")

    import asyncio
    asyncio.run(_to_csv())