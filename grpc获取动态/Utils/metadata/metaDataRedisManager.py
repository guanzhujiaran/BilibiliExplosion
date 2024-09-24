import asyncio
import json
import pickle
import time
from dataclasses import asdict
from enum import Enum
import random

from loguru import logger

from CONFIG import CONFIG
from grpc获取动态.Models.GrpcApiBaseModel import MetaDataWrapper
from grpc获取动态.Utils.metadata.makeMetaData import is_useable_Dalvik, make_metadata
from grpc获取动态.grpc.bapi.biliapi import get_latest_version_builds
from grpc获取动态.grpc.bapi.models import LatestVersionBuild
from utl.redisTool.RedisManager import RedisManagerBase


class MetaDataRedisManagerPool(RedisManagerBase):
    """
    metadata池
    """

    class RedisMap(str, Enum):
        metaData = "metaData"

    def __init__(self):
        super().__init__(db=14)
        self.PoolSize = 50  # 元数据池大小
        self.my_proxy_addr = CONFIG.my_ipv6_addr
        self.channel_list = ['bili', 'master', 'yyb', '360', 'huawei', 'xiaomi', 'oppo', 'vivo', 'google']  # 渠道包列表
        with open(CONFIG.root_dir + 'grpc获取动态/Utils/user-agents_dalvik_application_2-1.json', 'r',
                  encoding='utf-8') as f:
            self.Dalvik_list = json.loads(f.read())
            self.Dalvik_list = list(filter(lambda x: 'Dalvik/2.1.0' in x
                                                     and '[ip:' not in x
                                                     and 'AppleWebKit' not in x
                                           , self.Dalvik_list))
        self.brand_list = ['Xiaomi', 'Huawei', 'Samsung', 'Vivo', 'Oppo', 'Oneplus', 'Meizu', 'Nubia', 'Sony', 'Zte',
                           'Honor', 'Lenovo', 'Lg', 'Blu', 'Asus', 'Panasonic', 'Htc', 'Nokia', 'Motorola', 'Realme',
                           'Alcatel', 'BlackBerry']
        self.version_name_build_list: [LatestVersionBuild] = [LatestVersionBuild(**x) for x in [
            {
                "build": 8000200,
                "version": "8.0.0"
            },
            {
                "build": 7810200,
                "version": "7.81.0"
            },
            {
                "build": 7800300,
                "version": "7.80.0"
            },
            {
                "build": 7790400,
                "version": "7.79.0"
            },
            {
                "build": 7780300,
                "version": "7.78.0"
            },
            {
                "build": 7770300,
                "version": "7.77.0"
            },
            {
                "build": 7760700,
                "version": "7.76.0"
            },
            {
                "build": 7750300,
                "version": "7.75.0"
            },
            {
                "build": 7740200,
                "version": "7.74.0"
            },
            {
                "build": 7730300,
                "version": "7.73.0"
            },
            {
                "build": 7720200,
                "version": "7.72.0"
            },
            {
                "build": 7710300,
                "version": "7.71.0"
            }
        ]]
        try:
            self.version_name_build_list: [LatestVersionBuild] = get_latest_version_builds()[:10]  # 获取最新的build
        except Exception as e:
            logger.exception(e)

        loop = asyncio.get_event_loop()
        loop.create_task(self._start_periodic_task())
        self._global_lock = asyncio.Lock()

    async def _start_periodic_task(self):
        """启动后台任务"""
        while 1:
            self.task = [asyncio.create_task(self._refresh_metadata())]
            await asyncio.gather(*self.task)
            await asyncio.sleep(60)

    async def _refresh_metadata(self):
        """
        刷新metadata
        :return:
        """
        async with self._global_lock:
            all_metadata = [MetaDataWrapper(**pickle.loads(x)) for x in await self._sget_all(self.RedisMap.metaData)]
            to_remove_hash_ids = [x.hash_id for x in all_metadata if x.expire_ts > time.time() or x.able == False]
            if to_remove_hash_ids:
                logger.debug(f"to_remove_hash_ids: {to_remove_hash_ids}")
                await self._remove_metadata_by_hash_id(to_remove_hash_ids)

    async def _remove_metadata_by_hash_id(self, hash_ids: [str]):
        to_remove = [member for member in await self._sget_all(self.RedisMap.metaData) if
                     pickle.loads(member).get('hash_id') in hash_ids]
        if to_remove:
            await self._srem(self.RedisMap.metaData, *to_remove)

    async def _add_metadata(self, metadata_wrapper: MetaDataWrapper):
        async with self._global_lock:
            await self._sadd(self.RedisMap.metaData, pickle.dumps(asdict(metadata_wrapper)))

    async def _gen_metadata(self, proxy=None) -> MetaDataWrapper:
        if not proxy:
            proxy = {'proxy': {'http': self.my_proxy_addr, 'https': self.my_proxy_addr}}
        while 1:
            brand = random.choice(self.brand_list)
            Dalvik = random.choice(self.Dalvik_list)
            while not is_useable_Dalvik(Dalvik):
                Dalvik = random.choice(self.Dalvik_list)
            version_name_build: LatestVersionBuild = random.choice(self.version_name_build_list)
            version_name = version_name_build.version
            build = version_name_build.build
            channel = random.choice(self.channel_list)
            md: tuple = await make_metadata("",
                                            brand=brand,
                                            Dalvik=Dalvik,
                                            version_name=version_name,
                                            build=build,
                                            channel=channel,
                                            proxy=proxy
                                            )
            if not dict(md).get('x-bili-ticket'):
                logger.error(f'bili-ticket获取失败！{md}')
                await asyncio.sleep(30)
                continue
            else:
                break
        metadata_wrapper = MetaDataWrapper(
            md=md,
            expire_ts=int(time.time() + 0.5 * 3600),
            version_name=version_name
        )
        await self._add_metadata(metadata_wrapper)
        return metadata_wrapper

    async def get_rand_metadata(self) -> MetaDataWrapper:
        while 1:
            if await self._scount(self.RedisMap.metaData) < 50:
                metadata_wrapper = await self._gen_metadata()
                break
            else:
                metadata_pickle = await self._sget_rand(self.RedisMap.metaData)
                if not metadata_pickle:  # 如果获取不到，则重新获取
                    metadata_wrapper = await self._gen_metadata()
                    break
                metadata_wrapper = MetaDataWrapper(**pickle.loads(metadata_pickle))
                if metadata_wrapper.expire_ts < time.time():
                    await self._remove_metadata_by_hash_id(metadata_wrapper.hash_id)
                    continue
                if metadata_wrapper.times_352:
                    await asyncio.sleep(10)
                    continue
                break
        return metadata_wrapper
