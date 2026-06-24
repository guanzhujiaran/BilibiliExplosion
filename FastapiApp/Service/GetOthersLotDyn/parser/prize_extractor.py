"""基于 ModelScope DeBERTa 模型的第三方抽奖信息提取器

使用 iic/nlp_deberta_rex-uninlu_chinese-base 模型进行信息提取。
提取内容包括：奖品名称、开奖时间、是否抽奖、是否需要转发、是否需要带话题。
模型加载失败时回退到简单匹配。

模型生命周期管理：
- 首次调用时直接加载模型
- 记录最后使用时间
- 超过 _MODEL_IDLE_TIMEOUT 秒未使用时自动卸载模型，节省内存
"""
import asyncio
import re
import time
from typing import Any

import opencc

_QA_MODEL_NAME = "iic/nlp_deberta_rex-uninlu_chinese-base"
# 模型空闲超时时间（秒），超过此时间未使用则卸载模型
_MODEL_IDLE_TIMEOUT = 30 * 60  # 30 分钟

_pipeline: Any = None
_last_use_ts: float = 0.0
_unload_task: asyncio.Task | None = None

# 繁体转简体转换器（线程安全，可全局复用）
_t2s_converter = opencc.OpenCC('t2s.json')


def _preprocess_text(dyn_content: str) -> str:
    """文本预处理：繁体转简体"""
    return  _t2s_converter.convert(dyn_content)


def _load_pipeline() -> Any:
    """直接加载 ModelScope pipeline

    延迟导入 modelscope，避免在模块加载时就触发依赖链。
    """
    from modelscope.pipelines import pipeline
    from modelscope.utils.constant import Tasks
    return pipeline(
        Tasks.information_extraction,
        model=_QA_MODEL_NAME,
    )


def _unload_pipeline() -> None:
    """卸载模型，释放内存"""
    global _pipeline
    _pipeline = None


def _schedule_unload() -> None:
    """调度延迟卸载任务，在 _MODEL_IDLE_TIMEOUT 秒后卸载模型"""
    global _unload_task

    # 取消已有的卸载任务
    if _unload_task is not None and not _unload_task.done():
        _unload_task.cancel()

    async def _delayed_unload():
        try:
            await asyncio.sleep(_MODEL_IDLE_TIMEOUT)
            _unload_pipeline()
        except asyncio.CancelledError:
            pass

    try:
        _unload_task = asyncio.create_task(_delayed_unload())
    except RuntimeError:
        # 没有 event loop 时跳过调度
        pass


async def _get_pipeline() -> Any:
    """获取 ModelScope pipeline，首次调用时直接加载

    每次调用更新最后使用时间，并重新调度卸载任务。
    """
    global _pipeline, _last_use_ts
    if _pipeline is None:
        _pipeline = _load_pipeline()
    _last_use_ts = time.time()
    _schedule_unload()
    return _pipeline


async def extract_prize_names(dyn_content: str) -> list[str]:
    """使用 DeBERTa 模型从动态内容中提取奖品名称

    :param dyn_content: 动态文本内容
    :return: 提取到的奖品名称列表
    """
    if not dyn_content or not dyn_content.strip():
        return []

    text = _preprocess_text(dyn_content)
    if not text:
        return []

    try:
        pipe = await _get_pipeline()
        result = pipe(text)
        prizes = _parse_model_output(result, text)
        if prizes:
            return _deduplicate(prizes)
    except Exception:
        pass

    # 模型不可用，回退到简单匹配
    return _regex_fallback(dyn_content)


async def extract_lottery_time(dyn_content: str) -> str | None:
    """使用 DeBERTa 模型从动态内容中提取开奖时间

    :param dyn_content: 动态文本内容
    :return: 提取到的开奖时间字符串，未提取到返回 None
    """
    if not dyn_content or not dyn_content.strip():
        return None

    text = _preprocess_text(dyn_content)
    if not text:
        return None

    try:
        pipe = await _get_pipeline()
        result = pipe(text)
        # 1. 优先取带时间/日期标签的 span
        labeled_spans = _extract_spans_by_label(
            result, ["时间", "日期", "date", "time", "开奖时间"])
        for span in labeled_spans:
            if _looks_like_datetime(span):
                return span
        # 2. 取包含时间关键词的 span
        time_spans = _extract_spans_by_keywords(
            result, ["开奖", "公布", "结果", "抽取", "时间", "日期", "月", "日", "号"])
        for span in time_spans:
            if _looks_like_datetime(span):
                return span
        # 3. 对所有 span 做兜底检查（如 "6.23" 这类无关键词的日期）
        all_spans = _extract_all_spans(result)
        for span in all_spans:
            if _looks_like_datetime(span):
                return span
    except Exception:
        pass

    # 4. 模型不可用时回退到正则匹配
    return _regex_lottery_time_fallback(dyn_content)


async def extract_is_lot(dyn_content: str) -> bool:
    """使用 DeBERTa 模型判断动态内容是否是抽奖动态

    :param dyn_content: 动态文本内容
    :return: 是否是抽奖动态
    """
    if not dyn_content or not dyn_content.strip():
        return False

    text = _preprocess_text(dyn_content)
    if not text:
        return False

    try:
        pipe = await _get_pipeline()
        result = pipe(text)
        all_spans = _extract_all_spans(result)
        # 检查是否包含抽奖相关的实体
        lottery_keywords = ["抽奖", "抽", "送", "福利", "奖品", "赠送", "包邮"]
        for span in all_spans:
            for kw in lottery_keywords:
                if kw in span:
                    return True
    except Exception:
        pass

    return False


async def extract_need_repost(dyn_content: str) -> bool:
    """使用 DeBERTa 模型判断动态是否需要转发

    :param dyn_content: 动态文本内容
    :return: 是否需要转发
    """
    if not dyn_content or not dyn_content.strip():
        return False

    text = _preprocess_text(dyn_content)
    if not text:
        return False

    try:
        pipe = await _get_pipeline()
        result = pipe(text)
        all_spans = _extract_all_spans(result)
        # 检查是否包含转发相关的实体
        repost_keywords = ["转发", "转", "转评", "转关", "转+关"]
        negative_keywords = ["不用转发", "无需转发", "不准转发", "别转发"]
        for span in all_spans:
            for neg in negative_keywords:
                if neg in span:
                    return False
        for span in all_spans:
            for kw in repost_keywords:
                if kw in span:
                    return True
    except Exception:
        pass

    return False


async def extract_need_topic(dyn_content: str) -> bool:
    """使用 DeBERTa 模型判断动态是否需要带话题

    :param dyn_content: 动态文本内容
    :return: 是否需要带话题
    """
    if not dyn_content or not dyn_content.strip():
        return False

    text = _preprocess_text(dyn_content)
    if not text:
        return False

    try:
        pipe = await _get_pipeline()
        result = pipe(text)
        all_spans = _extract_all_spans(result)
        # 检查是否包含话题相关的实体
        topic_keywords = ["话题", "带话题", "添加话题", "参与话题"]
        for span in all_spans:
            for kw in topic_keywords:
                if kw in span:
                    return True
    except Exception:
        pass

    return False


def _parse_model_output(result: Any, original_text: str) -> list[str]:
    """解析模型输出，提取奖品名称"""
    prizes: list[str] = []

    if isinstance(result, list):
        for item in result:
            if isinstance(item, dict):
                # 提取 span 类型的结果
                span = item.get("span") or item.get("text") or item.get("name")
                label = item.get("type") or item.get("label") or ""
                if span and isinstance(span, str) and len(span) >= 2:
                    prizes.append(span.strip())
            elif isinstance(item, str) and len(item) >= 2:
                prizes.append(item.strip())

    return prizes


def _extract_all_spans(result: Any) -> list[str]:
    """从模型输出中提取所有文本片段"""
    spans: list[str] = []

    if isinstance(result, list):
        for item in result:
            if isinstance(item, dict):
                span = item.get("span") or item.get("text") or item.get("name")
                if span and isinstance(span, str):
                    spans.append(span.strip())
            elif isinstance(item, str):
                spans.append(item.strip())
    elif isinstance(result, dict):
        # 有些模型输出嵌套在 data 字段中
        for value in result.values():
            if isinstance(value, list):
                spans.extend(_extract_all_spans(value))

    return spans


def _extract_spans_by_keywords(result: Any, keywords: list[str]) -> list[str]:
    """从模型输出中提取包含指定关键词的文本片段"""
    all_spans = _extract_all_spans(result)
    matched: list[str] = []
    for span in all_spans:
        for kw in keywords:
            if kw in span:
                matched.append(span)
                break
    return matched


def _looks_like_datetime(text: str) -> bool:
    """判断文本是否看起来像日期时间（非正则，使用简单字符检查）"""
    if not text or len(text) < 3:
        return False
    # 包含数字且包含时间相关字符
    has_digit = any(c.isdigit() for c in text)
    time_chars = ["月", "日", "号", "点", ":", "：", "-", "/", "年", "时", "分", "周"]
    has_time_char = any(tc in text for tc in time_chars)
    if has_digit and has_time_char:
        return True
    # 识别 M.D / M.DD / MM.D / MM.DD 这类点分日期（如 6.23、06.23）
    if has_digit and re.match(r"^\d{1,2}\.\d{1,2}$", text.strip()):
        return True
    return False


def _extract_spans_by_label(result: Any, labels: list[str]) -> list[str]:
    """从模型输出中提取指定 label/type 的文本片段"""
    matched: list[str] = []
    labels_lower = {l.lower() for l in labels}

    def _collect(item: Any) -> None:
        if isinstance(item, dict):
            span = item.get("span") or item.get("text") or item.get("name")
            label = item.get("type") or item.get("label") or ""
            if span and isinstance(span, str) and isinstance(label, str):
                if label.lower() in labels_lower:
                    matched.append(span.strip())
        elif isinstance(item, list):
            for sub in item:
                _collect(sub)

    _collect(result)
    return matched


def _regex_lottery_time_fallback(dyn_content: str) -> str | None:
    """正则回退：当模型不可用或未提取到时，使用正则匹配开奖时间"""
    if not dyn_content:
        return None
    text = _t2s_converter.convert(dyn_content)
    # 匹配 "X月X日/号"、"X.X"、"X/X"、"X年X月X日" 等常见日期写法
    patterns = [
        r"\d{4}年\d{1,2}月\d{1,2}[日号]",
        r"\d{1,2}月\d{1,2}[日号]",
        r"\d{1,2}[./]\d{1,2}(?:\s*(?:开奖|抽|公布))?",
        r"\d{1,2}[:：]\d{2}",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(0).strip()
            # 去掉可能附带的"开奖"等后缀，只保留日期部分
            candidate = re.sub(r"(开奖|抽|公布)$", "", candidate).strip()
            if candidate and _looks_like_datetime(candidate):
                return candidate
    return None


def _regex_fallback(dyn_content: str) -> list[str]:
    """正则回退：当模型不可用时使用简单的模式匹配提取奖品"""
    prizes: list[str] = []
    text = _t2s_converter.convert(dyn_content) if dyn_content else ""

    patterns = [
        # 送 + 量词 + 单位 + 奖品名
        r"送\s*(?:一|两|三|四|五|六|七|八|九|十|几|数|多|[0-9]+)?\s*(?:个|份|盒|台|套|件|本|张|把|只|支|条|瓶|包|袋|箱|桶|罐|杯|碗|盘|双|对|组|副|打|箱)?\s*(.+?)(?:[，。,.\#]|祝|给|送|$|(?:\s*[，。,.\#]))",
        # 抽/奖品 + 冒号 + 内容
        r"(?:抽|奖品)\s*[：:]\s*([^\s#]{2,40})",
        # 关键词收尾模式（手办、模型等），限制前缀不超过10字
        r"([^\s，。,.]{2,10}(?:手办|模型|周边|卡片|立牌|徽章|挂件|抱枕|鼠标垫|T恤|卫衣|背包|键盘|耳机|音箱|游戏|激活码|兑换码|红包|现金|优惠券|会员|皮肤|道具|装备|礼包|福袋|盲盒))",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            m = m.strip()
            if m and len(m) >= 2 and m not in ("抽奖", "奖品", "什么", "送", "抽"):
                prizes.append(m)

    return _deduplicate(prizes)


def _deduplicate(items: list[str]) -> list[str]:
    """去重并保持顺序"""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


if __name__ == "__main__":
    async def _test():
        text = "点赞 评论 转发本期视频，送一盒同款传奇版TV零号机改，6月24日开奖，祝小伙伴们都有好运"
        result = await extract_prize_names(text)
        print(f"奖品提取结果: {result}")

        time_result = await extract_lottery_time(text)
        print(f"开奖时间提取结果: {time_result}")

        is_lot = await extract_is_lot(text)
        print(f"是否抽奖: {is_lot}")

        need_repost = await extract_need_repost(text)
        print(f"是否需要转发: {need_repost}")

        need_topic = await extract_need_topic(text)
        print(f"是否需要带话题: {need_topic}")

    asyncio.run(_test())
