"""通用雪花 ID 生成器（自包含，不依赖具体业务项目的配置）。

所有**对外发布**的业务主键（uid、moment_id、topic_id 及后续新增实体 ID）
一律使用雪花 ID，禁止使用数据库自增主键对外暴露（见项目规则
`.codebuddy/rules/snowflake-id.mdc`）。

## 位布局（短 ID，分钟步进）

    | 31 bits 时间戳(分钟, 相对 epoch) | 4 bits worker_id | 4 bits 序列号 |

共 39 bits，保证正数且初始约 7~8 位十进制。同一 worker 每分钟最多生成 16 个 ID。

## 用法

不同实体各自 `MinuteSnowflakeIdGenerator(worker_id, epoch_sec)` 独立实例化，
使各实体落在不同数值空间，避免跨实体在同一分钟内碰撞（即使共用 BIGINT 列）。

```python
from bili_common.core.snowflake import MinuteSnowflakeIdGenerator

_g_topic = MinuteSnowflakeIdGenerator(
    worker_id=settings.topic_id_worker_id,
    epoch_sec=settings.topic_id_epoch_sec,
)

def generate_topic_id() -> int:
    return _g_topic.next()
```
"""

import threading
import time

_SEQUENCE_BITS = 4
_WORKER_BITS = 4

_MAX_SEQUENCE = (1 << _SEQUENCE_BITS) - 1  # 15
_MAX_WORKER_ID = (1 << _WORKER_BITS) - 1  # 15

_WORKER_SHIFT = _SEQUENCE_BITS  # 4
_TIMESTAMP_SHIFT = _SEQUENCE_BITS + _WORKER_BITS  # 8


class MinuteSnowflakeIdGenerator:
    """分钟步进雪花 ID 生成器（线程安全）。

    Args:
        worker_id: worker 编号（0~15），多实例部署时互不相同。
        epoch_sec: epoch（秒级时间戳）。内部统一换算成分钟级，避免
            `(ts_minutes - epoch_sec)` 单位错配导致生成负数 ID。
    """

    def __init__(self, worker_id: int, epoch_sec: int) -> None:
        if not 0 <= worker_id <= _MAX_WORKER_ID:
            raise ValueError(f"worker_id 必须在 0~{_MAX_WORKER_ID} 之间，当前为 {worker_id}")
        self._worker_id = worker_id
        # 入参 epoch_sec 是秒级时间戳，生成器以「分钟」为步进单位，统一换算成分钟级 epoch
        self._epoch_minute = epoch_sec // 60
        self._sequence = 0
        self._last_ts = -1
        self._lock = threading.Lock()

    @staticmethod
    def _now_minute() -> int:
        return int(time.time() // 60)

    def next(self) -> int:
        """生成下一个短雪花 ID。"""
        with self._lock:
            ts = self._now_minute()
            ts = max(ts, self._last_ts)
            if ts == self._last_ts:
                self._sequence = (self._sequence + 1) & _MAX_SEQUENCE
                if self._sequence == 0:
                    # 当前分钟序列号耗尽，自旋到下一分钟
                    while ts <= self._last_ts:
                        ts = self._now_minute()
            else:
                self._sequence = 0
            self._last_ts = ts
            return (
                ((ts - self._epoch_minute) << _TIMESTAMP_SHIFT)
                | (self._worker_id << _WORKER_SHIFT)
                | self._sequence
            )


__all__ = ["MinuteSnowflakeIdGenerator"]
