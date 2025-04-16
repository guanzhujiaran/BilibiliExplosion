import asyncio
import os
import time
from loguru import logger
import fastapi接口.service.toutiao.src.spider.SpaceFeed.SpaceFeedScrapy as SpaceFeedScrapy

ToutiaoSpaceFeedSpider, FileMap = SpaceFeedScrapy.ToutiaoSpaceFeedSpider, SpaceFeedScrapy.FileMap


class ToutiaoSpaceFeedLotService:
    def __init__(self):
        self.is_getting_lot_id = False
        self.last_get_lot_id_timestamp = int(time.time())
        self.get_lot_sep_time = 0.8 * 24 * 3600

    def read_last_get_lot_timestamp(self):
        try:
            if os.path.exists(FileMap.last_get_lot_id_timestamp):
                with open(FileMap.last_get_lot_id_timestamp, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self.last_get_lot_id_timestamp = int(content)
            else:
                self.last_get_lot_id_timestamp = 0
                self.write_last_get_lot_id_timestamp()
        except Exception as e:
            logger.error(e)
            self.last_get_lot_id_timestamp = 0
            # self.write_last_get_lot_id_timestamp()

    def write_last_get_lot_id_timestamp(self):
        try:
            with open(FileMap.last_get_lot_id_timestamp, 'w', encoding='utf-8') as f:
                f.write(str(self.last_get_lot_id_timestamp))
        except Exception as e:
            logger.error(e)
            self.last_get_lot_id_timestamp = int(time.time())

    def generate_lot_id_list(self):
        lot_id_list = []
        with open(FileMap.rsult_latest, 'r', encoding='utf-8') as f:
            result = f.readlines()
            for i in result:
                lot_id_list.append(i.split('\t')[1])
        lot_id_list.sort(reverse=True)
        return lot_id_list

    async def main(self) -> [str]:
        try:
            while self.is_getting_lot_id:
                logger.info(f'头条抽奖数据获取中...')
                await asyncio.sleep(10)
            self.read_last_get_lot_timestamp()  # 获取最后一次获取头条空间的时间
            if int(time.time()) - self.last_get_lot_id_timestamp > self.get_lot_sep_time:
                self.is_getting_lot_id = True
                spider = ToutiaoSpaceFeedSpider()
                await spider.main()
                self.last_get_lot_id_timestamp = int(time.time())
                self.write_last_get_lot_id_timestamp()
                self.is_getting_lot_id = True
            ret_list = self.generate_lot_id_list()
            logger.info(f'头条抽奖数据获取完成！共计{len(ret_list)}条！')
            return ret_list
        except Exception as e:
            logger.exception(e)
        finally:
            self.is_getting_lot_id = False


toutiaoSpaceFeedLotService = ToutiaoSpaceFeedLotService()
