import asyncio

import sys

import time

import threading

import os


async def osexec(osarg: str):
    sys.path.insert(0, f"{'/'.join(osarg.split('/')[0:-1])}/")
    os.system(f"cd {'/'.join(osarg.split('/')[0:-1])}/")
    os.system(f"python {osarg}")
    # await asyncio.sleep(1)


def schedule():
    asyncio.run(osexec("../测试专用/JD.py"))
    asyncio.run(osexec("../哔哩哔哩直播/每日打卡.py"))
    asyncio.run(osexec("../哔哩哔哩直播/异想少女（每日必跑）.py"))
    asyncio.run(osexec("../哔哩哔哩直播/会员购ip任务（每日运行）.py"))
    asyncio.run(osexec("../哔哩哔哩直播/账号：斯卡蒂/fansMedalHelper/main.py"))
    asyncio.run(osexec("../哔哩哔哩直播/账号：保加利亚/fansMedalHelper/main.py"))


if __name__ == "__main__":
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    schedule()
    print('使用内置定时器,开启定时任务,等待时间到达后执行')
    schedulers = BlockingScheduler()
    schedulers.add_job(schedule, 'interval', days=1)
    schedulers.start()
