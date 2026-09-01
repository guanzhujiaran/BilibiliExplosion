"""通用雪花 ID 生成器（自包含，不依赖具体业务项目的配置）。

所有**对外发布**的业务主键（uid、moment_id、topic_id 及后续新增实体 ID）
一律使用雪花 ID，禁止使用数据库自增主键对外暴露（见项目规则
`.codebuddy/rules/snowflake-id.mdc`）。

## 设计

- **通用生成器 `SnowflakeIdGenerator`**：位宽（`timestamp_bits`/`worker_bits`/
  `sequence_bits`）与时间单位（`minute` / `millisecond`）均可配置，分钟级短 ID
  与毫秒级大容量 msgkey 由同一实现参数化生成，避免两套重复算法。
- **兼容特化 `MinuteSnowflakeIdGenerator`**：分钟步进短 ID（位布局见下），
  签名 `(worker_id, epoch_sec)` 与位布局保持不变，对外 ID 数值不变。

## 位布局（分钟级短 ID，分钟步进）

    | 时间戳(分钟, 相对 epoch) | 4 bits worker_id | N bits 序列号 |

总位数恒为 39 bits，保证正数且初始约 7~8 位十进制。默认 `sequence_bits=4`
（时间戳 31 bits），同一 worker 每分钟最多 16 个；`sequence_bits` 可放宽
（如 7 → 每分钟 128 个），时间戳位宽相应缩减（`31-(sequence_bits-4)`），
**仅限清库重建的开发/测试环境启用**（变更位宽会与已发布 ID 数值重叠）。

## 并发安全（异步锁外等待，不持锁自旋）

`next()` 是 **async** 方法，仅在锁内做**极短临界区**（读时间戳 + 序列号递增 +
位运算，微秒级）。当同一时间片内序列号耗尽时，**不在锁内 `while` 忙等**（旧同步
实现会持锁自旋到下一时间片，分钟级最坏阻塞事件循环近 60s），而是记录目标
时间片、**释放锁后 `await asyncio.sleep`** 到下一时间片再重试——不阻塞事件循环，
避免极端流量下持锁自旋阻塞 asyncio 服务。

## 用法

不同实体各自 `MinuteSnowflakeIdGenerator(worker_id, epoch_sec)` 独立实例化，
使各实体落在不同数值空间，避免跨实体在同一分钟内碰撞（即使共用 BIGINT 列）。

```python
from bili_common.core.snowflake import MinuteSnowflakeIdGenerator

_g_topic = MinuteSnowflakeIdGenerator(
    worker_id=settings.topic_id_worker_id,
    epoch_sec=settings.topic_id_epoch_sec,
)

async def generate_topic_id() -> int:
    return await _g_topic.next()
```
"""

import asyncio
import threading
import time
from loguru import logger
__all__ = ["MinuteSnowflakeIdGenerator", "SnowflakeIdGenerator"]


class SnowflakeIdGenerator:
    """可配置雪花 ID 生成器（线程安全，序列耗尽时异步锁外等待）。

    Args:
        worker_id: worker 编号（0 ~ 2**worker_bits - 1）。
        epoch: 起始时间戳，单位与 `time_unit` 一致（分钟级传分钟、毫秒级传毫秒）。
        timestamp_bits: 时间戳位数。
        worker_bits: worker 位数。
        sequence_bits: 序列号位数。
        time_unit: 时间戳步进单位，"minute" / "millisecond"。
    """

    _TIME_UNITS = ("minute", "millisecond")

    def __init__(
        self,
        *,
        worker_id: int,
        epoch: int,
        timestamp_bits: int,
        worker_bits: int,
        sequence_bits: int,
        time_unit: str,
    ) -> None:
        if time_unit not in self._TIME_UNITS:
            raise ValueError(f"time_unit 必须为 {self._TIME_UNITS} 之一，当前为 {time_unit}")
        max_worker = (1 << worker_bits) - 1
        if not 0 <= worker_id <= max_worker:
            raise ValueError(f"worker_id 必须在 0~{max_worker} 之间，当前为 {worker_id}")
        self._worker_id = worker_id
        self._epoch = epoch
        self._time_unit = time_unit
        self._timestamp_bits = timestamp_bits
        self._worker_bits = worker_bits
        self._sequence_bits = sequence_bits
        self._max_sequence = (1 << sequence_bits) - 1
        # 位偏移：时间戳字段 = 序列号 + worker 位宽；worker 字段 = 序列号位宽
        self._timestamp_shift = sequence_bits + worker_bits
        self._worker_shift = sequence_bits
        self._sequence = 0
        self._last_ts = -1
        self._lock = threading.Lock()

    @property
    def timestamp_shift(self) -> int:
        """时间戳字段的位偏移（供反解时间戳 / 分库路由使用）。"""
        return self._timestamp_shift

    def _now_ts(self) -> int:
        """当前时间片数值（与 `time_unit` 同单位）。"""
        if self._time_unit == "minute":
            return int(time.time() // 60)
        return int(time.time() * 1000)

    def _tick_to_seconds(self, ts: int) -> float:
        """把时间片数值换算为绝对秒时间戳（用于锁外等待）。"""
        if self._time_unit == "minute":
            return ts * 60.0
        return ts / 1000.0

    async def _sleep_until_tick(self, target_ts: int) -> None:
        """锁外等待到目标时间片开始（target_ts 未到则异步 sleep）。"""
        delay = self._tick_to_seconds(target_ts) - time.time()
        if delay > 0:
            logger.warning(f"snowflake: 锁外等待 {delay}s 到 {target_ts} 时间片")
            await asyncio.sleep(delay)

    def _pack(self, ts: int, seq: int) -> int:
        return (
            ((ts - self._epoch) << self._timestamp_shift)
            | (self._worker_id << self._worker_shift)
            | seq
        )

    async def next(self) -> int:
        """生成下一个雪花 ID（async，序列耗尽时锁外异步等待，不阻塞事件循环）。"""
        while True:
            with self._lock:
                ts = self._now_ts()
                if ts <= self._last_ts:
                    # 同一时间片或时钟回拨：沿用 last_ts，序列号递增
                    ts = self._last_ts
                    seq = self._sequence + 1
                    if seq > self._max_sequence:
                        # 序列号耗尽：锁外等待下一时间片，不在锁内忙等
                        target_ts = ts + 1
                    else:
                        self._sequence = seq
                        return self._pack(ts, seq)
                else:
                    self._last_ts = ts
                    self._sequence = 0
                    return self._pack(ts, 0)
            await self._sleep_until_tick(target_ts)


class MinuteSnowflakeIdGenerator(SnowflakeIdGenerator):
    """分钟步进短雪花 ID 生成器（兼容特化，默认签名与位布局不变）。

    Args:
        worker_id: worker 编号（0~15），多实例部署时互不相同。
        epoch_sec: epoch（秒级时间戳）。内部统一换算成分钟级，避免
            `(ts_minutes - epoch_sec)` 单位错配导致生成负数 ID。
        sequence_bits: 序列号位宽，默认 4（每 worker 每分钟最多 16 个）。
            放宽时时间戳位宽相应缩减为 `39 - 4 - sequence_bits`，**总位数恒为
            39 bits**。⚠️ 变更位宽会改变对外 ID 数值空间，与已发布 ID 可能重叠，
            仅允许在清库重建（无历史 ID）的开发/测试环境启用；生产保持默认 4。
    """

    def __init__(
        self, worker_id: int, epoch_sec: int, *, sequence_bits: int = 4
    ) -> None:
        if not 4 <= sequence_bits <= 15:
            raise ValueError(
                f"sequence_bits 必须在 4~15 之间（总位数恒 39 bits），当前为 {sequence_bits}"
            )
        super().__init__(
            worker_id=worker_id,
            # 入参 epoch_sec 是秒级时间戳，生成器以「分钟」为步进单位，统一换算成分钟级 epoch
            epoch=epoch_sec // 60,
            # 时间戳位宽 = 39 - worker_bits(4) - sequence_bits，总位数恒为 39
            timestamp_bits=39 - 4 - sequence_bits,
            worker_bits=4,
            sequence_bits=sequence_bits,
            time_unit="minute",
        )
