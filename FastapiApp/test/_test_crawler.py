import asyncio
import random
from typing import AsyncGenerator, Literal
from Service.BaseCrawler.CrawlerType import UnlimitedCrawler
from Service.BaseCrawler.model.base import WorkerModel, WorkerStatus
from Service.BaseCrawler.plugin.statusPlugin import StatsPlugin
from Models.base.custom_pydantic import CustomBaseModelHashable

class TestParamsType(CustomBaseModelHashable):
    a: int
    test_type: Literal["normal", "timeout", "error"] = (
        "normal"  # normal, timeout, error
    )

    def __hash__(self) -> int:
        return hash(self.a)


class TestCrawler(UnlimitedCrawler):
    def __init__(self, gen_num: int = 1000000, max_sem: int = 100):
        self.stats_plugin = StatsPlugin(self)

        super().__init__(
            plugins=[self.stats_plugin],  # 启用 StatsPlugin
            requeue_on_fetch_fail=True,  # 启用失败重试
            requeue_on_timeout=True,  # 暂时禁用超时重试
            max_retries=-1,  # 最大重试次数（-1表示无限重试）
            worker_max_timeout=None,  # 暂时禁用超时
            log_timeout_error=False,
            log_error=False,
            max_sem=max_sem,
        )
        self._count = 0
        print("初始化")
        self.params_arr = []
        self.limit_mode = True
        self.success_count = 0
        self.fail_count = 0
        self.timeout_count = 0
        self.gen_num: int = gen_num
        self.all_results = ["normal", "error", "timeout"]
        self._mode = "mixed"  # 记录当前模式
        self.params_arr = []
        self.limit_mode = True

    async def handle_fetch(self, params: TestParamsType) -> WorkerStatus:
        # 保存原始的 test_type（只在第一次执行时保存）
        self.log.info(f'处理任务:{params}')
        await asyncio.sleep(random.randint(0, 4))
        # 根据测试类型模拟不同的场景
        if params.test_type == "timeout":
            if self.worker_max_timeout:
                await asyncio.sleep(random.randint(self.worker_max_timeout, self.worker_max_timeout+4))
            raise asyncio.TimeoutError()
            return WorkerStatus.complete
        elif params.test_type == "error":
            # 模拟错误：总是抛出异常
            raise Exception(f"模拟错误: 任务 {params.a}")
        else:
            # 正常任务：总是返回成功状态，避免无限重试
            return WorkerStatus.complete

    async def on_task_requeue(self, worker_model: WorkerModel[TestParamsType]):
        """任务重新入队前，随机重新分配参数类型"""
        # 随着重试次数增加，增加分配为 normal 的概率
        # 这样可以确保任务最终会成功，避免无限重试
        retry_count = worker_model.retry_count
        # 基础概率：30% normal，35% error，35% timeout
        # 每次重试增加 10% 的 normal 概率，最多 90%
        normal_prob = min(0.3 + retry_count * 0.1, 0.9)
        remaining = 1.0 - normal_prob
        error_prob = remaining / 2
        timeout_prob = remaining / 2

        rand_val = random.random()
        if rand_val < normal_prob:
            worker_model.params.test_type = "normal"
        elif rand_val < normal_prob + error_prob:
            worker_model.params.test_type = "error"
        else:
            worker_model.params.test_type = "timeout"

        print(
            f"任务 {worker_model.params.a} 第 {worker_model.retry_count} 次重试, 分配类型为: {worker_model.params.test_type} (normal_prob={normal_prob:.2f})"
        )

    async def on_worker_end(self, worker_model: WorkerModel[TestParamsType]):
        """只在第一次执行时统计(不统计重试)"""
        # 调用 super().on_worker_end()，让插件回调正常执行
        await super().on_worker_end(worker_model)

    async def key_params_gen(
        self, params: TestParamsType
    ) -> AsyncGenerator[TestParamsType, None]:
        if self.limit_mode:
            # 简化测试用例
            test_cases = [
                (1, "normal"),
                (2, "error"),  # 会失败并重试
                (3, "normal"),
                (4, "error"),
                (5, "error"),
                (6, "error"),
                (7, "timeout"),
                (8, "error"),
                (9, "timeout"),
                (10, "error"),
                (11, "timeout"),
                (12, "error"),
            ]
            for i, (value, test_type) in enumerate(test_cases):
                print(
                    f"[生成器] 准备 yield 第 {i+1} 个任务: a={value}, test_type={test_type}"
                )
                yield TestParamsType(a=value, test_type=test_type)
                print(f"[生成器] 完成 yield 第 {i+1} 个任务")
            print(f"[生成器] 所有任务已 yield，生成器结束")
            return
        else:
            # 第二种模式：生成有限数量任务用于测试重试机制
            # 初始化起始值
            start_id = params.a if params is not None else 1
            for i in range(start_id, start_id + self.gen_num):
                # 随机选择任务类型
                test_type = random.choice(self.all_results)
                yield TestParamsType(a=i, test_type=test_type)

    async def is_stop(self) -> bool:
        return False

    async def on_run_end(self, end_param):
        print(f"结束参数：{end_param}")
        print(
            f"统计信息: 成功={self.success_count}, 失败={self.fail_count}, 超时={self.timeout_count}, 总计={self._count}"
        )
        print(f"模式: {self._mode}, gen_num: {self.gen_num}")

    async def main(self):
        # print("\n=== 第一种模式：混合测试 ===")
        # self.limit_mode = True
        # self._mode = "mixed"
        # await self.run()
        # print(self.stats_plugin.get_all_status())
        # print("\n=== 最终统计 ===")
        # print(
        #     f'=== 第一种模式：混合测试 === \n统计信息: 成功={self.success_count}, 失败={self.fail_count}, 超时={self.timeout_count}, 总计={self._count}')
        print("\n=== 第二种模式：随机测试 ===")
        self.limit_mode = False
        self._mode = "random"
        # 重置统计
        self._count = 0
        self.success_count = 0
        self.fail_count = 0
        self.timeout_count = 0
        await self.run()
        print("\n=== 最终统计 ===")
        print(
            f"=== 第二种模式：随机测试 ===\n统计信息: {self.stats_plugin.get_all_status()}"
        )


async def _test():
    a = TestCrawler(gen_num=10, max_sem=2)
    await a.main()


if __name__ == "__main__":
    asyncio.run(_test())