"""vLLM 模型服务（Singleton），管理 Qwen3.5-0.8B 的加载、推理与生命周期

特性：
- 单例模式：全局唯一实例，避免重复加载
- 懒加载：首次调用时加载模型
- 空闲超时自动卸载：超过 _IDLE_TIMEOUT 秒未使用后释放显存
- 全异步：基于 AsyncLLMEngine 实现，无需 asyncio.to_thread
"""
from vllm.config import VllmConfig, ModelConfig
import asyncio
import time
import uuid
from enum import StrEnum
from typing import Any
from loguru import logger
from vllm import AsyncEngineArgs, AsyncLLMEngine, SamplingParams
import os
# ============ 采样参数预设（基于 Qwen3.5 官方最佳实践） ============

_PRESET_KWARGS: dict["SamplingPreset", dict[str, Any]] = {}


class SamplingPreset(StrEnum):
    """Qwen3.5 采样参数预设

    基于官方最佳实践，按模式和任务类型分为 4 组预设。
    使用 `preset.to_params(**overrides)` 获取 SamplingParams 实例。
    """
    TEXT_NON_THINKING = "text_non_thinking"   # 文本任务，非思考模式
    VL_NON_THINKING = "vl_non_thinking"       # 视觉-语言任务，非思考模式
    TEXT_THINKING = "text_thinking"           # 文本任务，思考模式
    VL_THINKING = "vl_thinking"               # 视觉-语言 / 精确编码任务，思考模式

    def to_params(self, **overrides: Any) -> SamplingParams:
        """根据预设创建 SamplingParams，支持通过 overrides 覆盖任务特定参数

        :param overrides: 覆盖参数，如 max_tokens, stop 等
        """
        kwargs = dict(_PRESET_KWARGS[self])
        kwargs.update(overrides)
        return SamplingParams(**kwargs)


_PRESET_KWARGS.update({
    SamplingPreset.TEXT_NON_THINKING: dict(
        temperature=1.0, top_p=1.00, top_k=20, extra_args={"enable_thinking": False}, min_p=0.0,
        presence_penalty=2.0, repetition_penalty=1.0,
    ),
    SamplingPreset.VL_NON_THINKING: dict(
        temperature=0.7, top_p=0.80, top_k=20, extra_args={"enable_thinking": False}, min_p=0.0,
        presence_penalty=1.5, repetition_penalty=1.0,
    ),
    SamplingPreset.TEXT_THINKING: dict(
        temperature=1.0, top_p=0.95, top_k=20, extra_args={"enable_thinking": True}, min_p=0.0,
        presence_penalty=1.5, repetition_penalty=1.0,
    ),
    SamplingPreset.VL_THINKING: dict(
        temperature=0.6, top_p=0.95, top_k=20, extra_args={"enable_thinking": True}, min_p=0.0,
        presence_penalty=0.0, repetition_penalty=1.0,
    ),
})


# ============ LLM 服务单例 ============


class LLMService:
    """vLLM 模型服务单例

    使用 __new__ 实现线程安全的单例，基于 AsyncLLMEngine 实现全异步推理。
    """

    _instance: "LLMService | None" = None
    _lock = asyncio.Lock()

    _MODEL_NAME = "Qwen/Qwen3.5-0.8B"
    _IDLE_TIMEOUT = 30 * 60  # 30 分钟

    def __new__(cls) -> "LLMService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._engine: AsyncLLMEngine | None = None
            cls._instance._last_use_ts: float = 0.0
            cls._instance._unload_task: asyncio.Task | None = None
        return cls._instance

    # ---------- 模型加载 / 卸载 ----------

    def _load(self) -> AsyncLLMEngine:
        """加载 Qwen3.5-0.8B 模型（int4 量化，language-model-only）

        from_engine_args 是同步方法，不阻塞事件循环时直接调用。
        """
        logger.debug(f"Loading model {self._MODEL_NAME}")
        llm = AsyncLLMEngine.from_vllm_config(
            vllm_config=VllmConfig(
                model_config=ModelConfig(
                    model=self._MODEL_NAME,
                    dtype="auto",
                    trust_remote_code=True,
                    max_model_len=2 * 1024,
                    enforce_eager=True,
                    language_model_only=True,
                ),
            )
        )
        logger.debug(f"Model {self._MODEL_NAME} loaded")
        return llm

    def _unload(self) -> None:
        """卸载模型，释放显存"""
        logger.debug("Unloading model %s", self._MODEL_NAME)
        if self._engine is not None:
            del self._engine
            self._engine = None

    # ---------- 空闲超时调度 ----------

    def _schedule_unload(self) -> None:
        """调度延迟卸载：_IDLE_TIMEOUT 秒后若未被使用则卸载"""
        if self._unload_task is not None and not self._unload_task.done():
            self._unload_task.cancel()

        async def _delayed_unload():
            await asyncio.sleep(self._IDLE_TIMEOUT)
            self._unload()

        try:
            self._unload_task = asyncio.create_task(_delayed_unload())
        except RuntimeError:
            pass

    # ---------- 公开接口 ----------

    async def _ensure_loaded(self) -> AsyncLLMEngine:
        """确保模型已加载，更新最后使用时间并重新调度卸载"""
        logger.debug(f"Ensuring model {self._MODEL_NAME} is loaded")
        async with self._lock:
            if self._engine is None:
                self._engine = self._load()
            self._last_use_ts = time.time()
            self._schedule_unload()
            return self._engine

    async def generate(
        self, prompt: str, sampling_params: SamplingParams
    ) -> str:
        """生成文本

        :param prompt: 提示词
        :param sampling_params: 采样参数
        :return: 生成的文本
        """
        engine = await self._ensure_loaded()
        request_id = str(uuid.uuid4())
        final_output = None
        async for request_output in engine.generate(
            prompt, sampling_params, request_id
        ):
            final_output = request_output
        logger.debug(f"Generated text: {final_output}")
        return (
            final_output.outputs[0].text
            if final_output and final_output.outputs
            else ""
        )

    @property
    def is_loaded(self) -> bool:
        return self._engine is not None
