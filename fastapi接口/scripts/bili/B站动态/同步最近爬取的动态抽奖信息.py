"""
重新获取有lot_id，但是lotdata没存进去的抽奖
"""
import asyncio

from fastapi接口.service.grpc_module.src.getDynDetail import dyn_detail_scrapy


async def main():
    await dyn_detail_scrapy.get_lost_lottery_notice(limit_ts=1 * 365 * 24 * 3600)  # 获取最近一年的动态！


if __name__ == '__main__':
    asyncio.run(main())
