import secrets
import time
from dataclasses import dataclass, asdict, field

_352_cd = 30 * 60
_max_used_times_one_round = 6


@dataclass
class MetaDataWrapper:
    md: tuple  # header
    buvid: str
    expire_ts: int  # 秒级时间戳
    version_name: str  # 8.15.0
    session_id: str  # 会话id，需要保持不变
    guestid: str | int
    times_352: int = 0
    hash_id: str = field(default_factory=lambda: secrets.token_hex(16))
    used_times: int = 0  # 使用次数
    lastest_used_ts: int = field(default_factory=lambda: int(time.time()))

    def able(self, num_add=True) -> bool:
        """
        是否可用
        :return:
        """
        if int(time.time()) - self.lastest_used_ts > _352_cd:
            self.used_times = 0
        if num_add:
            self.used_times += 1
            self.lastest_used_ts = int(time.time())
        if (self.expire_ts >= int(time.time())
                and not self.is_need_delete
                and self.used_times < _max_used_times_one_round
        ):
            return True
        else:
            return False

    @property
    def is_need_delete(self) -> bool:
        """
        是否需要删除
        :return:
        """
        if self.expire_ts < int(time.time()) or self.times_352 >= 3 or self.used_times >= _max_used_times_one_round:
            return True
        else:
            return False


@dataclass
class MetaDataBasicInfo:
    buvid: str
    fp_local: str
    fp_remote: str
    guestid: str | int
    app_version_name: str
    model: str
    app_build: str | int
    channel: str
    osver: str
    ticket: str
    brand: str
    session_id: str = ''


if __name__ == '__main__':
    a = MetaDataWrapper(md=(), expire_ts=0, version_name='1.0.0')
    print(asdict(a))
