import random
from typing import Tuple
from fastapi接口.log.base_log import myfastapi_logger


class SleepTimeGenerator:
    def __init__(
            self,
            short_wait_range: Tuple[float, float] = (1, 5.0),  # 短等待时间范围 (秒)
            medium_wait_range: Tuple[float, float] = (7.0, 10.0),  # 中等等待时间范围 (秒)
            long_wait_range: Tuple[float, float] = (300, 600),  # 长等待时间范围 (秒)
            medium_wait_frequency: int = 5,  # 每 N 次访问触发一次中等等待 (例如：每 5 次)
            long_wait_frequency: int = 150,  # 每 M 次访问触发一次长等待 (例如：每 20 次)
            random_long_wait_probability: float = 0.0,  # 每次访问时随机触发长等待的概率 (0.0 - 1.0)
    ):
        """
        初始化一个模拟真人操作的等待时间生成器。

        Args:
            short_wait_range: 短等待时间的范围 (最小值, 最大值)，单位秒。
            medium_wait_range: 中等等待时间的范围 (最小值, 最大值)，单位秒。
            long_wait_range: 长等待时间的范围 (最小值, 最大值)，单位秒。
            medium_wait_frequency: 每 N 次访问进行一次中等等待的频率 (N > 0)。
            long_wait_frequency: 每 M 次访问进行一次长等待的频率 (M > 0)。
            random_long_wait_probability: 每次访问时随机触发长等待的概率 (0.0 到 1.0 之间)。
        """
        # 参数校验
        if not (0.0 <= random_long_wait_probability <= 1.0):
            raise ValueError("random_long_wait_probability 必须在 0.0 到 1.0 之间。")
        for r in [short_wait_range, medium_wait_range, long_wait_range]:
            if not (isinstance(r, tuple) and len(r) == 2 and r[0] >= 0 and r[0] <= r[1]):
                raise ValueError(f"等待时间范围 {r} 必须是 (min, max) 形式的元组，且 min >= 0, min <= max。")
        if not (isinstance(medium_wait_frequency, int) and medium_wait_frequency > 0):
            raise ValueError("medium_wait_frequency 必须是大于 0 的整数。")
        if not (isinstance(long_wait_frequency, int) and long_wait_frequency > 0):
            raise ValueError("long_wait_frequency 必须是大于 0 的整数。")

        self.short_wait_min, self.short_wait_max = short_wait_range
        self.medium_wait_min, self.medium_wait_max = medium_wait_range
        self.long_wait_min, self.long_wait_max = long_wait_range
        self.medium_wait_freq = medium_wait_frequency
        self.long_wait_freq = long_wait_frequency
        self.random_long_prob = random_long_wait_probability

    def get_wait_time(self, cnt: int) -> float:
        """
        根据当前访问次数 (cnt) 生成模拟真人的等待时间。

        生成逻辑优先级：长等待频率 > 中等等待频率 > 随机长等待 > 短等待。
        这意味着如果同时满足多个条件，优先级高的等待时间将被选择。

        Args:
            cnt: 当前的访问次数 (通常从 1 开始计数)。

        Returns:
            生成的等待时间，单位秒。
        """
        wait_time = 0.0

        # 优先判断是否达到长等待频率
        # 使用 cnt % self.long_wait_freq == 0 且 cnt > 0 确保只在大于0的 cnt 且能被整除时触发
        if self.long_wait_freq > 0 and cnt > 0 and (cnt % self.long_wait_freq == 0):
            wait_time = random.uniform(self.long_wait_min, self.long_wait_max)
            myfastapi_logger.info(f"Cnt {cnt}: 触发长等待 (固定频率): {wait_time:.2f}s")
        # 其次判断是否达到中等等待频率
        elif self.medium_wait_freq > 0 and cnt > 0 and (cnt % self.medium_wait_freq == 0):
            wait_time = random.uniform(self.medium_wait_min, self.medium_wait_max)
            myfastapi_logger.info(f"Cnt {cnt}: 触发中等等待 (固定频率): {wait_time:.2f}s")
        # 再次判断是否随机触发长等待
        elif random.random() < self.random_long_prob:
            wait_time = random.uniform(self.long_wait_min, self.long_wait_max)
            myfastapi_logger.info(f"Cnt {cnt}: 触发随机长等待 (概率): {wait_time:.2f}s")
        # 否则，使用短等待
        else:
            wait_time = random.uniform(self.short_wait_min, self.short_wait_max)
            myfastapi_logger.info(f"Cnt {cnt}: 触发短等待: {wait_time:.2f}s")

        return wait_time

    def continuous_generator(self):
        """
        一个辅助的 Python yield 生成器，用于连续生成等待时间，内部维护访问次数。
        每次调用 next() 或在 for 循环中使用时，会返回下一个等待时间。
        """
        cnt = 0
        while True:
            cnt += 1
            yield self.get_wait_time(cnt)
