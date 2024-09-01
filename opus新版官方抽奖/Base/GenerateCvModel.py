from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field
# windows中如果出现编码错误. 在引入execjs之前. 插入以下代码即可.
import os

os.environ['EXECJS_RUNTIME'] = 'Node'
import subprocess
from functools import partial

subprocess.Popen = partial(subprocess.Popen, encoding='utf-8')

import execjs


class LotType(Enum):
    activity_lottery = "h5转盘抽奖"
    activity_match_lottery = "赛事抽奖"
    activity_match_task = "赛事抽奖任务"
    era_jika = "集卡活动"
    era_lottery = "轮播抽奖"
    era_task = "轮播抽奖任务"
    era_video = "投稿瓜分"
    unknown = "未知活动"


class CvItem(BaseModel):
    jumpUrl: str
    title: str
    lot_type_list: Optional[List[LotType]] = []
    end_date_str: str
    lottery_pool: Optional[List[str]] = []


class OpusType(Enum):
    ALBUM = 1
    ARTICLE = 2
    ARTICLE_H5 = 5
    DEFAULT_SOURCE = 0
    MANGA_EP = 8
    NOTE = 3
    OGV_COMMENT = 4
    REPOST = 7
    WORD = 6


class Color(Enum):
    color_blue_01 = "#56c1fe"
    color_lblue_01 = "#73fdea"
    color_green_01 = "#89fa4e"
    color_yellow_01 = "#fff359"
    color_pink_01 = "#ff968d"
    color_purple_01 = "#ff8cc6"
    color_blue_02 = "#02a2ff"
    color_lblue_02 = "#18e7cf"
    color_green_02 = "#60d837"
    color_yellow_02 = "#fbe231"
    color_pink_02 = "#ff654e"
    color_blue_03 = "#0176ba"
    color_lblue_03 = "#068f86"
    color_green_03 = "#1db100"
    color_yellow_03 = "#f8ba00"
    color_pink_03 = "#ee230d"
    color_purple_03 = "#cb297a"
    color_blue_04 = "#004e80"
    color_lblue_04 = "#017c76"
    color_green_04 = "#017001"
    color_yellow_04 = "#ff9201"
    color_pink_04 = "#b41700"
    color_purple_04 = "#99195e"
    color_gray_01 = "#d6d5d5"
    color_gray_02 = "#929292"
    color_gray_03 = "#5f5f5f"


class CutOff(Enum):
    cut_off_5 = {"cut-off": {
        "type": "5",
        "url": "https://i0.hdslb.com/bfs/article/02db465212d3c374a43c60fa2625cc1caeaab796.png"
    }}


class CvContentAttr(BaseModel):
    link: Optional[str] = Field(None, description="站内链接属性")
    color: Optional[Color] = Field(None, description="颜色属性")
    class_: Optional[str] = Field(None, description="截断属性", alias="class")
    list: Optional[str] = Field(None, description="列表属性")


class CvContentOps(BaseModel):
    attributes: Optional[CvContentAttr] = Field(None, description="插入文字属性")
    insert: Union[str, CutOff]


with open(os.path.join(__file__, '../read_editor.js'), 'r', encoding='utf-8') as f:
    toOpusContent = execjs.compile(
        f.read()
    )


class CvContent(BaseModel):
    ops: List[CvContentOps]

    @property
    def rawContent(self):
        return self.model_dump_json(exclude_unset=True, by_alias=True)

    def toOpusContent(self, _type: OpusType):
        return toOpusContent.call('toOpusContent', _type.value, self.rawContent)


if __name__ == "__main__":
    b = [{"attributes": {"color": "#99195e"}, "insert": "2024-09-25 23:59截止 "},
         {"attributes": {"link": "https://www.bilibili.com/blackboard/activity-7tuZ5wP6aM.html"},
          "insert": "幻塔UP主激励计划 "},
         {"attributes": {"color": "#99195e"}, "insert": "赛事抽奖|赛事抽奖任务 "},
         {"attributes": {"list": "ordered"}, "insert": "\n"},
         {"attributes": {"color": "#0176ba"}, "insert": "2024-09-08 00:00截止 "}]
    _a = CvContent(ops=b)
    c = _a.toOpusContent(OpusType.ARTICLE)
    print(c)
