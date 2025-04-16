import math
import time

class BaseStopCounter:
    _stop_flag: bool = False
    _max_stop_continuous_num: int = 30  # 短时间内超过30个动态都满足条件，则将stop_flag设置为True
    cur_stop_continuous_num: int = 0

    def __init__(self, max_stop_continuous_num: int = 30):
        self._max_stop_continuous_num = max_stop_continuous_num

    @property
    def stop_flag(self) -> bool:
        if self.cur_stop_continuous_num >= self._max_stop_continuous_num:
            return True
        return False

    def set_max_stop_num(self):
        """
        直接设置达到最大连续次数
        即设置_stop_flag为True
        :return:
        """
        self.cur_stop_continuous_num = self._max_stop_continuous_num




class BaseSuccCounter:
    start_ts = int(time.time())
    _succ_count = 0
    update_ts:int=0
    is_running:bool = False

    @property
    def succ_count(self):
        return self._succ_count

    @succ_count.setter
    def succ_count(self, value):
        self._succ_count = value
        self.update_ts = int(time.time())

    def __init__(self):
        self.start_ts = int(time.time())
        self.succ_count = 0

    def show_pace(self) -> float:
        """
        获取一个动态需要花多少秒
        :return:
        """
        if self.is_running:
            target_ts = int(time.time())
        else:
            target_ts = self.update_ts
        spend_ts = target_ts - self.start_ts
        if self.succ_count > 0:
            pace_per_sec = spend_ts / self.succ_count
            return pace_per_sec
        else:
            return 0.0

    def show_text(self) -> str:
        pass



class ProgressCounter(BaseSuccCounter):
    _total_num: int = 0

    def __init__(self):
        super().__init__()

    @property
    def total_num(self):
        # 返回私有变量_total_num的值
        return self._total_num

    @total_num.setter
    def total_num(self, value: int):
        self.is_running = True
        self.succ_count = 0
        self._total_num = value

    def show_pace(self):
        return math.floor(self.succ_count / self.total_num * 100) / 100 if self.total_num else 0
