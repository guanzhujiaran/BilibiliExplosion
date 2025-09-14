import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from pydantic import Field, PrivateAttr, computed_field

from Models.base.custom_pydantic import CustomBaseModelHashable
from Service.GetOthersLotDyn.Sql.models import TLotdyninfo


@dataclass
class RobotScrapyInfo:
    """
    保存机器人爬取的信息
    """
    all_lot_dyn_info_list: List[TLotdyninfo] = field(default_factory=list)  # 所有的一轮获取到的抽奖动态
    all_useless_info_list: List[TLotdyninfo] = field(default_factory=list)  # 所有的一轮获取到的非抽奖动态


class BiliSpaceUserParamsType(CustomBaseModelHashable):
    _update_ts: int = PrivateAttr(default_factory=lambda: int(time.time()))
    uid: int = Field(..., description="用户uid")
    _offset: int = PrivateAttr(default=0)

    @computed_field
    @property
    def offset(self) -> int:
        return self._offset

    @offset.setter
    def offset(self, value):
        self._offset = value
        self._update_ts = int(time.time())

    @computed_field
    @property
    def update_time(self) -> datetime:
        return datetime.fromtimestamp(self._update_ts)

    def __hash__(self):
        return hash(self.uid)


if __name__ == '__main__':
    params = BiliSpaceUserParamsType(uid=1)
    params.offset = 1
    print(params.model_dump_json(exclude_none=True,exclude_defaults=True,exclude_unset=True))
    params.offset = 2
    print(params.model_dump_json(exclude_none=True,exclude_defaults=True,exclude_unset=True))
    params.offset = 3
    print(params.model_dump_json(exclude_none=True,exclude_defaults=True))
    params.offset = 4
    print(params.model_dump_json(exclude_none=True,exclude_defaults=True))
    params.offset = 5
    print(params.model_dump_json(exclude_none=True,exclude_defaults=True))
