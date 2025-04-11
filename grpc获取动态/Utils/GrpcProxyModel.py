import time
from dataclasses import dataclass
import ast

_max_use_count_before_352 = 20
_352_cd = 15 * 60
_412_cd = 24 * 3600


@dataclass
class GrpcProxyStatus:
    ip: str  # ip地址 如”https://127.0.0.1:114514“
    counter: int  # 使用次数
    max_counter_ts: int = 0  # 达到最大的时间戳
    code: int = 0  # 返回响应的代码。0或者-352或者-412
    available: bool = False  # 是否能够连接同的代理，不管412还是352，只要能用就是True，不能用就是False，删除代理都是删掉那些无法连接的
    latest_352_ts: int = 0
    latest_used_ts: int = 0

    @property
    def is_usable(self):
        """
        是否可以使用，使用次数没到
        :return:
        """
        if not self.available:
            return False
        if self.code != 0:
            if self.code == -352:
                if self.latest_352_ts + _352_cd > time.time():
                    return True
                else:
                    return False
            if self.code == -412:
                if self.latest_used_ts + _412_cd > time.time():
                    return True
                else:
                    return False
            return False
        if self.counter >= _max_use_count_before_352:
            return False
        return True

    def to_redis_data(self):
        return {
            "ip": self.ip,
            "counter": self.counter,
            "max_counter_ts": self.max_counter_ts,
            "code": self.code,
            "available": str(self.available),
            "latest_352_ts": self.latest_352_ts,
            "latest_used_ts": self.latest_used_ts
        }

    def parse_form_redis_data(self, data: dict):
        self.ip = data["ip"]
        self.counter = ast.literal_eval(data["counter"])
        self.max_counter_ts = ast.literal_eval(data["max_counter_ts"])
        self.code = ast.literal_eval(data["code"])
        self.available = ast.literal_eval(data["available"])
        self.latest_352_ts = ast.literal_eval(data["latest_352_ts"])
        self.latest_used_ts = ast.literal_eval(data["latest_used_ts"])

    def to_dict(self):
        return {
            "ip": self.ip,
            "counter": self.counter,
            "max_counter_ts": self.max_counter_ts,
            "code": self.code,
            "available": self.available,
            "latest_352_ts": self.latest_352_ts,
            "latest_used_ts": self.latest_used_ts
        }

    def is_usable_before_use(self, add_counter_flag: bool = False):
        """
        根据使用次数判断是否能够使用
        :param add_counter_flag:
        :return:
        """
        if self.max_counter_ts and int(time.time()) - self.max_counter_ts >= 3600:  # 如果一小时以上就重置为0
            self.counter = 1
            self.code = 0
            self.max_counter_ts = int(time.time())
            self.latest_used_ts = 0
            self.latest_352_ts = 0
            return True
        if add_counter_flag:
            self.latest_used_ts = int(time.time())
            self.counter += 1
        return self.is_usable
