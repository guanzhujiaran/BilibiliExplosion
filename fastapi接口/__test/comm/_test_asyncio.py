import asyncio
import logging
import time


async def background_task(task_id):
    print(f"[Task {task_id}] Started")
    await asyncio.sleep(2)  # 模拟耗时操作
    print(f"[Task {task_id}] Finished")


async def main():
    print("Starting main function...")

    # 启动多个后台任务，但不 await 它们
    for i in range(1, 6):
        asyncio.create_task(background_task(i)) # noqa

    print("Main function continues to run...")
    await asyncio.sleep(3)  # 主协程做一些其他事情
    print("Main function ends. Background tasks continue...")


# 运行事件循环
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(),debug=True)