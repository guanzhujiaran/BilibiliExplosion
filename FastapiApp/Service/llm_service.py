"""LangChain 模型服务，支持「外部 LLM API 列表 → 本地 LM Studio」回退策略

通过环境变量 llm_apis 配置 OpenAI 兼容 API 列表（Pydantic list[LLMApiConfig]）：
    llm_apis='[{"base_url":"https://...","model_name":"gpt-3.5","token":"sk-xxx"}]'
    或：llm_apis__0__base_url=...  llm_apis__0__model_name=...  llm_apis__0__token=...

按列表顺序依次尝试，全部失败后回退到本地 LM Studio（OpenAI 兼容）。未配置时直接使用本地 LM Studio。

采样参数通过 get_llm() 的关键字参数传入：
    llm = get_llm(temperature=0.7, num_predict=256)
"""
from CONFIG import CONFIG, ModelName
from enum import StrEnum
from typing import Any

from pydantic import SecretStr

from langchain_openai import ChatOpenAI

from CONFIG import settings
from loguru import logger
# ============ 采样参数预设 ============

_PRESET_KWARGS: dict["SamplingPreset", dict[str, Any]] = {}


class SamplingPreset(StrEnum):
    """采样参数预设，按任务类型分为 4 组"""
    TEXT_NON_THINKING = "text_non_thinking"   # 文本任务，非思考模式
    VL_NON_THINKING = "vl_non_thinking"       # 视觉-语言任务，非思考模式
    TEXT_THINKING = "text_thinking"           # 文本任务，思考模式
    VL_THINKING = "vl_thinking"               # 视觉-语言 / 精确编码任务，思考模式

    def to_kwargs(self, **overrides: Any) -> dict[str, Any]:
        """根据预设生成 bind 参数，支持 overrides 覆盖"""
        kwargs = dict(_PRESET_KWARGS[self])
        kwargs.update(overrides)
        return kwargs


_PRESET_KWARGS.update({
    SamplingPreset.TEXT_NON_THINKING: dict(
        temperature=1.0, top_p=1.0, top_k=20, num_predict=512,
    ),
    SamplingPreset.VL_NON_THINKING: dict(
        temperature=0.7, top_p=0.80, top_k=20, num_predict=512,
    ),
    SamplingPreset.TEXT_THINKING: dict(
        temperature=1.0, top_p=0.95, top_k=20, num_predict=512,
    ),
    SamplingPreset.VL_THINKING: dict(
        temperature=0.6, top_p=0.95, top_k=20, num_predict=512,
    ),
})


# ============ 全局 LLM 实例 ============
# 本地 LM Studio（兜底，OpenAI 兼容）
_local_llm = ChatOpenAI(
    model=ModelName.QWEN3_5_0_8_Q4_K_M_GGUF,
    base_url=CONFIG.llama_url,
    api_key="not-needed",
)

# 免费 API 列表（按顺序优先使用）
_free_api_llms: list[ChatOpenAI] = []
for cfg in settings.llm_apis:
    if cfg.base_url and cfg.model_name:
        _free_api_llms.append(ChatOpenAI(
            model=cfg.model_name,
            base_url=cfg.base_url,
            api_key=SecretStr(
                cfg.token) if cfg.token else SecretStr("not-needed"),
        ))

# 轮询索引，用于循环切换主模型（协程安全）
# 说明：本服务运行在 asyncio 单线程事件循环中，协程只在 await 处发生切换。
# 本函数内无任何 await，对 _robin_idx 的读写是原子的，无需加锁也不会阻塞主线程。
_robin_idx: int = 0


def _next_rotated_llms() -> tuple[list[ChatOpenAI], int]:
    """获取轮转后的 LLM 列表，当前轮到的排在第一位

    协程安全：函数体内无 await，事件循环不会中途切换协程，因此对全局
    _robin_idx 的递增操作是原子性的，不会与其他协程产生竞态。
    """
    global _robin_idx
    idx = _robin_idx
    _robin_idx = (
        _robin_idx + 1) % len(_free_api_llms) if _free_api_llms else 0
    rotated = _free_api_llms[idx:] + _free_api_llms[:idx]
    return rotated, idx


def _map_kwargs_for_openai(kwargs: dict[str, Any]) -> dict[str, Any]:
    """将 ChatOllama 的采样参数映射为 ChatOpenAI 兼容的参数"""
    mapped: dict[str, Any] = {}
    for k, v in kwargs.items():
        if k == "num_predict":
            mapped["max_tokens"] = v
        elif k == "top_k":
            continue  # ChatOpenAI 不支持 top_k
        else:
            mapped[k] = v
    return mapped


def get_llm(force_local: bool = False, **kwargs: Any):
    """获取 LLM 实例，可选传入采样参数

    从 llm_apis 列表中轮询选择主模型，其余作为 fallback，全部失败后回退到本地 LM Studio。
    未配置外部 API 时直接使用本地 LM Studio。

    用法：
        llm = get_llm(temperature=0.7, num_predict=256)
        structured_llm = llm.with_structured_output(schema=MyModel)
    """
    has_free_api = bool(_free_api_llms)
    logger.info(f"获取LLM实例，has_free_api={has_free_api}, kwargs={kwargs}")

    if force_local:
        logger.info("强制使用本地llama.cpp")
        if not kwargs:
            return _local_llm
        return _local_llm.bind(**kwargs)

    if not kwargs:
        if has_free_api:
            rotated, idx = _next_rotated_llms()
            primary = rotated[0]
            fallbacks = rotated[1:] + [_local_llm]
            logger.info(f"轮询使用外部API [{idx}]: {primary.model_name}")
            return primary.with_fallbacks(fallbacks)
        logger.info("无外部API配置，使用本地LM Studio")
        return _local_llm

    local_bound = _local_llm.bind(**kwargs)
    if not has_free_api:
        logger.info("无外部API配置，使用本地LM Studio（带参数绑定）")
        return local_bound

    openai_kwargs = _map_kwargs_for_openai(kwargs)
    logger.info(f"映射后的OpenAI参数: {openai_kwargs}")
    rotated, idx = _next_rotated_llms()
    primary = rotated[0].bind(**openai_kwargs) if openai_kwargs else rotated[0]
    logger.info(f"轮询使用外部API [{idx}]: {rotated[0].model_name}")
    fallbacks = [
        llm.bind(**openai_kwargs) if openai_kwargs else llm
        for llm in rotated[1:]
    ]
    fallbacks.append(local_bound)
    logger.info(f"设置{len(fallbacks)}个fallback（含本地LM Studio）")
    return primary.with_fallbacks(fallbacks)


if __name__ == "__main__":
    response = _local_llm.invoke("你好")
    logger.info(response)
