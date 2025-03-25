from dataclasses import dataclass, field
from typing import Set
from fastapi接口.service.get_others_lot_dyn.Sql.models import TLotdyninfo

@dataclass
class RobotScrapyInfo:
    """
    保存机器人爬取的信息
    """
    all_lot_dyn_info_set: Set[TLotdyninfo] = field(default_factory=set) # 所有的一轮获取到的抽奖动态
    all_useless_info_set: Set[TLotdyninfo] = field(default_factory=set) # 所有的一轮获取到的非抽奖动态
