import asyncio
import random
import time
import uuid

from fastapi接口.log.base_log import sams_club_logger
from fastapi接口.models.v1.samsclub.samsclub_model import SamsClubHeadersModel, SamsClubEncryptModel, \
    SamsClubGetDoEncryptReqModel
from fastapi接口.service.samsclub.tools.do_samsclub_encryptor import get_st, get_do_encrypt_result_str
from fastapi接口.service.samsclub.tools.java_rand_gen import F65205aRandomIntGenerator
from fastapi接口.utils.Common import retry_wrapper


def sort_headers_with_missing_last(headers, desired_order: list[str] = None):
    if desired_order is None:
        desired_order = [
            'language', 'system-language', 'device-type', 'tpg', 'app-version',
            'device-id', 'device-os-version', 'device-name', 'treq-id', 'auth-token',
            'longitude', 'latitude', 'p', 't', 'n', 'sy', 'st', 'sny', 'rcs', 'spv',
            'Local-Longitude', 'Local-Latitude', 'zoneType', 'provinceCode', 'cityCode',
            'districtCode', 'amapProvinceCode', 'amapCityCode', 'amapDistrictCode',
            'Content-Type', 'Content-Length', 'Host', 'Connection', 'Accept-Encoding',
            'User-Agent'
        ]
    # 构造一个列表用于存储最终结果
    result = []
    # 构造一个集合用于记录已经处理过的 key
    used_keys = set()

    # 第一步：按 desired_order 添加存在的字段
    for key in desired_order:
        if key in headers:
            result.append((key, headers[key]))
            used_keys.add(key)
        else:
            # 如果希望对不存在的 header 添加默认值，可以在这里操作
            # 例如：result.append((key, ""))
            pass

    # 第二步：把不在 desired_order 中的字段加到末尾
    other_headers = [(k, v) for k, v in headers.items() if k not in used_keys]

    # 可选：打乱其他字段的顺序（模拟“随机排列”）
    random.shuffle(other_headers)  # 打乱顺序

    # 将剩余的 headers 加入到结果中
    result.extend(other_headers)

    # 返回结果作为 tuple
    return tuple(result)


class SamsClubHeadersGen:
    random_gen = F65205aRandomIntGenerator()
    treq_uuid = uuid.uuid4().hex.replace("-", "")
    device_os_version = "11"
    device_name = "OnePlus_ONEPLUS+A6000"
    device_str = "d3e9907ab1881aac891aff90100016e1950c"
    version_str = "5.0.122"
    longitude = 121.463874
    latitude = 31.258597
    auth_token = ""
    _counter = 100
    _lock = asyncio.Lock()

    def __init__(self,
                 auth_token,
                 treq_uuid=treq_uuid,
                 device_os_version=device_os_version,
                 device_name=device_name,
                 device_str=device_str,
                 version_str=version_str,
                 ):
        self.treq_uuid = treq_uuid
        self.device_os_version = device_os_version
        self.device_name = device_name
        self.auth_token = auth_token
        self.device_str = device_str
        self.version_str = version_str

    async def _get_counter(self):
        async with self._lock:
            ret = self._counter + 1
            self._counter = ret
            if ret > 999:
                self._counter = 100
            return self._counter

    @retry_wrapper
    async def gen_headers(
            self,
            body: str,
    ) -> SamsClubHeadersModel:
        cnt = await self._get_counter()
        ts = int(time.time() * 1000)  # 模拟Java的System.currentTimeMillis() 方法，返回当前时间的毫秒数
        ts_str = str(int(ts))
        treq_ts_10000 = int(ts * 10000) + self.random_gen.nextInt()
        treq_ts_10000_str = str(treq_ts_10000)
        fake_treq_id = f"{self.treq_uuid}.{cnt}.{treq_ts_10000_str}"  # 这里面的uuid是每次请求的时候固定下来，然后中间的是一个请求次数的计数，到999就重置为100，一个个往下面加
        fake_n = uuid.uuid4().hex.replace("-", "")
        st = get_st(
            SamsClubEncryptModel(
                device_id_str=self.device_str,
                version_str=self.version_str,
                device_name=self.device_name,
                do_encrypt_result_str=await get_do_encrypt_result_str(
                    SamsClubGetDoEncryptReqModel(
                        timestampStr=ts_str,
                        bodyStr=body,
                        uuidStr=fake_n,
                        tokenStr=self.auth_token
                    )
                ),
            )
        )
        if not st:
            raise Exception("st is None")
        sams_club_logger.debug(f"st: {st}")
        headers_dict = {
            "device-id": self.device_str,
            "device-os-version": self.device_os_version,
            "device-name": self.device_name,
            "auth-token": self.auth_token,
            "treq-id": fake_treq_id,
            "t": ts_str,
            "n": fake_n,
            "st": st,
            "app-version": self.version_str,
            'Local-Longitude': str(self.longitude),
            'Local-Latitude': str(self.latitude),
            'longitude': str(self.longitude),
            'latitude': str(self.latitude),
        }
        return SamsClubHeadersModel(
            **headers_dict
        )
