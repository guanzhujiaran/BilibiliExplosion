from typing import Generic
import asyncio
from abc import abstractmethod
from types import EllipsisType
from typing import Any, AsyncGenerator, List
from Service.BaseCrawler.base.core import BaseCrawler
from Service.BaseCrawler.model.base import WorkerModel, WorkerStatus, ParamsType
from Service.BaseCrawler.plugin.base import CrawlerPlugin
from Utils.Common import asyncio_gather


class UnlimitedCrawler(BaseCrawler[ParamsType], Generic[ParamsType]):
    """
    无限爬虫基类，支持动态生成任务并执行

    特性：
    - 支持插件扩展（统计、监控、限制等）
    - 支持任务失败重入队
    - 支持并发控制（通过信号量）
    - 自动管理任务队列和 worker 线程池

    使用示例：
        class MyCrawler(UnlimitedCrawler[MyParams]):
            async def is_stop(self) -> bool:
                # 判断是否应该停止生成新任务
                return False

            async def key_params_gen(self, params=None) -> AsyncGenerator[MyParams, None]:
                # 动态生成任务参数
                for i in range(100):
                    yield MyParams(id=i)

            async def handle_fetch(self, params: MyParams) -> WorkerStatus:
                # 处理单个任务
                await self.fetch_data(params)
                return WorkerStatus.complete
    """

    _plugins: List[CrawlerPlugin[ParamsType]]

    def __init__(
        self,
        plugins: List[CrawlerPlugin[ParamsType]] = None,
        requeue_on_fetch_fail: bool = False,
        worker_max_timeout: int | None = None,
        log_timeout_error: bool = True,
        *args,
        **kwargs,
    ):
        """
        初始化无限爬虫

        Args:
            plugins (List[CrawlerPlugin[ParamsType]], optional): 插件列表，用于扩展功能
                常见插件：StatsPlugin（统计）、SequentialNullStopPlugin（连续空结果停止）等
                默认为 None（不使用插件）

            requeue_on_fetch_fail (bool, optional): 任务失败时是否重新入队
                True: 失败的任务会被放回队列重试
                False: 失败的任务不会重试，直接标记为失败
                注意：当 max_sem=1 时，设置为 True 可能导致死锁，已在代码中修复
                默认为 False

            max_timeout (int | None, optional): 单个任务的最大超时时间（秒）
                None: 不设置超时（依赖具体实现）
                整数: 设置超时时间，超时后会抛出 asyncio.TimeoutError
                默认为 None（未在当前实现中使用，保留用于扩展）

            log_timeout_error (bool, optional): 是否打印超时错误日志
                True: 打印超时错误日志（默认）
                False: 不打印超时错误日志
                默认为 True

            *args, **kwargs: 传递给父类 BaseCrawler 的参数
                包括：max_sem（最大并发数）、_logger（日志对象）等

        示例：
            crawler = MyCrawler(
                plugins=[StatsPlugin(self), SequentialNullStopPlugin(self, max_consecutive_nulls=100)],
                requeue_on_fetch_fail=True,
                max_sem=2,
                _logger=logger
            )
        """
        self.requeue_on_fetch_fail = requeue_on_fetch_fail
        self.worker_max_timeout = worker_max_timeout
        self.log_timeout_error = log_timeout_error
        if plugins is None:
            plugins = []
        super().__init__(*args, **kwargs)
        self._plugins = []
        for plugin in plugins:
            self.__register_plugin(plugin)

    @property
    def plugins(self) -> List[CrawlerPlugin[ParamsType]]:
        """
        获取已注册的插件列表

        Returns:
            List[CrawlerPlugin[ParamsType]]: 插件列表
                常见插件：StatsPlugin（统计）、SequentialNullStopPlugin（限制连续空结果）等
        """
        return self._plugins

    def __register_plugin(self, plugin: CrawlerPlugin[ParamsType]):
        """
        注册插件到爬虫实例

        Args:
            plugin: 要注册的插件对象

        功能：
        - 检查插件是否已注册（避免重复注册）
        - 添加插件到内部列表
        - 调用插件的 on_plugin_register 方法进行初始化

        注意：
        - 插件的注册顺序影响回调执行顺序
        - 如果插件已存在，不会重复注册
        """
        if plugin not in self._plugins:
            self._plugins.append(plugin)
            plugin.on_plugin_register()
            self.log.debug(
                self.format_log(
                    f"Plugin {plugin.__class__.__name__} registered to {self.__class__.__name__}."
                )
            )

    @abstractmethod
    async def is_stop(self) -> bool:
        """
        判断是否应该停止生成新任务

        Returns:
            bool: True 表示应该停止，False 表示继续生成任务

        实现示例：
            async def is_stop(self) -> bool:
                # 连续失败次数超过阈值时停止
                return self._fail_count >= 10
        """
        ...

    @abstractmethod
    async def key_params_gen(
        self, params: ParamsType | Any | None
    ) -> AsyncGenerator[EllipsisType, None]:
        """
        生成任务参数的异步生成器

        Args:
            params: 初始参数，用于确定从哪里开始生成

        Yields:
            EllipsisType: 生成的任务参数，实际类型由子类定义

        实现示例：
            async def key_params_gen(self, params: MyParams) -> AsyncGenerator[MyParams, None]:
                if params is None:
                    start_id = 1
                else:
                    start_id = params.id + 1

                for i in range(start_id, 1000):
                    yield MyParams(id=i)
                    await asyncio.sleep(0.1)  # 控制生成速度
        """
        yield ...

    @abstractmethod
    async def handle_fetch(self, params: ParamsType | None) -> WorkerStatus | Any:
        """
        处理单个任务，获取数据

        Args:
            params: 任务参数，由 key_params_gen 生成

        Returns:
            WorkerStatus | Any: 任务状态或返回值
                - WorkerStatus.complete: 任务成功完成
                - WorkerStatus.fail: 任务失败
                - 其他值: 表示任务成功完成，并返回具体数据

        实现示例：
            async def handle_fetch(self, params: MyParams) -> WorkerStatus:
                try:
                    data = await self.api.fetch(params.id)
                    await self.save_to_db(data)
                    return WorkerStatus.complete
                except Exception as e:
                    self.log.error(f"获取数据失败: {e}")
                    return WorkerStatus.fail
        """
        ...

    @abstractmethod
    async def main(self, *args, **kwargs):
        """
        爬虫的主入口方法，包含完整的业务逻辑流程

        可以包含以下内容：
        - 数据预处理
        - 调用 self.run() 执行爬取
        - 数据后处理
        - 结果统计和上报

        实现示例：
            async def main(self, *args, **kwargs):
                # 准备工作
                await self.init_database()

                # 执行爬取
                await self.run(init_params=MyParams(id=0))

                # 清理工作
                await self.close_connections()

                # 上报结果
                await self.send_report()
        """

    async def on_worker_start(self, worker_model: WorkerModel):
        """
        Worker 开始处理任务时的回调，触发所有插件的 on_worker_start 方法

        Args:
            worker_model: 包含任务参数、序列号、状态等信息的模型对象

        用途：
        - 记录任务开始时间
        - 更新任务状态统计
        - 初始化任务上下文
        """
        await asyncio_gather(
            *[x.on_worker_start(worker_model) for x in self._plugins], log=self.log
        )

    async def on_worker_end(self, worker_model: WorkerModel):
        """
        Worker 完成任务处理时的回调，触发所有插件的 on_worker_end 方法

        Args:
            worker_model: 包含任务参数、序列号、状态等信息的模型对象

        用途：
        - 更新任务统计信息（成功/失败计数）
        - 记录任务执行时长
        - 更新进度信息
        """
        await asyncio_gather(
            *[x.on_worker_end(worker_model) for x in self._plugins], log=self.log
        )

    async def on_run_end(self, end_param: ParamsType):
        """
        爬虫运行结束时的回调，触发所有插件的 on_run_end 方法

        Args:
            end_param: 最后一个任务参数（可能为 None）

        用途：
        - 生成统计报告
        - 清理资源
        - 保存最终状态
        - 发送通知
        """
        await asyncio_gather(
            *[x.on_run_end(end_param) for x in self._plugins], log=self.log
        )

    async def worker(self):
        """
        Worker 协程，从队列中获取任务并处理

        工作流程：
        1. 获取信号量（控制并发数）
        2. 从任务队列获取一个任务
        3. 触发 on_worker_start 回调
        4. 调用 handle_fetch 处理任务
        5. 处理异常情况
        6. 更新任务状态
        7. 触发 on_worker_end 回调
        8. 释放信号量
        9. 如果任务失败且需要重试，在信号量作用域外重新入队（避免死锁）

        重要：重新入队的操作必须在 async with self.sem 作用域外执行，
        否则当 max_sem=1 时可能导致死锁。
        """
        should_requeue = False

        async with self.sem:
            worker_model: WorkerModel = await self.task_queue.get()
            await self.on_worker_start(worker_model)
            try:
                async with asyncio.timeout(self.worker_max_timeout):
                    fetch_result = await self.handle_fetch(worker_model.params)
            except asyncio.TimeoutError:
                if self.log_timeout_error:
                    self.log.exception(
                        self.format_log(f"爬取超时：{self.worker_max_timeout}s")
                    )
                fetch_result = WorkerStatus.fail
                should_requeue = True  # 超时的任务都自动回到队列
                await asyncio.sleep(30)
            except Exception as e:
                self.log.exception(self.format_log(f"爬取异常：{e}"))
                fetch_result = WorkerStatus.fail
                if self.requeue_on_fetch_fail:
                    should_requeue = True
                else:
                    await asyncio.sleep(30)

            if not isinstance(fetch_result, WorkerStatus):
                worker_model.fetchStatus = WorkerStatus.complete
            else:
                worker_model.fetchStatus = fetch_result
            await self.on_worker_end(worker_model)

        # 在 sem 作用域外重新入队，避免死锁
        # 原因：如果在 sem 作用域内重新入队，当 max_sem=1 时，
        # worker 持有 sem 并等待队列中的任务，而任务需要另一个 worker（也需要 sem）来处理，
        # 但此时没有可用的 sem，导致死锁
        if should_requeue:
            await self.task_queue.put(worker_model)

    async def run(self, init_params: ParamsType | None = None):
        """
        爬虫的主运行方法，负责任务的生成和调度

        工作流程：
        1. 创建并处理初始任务
        2. 通过 key_params_gen 动态生成任务参数
        3. 将任务放入队列供 worker 处理
        4. 维护 worker 线程池（通过 task_set）
        5. 检查停止条件（is_stop 和插件的 should_stop_check）
        6. 支持暂停功能
        7. 等待所有 worker 完成任务
        8. 清理队列并触发 on_run_end

        Args:
            init_params: 初始任务参数，用于确定从哪里开始生成后续任务

        关键机制：
        - 任务队列：异步队列，用于在任务生成器和 worker 之间传递任务
        - 信号量（self.sem）：控制并发 worker 数量
        - 任务集合（task_set）：跟踪所有活跃的 worker 任务
        - 回调机制：task.add_done_callback(task_set.discard) 自动清理已完成的 worker

        注意：
        - 任务必须先放入队列，再创建 worker（确保 worker 能立即获取到任务）
        - seqId 用于标识任务的顺序，从 0 开始递增
        - 支持暂停：通过 self._is_pause 标志控制，暂停时每 10 秒检查一次
        """
        self.log.info(self.format_log(f"starting with init_params: {init_params}"))
        seqId = 0
        worker_model = WorkerModel(params=init_params, seqId=seqId)
        await asyncio_gather(
            *[x.on_run_start(worker_model) for x in self._plugins], log=self.log
        )
        task_set = set()
        # 处理初始参数（仅当 init_params 不为 None 时才入队执行）
        if init_params is not None:
            seqId += 1
            await self.task_queue.put(worker_model)
            task = asyncio.create_task(self.worker())
            task_set.add(task)
            task.add_done_callback(task_set.discard)
            self.log.debug(
                self.format_log(
                    f"当前线程存活数量：{len(task_set)}，队列大小：{self.task_queue.qsize()}，添加初始任务：{init_params}"
                )
            )
        # 开始循环
        async for param in self.key_params_gen(init_params):
            worker_model = WorkerModel(params=param, seqId=seqId)
            seqId += 1
            await self.task_queue.put(worker_model)  # 这个必须在最前面

            if await self.is_stop():
                self.log.info(self.format_log("触发终止条件，停止生成新任务。"))
                break

            if True in await asyncio_gather(
                *[x.should_stop_check() for x in self._plugins], log=self.log
            ):
                self.log.info(self.format_log("触发终止条件，停止生成新任务。"))
                break
            if self._is_pause:
                while self._is_pause:
                    await asyncio.sleep(10)

            task = asyncio.create_task(self.worker())
            task_set.add(task)
            task.add_done_callback(task_set.discard)
            self.log.debug(
                self.format_log(
                    f"当前线程存活数量：{len(task_set)}，队列大小：{self.task_queue.qsize()}，添加任务：{param}"
                )
            )
        self.log.critical(
            self.format_log(
                f"任务生成完成。正在等待剩余线程完成任务，当前存活线程数量：{len(task_set)}"
            )
        )
        await asyncio_gather(*task_set, log=self.log)
        self.log.info(self.format_log("所有任务已完成。"))
        await self.on_run_end(worker_model or None)

        self.log.info(self.format_log("run finished."))
        while not self.task_queue.empty():
            await self.task_queue.get()
