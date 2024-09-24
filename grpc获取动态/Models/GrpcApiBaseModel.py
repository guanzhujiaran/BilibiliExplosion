import secrets
import time
from dataclasses import dataclass, asdict

_352_cd = 5 * 60
_max_used_times_one_round = 20


@dataclass
class MetaDataWrapper:
    md: tuple
    expire_ts: int
    version_name: str
    times_352: int = 0
    hash_id: str = secrets.token_hex(16)
    used_times: int = 0  # 使用次数
    lastest_used_ts: int = int(time.time())

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
        if self.expire_ts >= int(
                time.time()) and not self.is_need_delete and self.used_times < _max_used_times_one_round:
            return True
        else:
            return False

    @property
    def is_need_delete(self) -> bool:
        """
        是否需要删除
        :return:
        """
        if self.expire_ts < time.time() or self.times_352 >= 3:
            return True
        else:
            return False


if __name__ == '__main__':
    a = MetaDataWrapper(md=(), expire_ts=0, version_name='1.0.0')
    print(asdict(a))
