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
    lottery_pool: Optional[List[str]] = [] # 奖池内容（奖品列表）
    lottery_sid:Optional[str] = '' # 抽奖的sid信息

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
    def rawContent(self) -> str:
        return self.model_dump_json(exclude_unset=True, by_alias=True)

    @property
    def manualSubmitContent(self) -> str:
        content_ls = []
        for x in self.ops:
            if x.insert and type(x.insert) is str:
                content_ls.append(x.insert)
            if x.attributes and x.attributes.link:
                content_ls.append(x.attributes.link)
            if x.insert == CutOff.cut_off_5.value:
                content_ls.append('\n\n\n')
                continue
        return ''.join(content_ls)

    def toOpusContent(self, _type: OpusType):
        return toOpusContent.call('toOpusContent', _type.value, self.rawContent)


if __name__ == "__main__":
    b = {"ops":[{"attributes":{"color":"#99195e"},"insert":"2024-12-09 00:00截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/activity-6Mk5LYyPC0.html"},"insert":"舞蹈热点情报站5.0 "},{"attributes":{"color":"#99195e"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#004e80"},"insert":"2024-11-20 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/activity-7g1eXvxUk1.html"},"insert":"鬼畜星探企划 "},{"attributes":{"color":"#004e80"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#73fdea"},"insert":"2025-12-31 18:00截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/activity-ParItHBk5u.html?id=662b7008962d49513fe415ab"},"insert":"猩球崛起十级影迷考试 "},{"attributes":{"color":"#73fdea"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#fff359"},"insert":"2025-12-31 00:00截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/activity-ParItHBk5u.html?id=661e4650c90acd8cff0bb459"},"insert":"美羊羊十级考试 "},{"attributes":{"color":"#fff359"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#fff359"},"insert":"2025-12-31 00:00截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/activity-ParItHBk5u.html?id=661e4dc4a606156e637a0901"},"insert":"伊之助十级考试 "},{"attributes":{"color":"#fff359"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#18e7cf"},"insert":"2025-12-31 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/activity-ParItHBk5u.html?id=66067450eb3c6a5b77907d1d"},"insert":"五月天十级考试来了！ "},{"attributes":{"color":"#18e7cf"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#ff8cc6"},"insert":"2025-12-31 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/activity-ParItHBk5u.html?id=6606424ceb3c6a5b77907d02"},"insert":"宫崎骏十级学者考试来了！ "},{"attributes":{"color":"#ff8cc6"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#b41700"},"insert":"2025-12-31 00:00截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/activity-ParItHBk5u.html?id=6603d33bef6ffaa2f54a138b"},"insert":"小樱十级考试 "},{"attributes":{"color":"#b41700"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#89fa4e"},"insert":"2025-12-31 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/activity-ParItHBk5u.html?id=65fd08d8eb3c6a5b77907b11"},"insert":"绫波丽十级考试 "},{"attributes":{"color":"#89fa4e"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#89fa4e"},"insert":"2024-12-31 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/activity-ParItHBk5u.html?id=65f287fb8ad2f496794bd9f9"},"insert":"LPL春季赛答题挑战 "},{"attributes":{"color":"#89fa4e"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"class":"cut-off"},"insert":{"cut-off":{"type":"5","url":"https://i0.hdslb.com/bfs/article/02db465212d3c374a43c60fa2625cc1caeaab796.png"}}},{"attributes":{"class":"cut-off"},"insert":{"cut-off":{"type":"5","url":"https://i0.hdslb.com/bfs/article/02db465212d3c374a43c60fa2625cc1caeaab796.png"}}},{"attributes":{"color":"#02a2ff"},"insert":"2024-10-21 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/jub6HGUXPKr0nmW1.html"},"insert":"全能追星企划6.0 "},{"attributes":{"color":"#02a2ff"},"insert":"投稿瓜分|投稿瓜分|投稿瓜分|投稿瓜分 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#004e80"},"insert":"2024-10-21 00:00截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/0QJxtXd5i2eKw1Zu.html"},"insert":"哔哩谷研所2.0 "},{"attributes":{"color":"#004e80"},"insert":"轮播抽奖|轮播抽奖任务|投稿瓜分 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#5f5f5f"},"insert":"2024-12-31 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/zhenguolipc.html"},"insert":"人人都是时尚玩家 "},{"attributes":{"color":"#5f5f5f"},"insert":"投稿瓜分|投稿瓜分 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#ee230d"},"insert":"2024-11-01 00:00截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/VyleZRKvH9ZImtKm.html"},"insert":"一起来看live "},{"attributes":{"color":"#ee230d"},"insert":"轮播抽奖|轮播抽奖任务 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#5f5f5f"},"insert":"2025-01-01 00:00截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/eF8XNFxGMLrgPpW4.html?auto_media_playback=1"},"insert":"一键查看哥伦比亚百年高光！ "},{"attributes":{"color":"#5f5f5f"},"insert":"轮播抽奖 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#0176ba"},"insert":"2024-10-12 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/NNDk9on1thKcL9Tw.html"},"insert":"吞海广播剧音乐创作激励计划 "},{"attributes":{"color":"#0176ba"},"insert":"投稿瓜分 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#cb297a"},"insert":"2024-11-30 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/cHBPYYUgdGp8pfHN.html"},"insert":"歌手UP计划 "},{"attributes":{"color":"#cb297a"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#56c1fe"},"insert":"2024-10-28 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/wLiNpgB0OggtDNrq.html"},"insert":"金秋减脂小队 "},{"attributes":{"color":"#56c1fe"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#73fdea"},"insert":"2024-12-19 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/ne316EYCMzU7osfx.html"},"insert":"2024干杯音乐节 "},{"attributes":{"color":"#73fdea"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#89fa4e"},"insert":"2024-11-12 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/LMhYyPe2WNQEYyb8.html"},"insert":"我家有个小森林 "},{"attributes":{"color":"#89fa4e"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#ff654e"},"insert":"2024-10-31 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/SEEi8ac1oLu6EI4s.html"},"insert":"轻舞蹈竖屏激励计划 "},{"attributes":{"color":"#ff654e"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#004e80"},"insert":"2024-10-18 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/TcIS7luLPJuTnOzf.html"},"insert":"永劫无间手游UP主播激励计划 "},{"attributes":{"color":"#004e80"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#f8ba00"},"insert":"2024-11-06 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/CUsnbj9DUtg9qe9p.html"},"insert":"一起过秋天 "},{"attributes":{"color":"#f8ba00"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#b41700"},"insert":"2024-11-03 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/kzrLABB0P45z7A9C.html"},"insert":"粉丝饭拍大赛3.0 "},{"attributes":{"color":"#b41700"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#0176ba"},"insert":"2024-10-25 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/f4w1V56VrYt6QxS7.html"},"insert":"收藏这个秋天 "},{"attributes":{"color":"#0176ba"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#0176ba"},"insert":"2024-10-16 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/dwmeizhuangpc.html"},"insert":"持妆有方 有offer没班味 "},{"attributes":{"color":"#0176ba"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#004e80"},"insert":"2024-11-02 00:00截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/Appleevents2024PC.html"},"insert":"2024苹果秋季发布会 "},{"attributes":{"color":"#004e80"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#ee230d"},"insert":"2024-10-31 18:00截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/R06Um553T7zPZQMn.html"},"insert":"资讯直通车4.0 "},{"attributes":{"color":"#ee230d"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#18e7cf"},"insert":"2024-10-21 00:00截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/QDfwUqAkeijoKvVk.html"},"insert":"翻唱总动员 "},{"attributes":{"color":"#18e7cf"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#60d837"},"insert":"2024-12-31 23:00截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/wFhel6qofOdqD3rv.html"},"insert":"up大明星3.0 "},{"attributes":{"color":"#60d837"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#b41700"},"insert":"2024-10-31 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/leP8CFpAFORiOBMM.html"},"insert":"B站秋招季 "},{"attributes":{"color":"#b41700"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#ff9201"},"insert":"2024-11-27 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/GE7WLRRsaFda2RNK.html"},"insert":"新世代音乐人计划·原创季 "},{"attributes":{"color":"#ff9201"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#b41700"},"insert":"2025-01-11 00:00截止 "},{"attributes":{"link":"https://www.bilibili.com/blackboard/era/5U8ttg4BpRj28fj6.html"},"insert":"征稿活动任务开始 "},{"attributes":{"color":"#b41700"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"class":"cut-off"},"insert":{"cut-off":{"type":"5","url":"https://i0.hdslb.com/bfs/article/02db465212d3c374a43c60fa2625cc1caeaab796.png"}}},{"attributes":{"color":"#ff8cc6"},"insert":"2025-09-10 00:00截止 "},{"attributes":{"link":"https://www.bilibili.com/h5/mall/digital-card/home?-Abrowser=live&act_id=103677&hybrid_set_header=2&lottery_id=103679&f_source=plat&from=PC"},"insert":"拜仁慕尼黑-征途再起 "},{"attributes":{"color":"#ff8cc6"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#ff8cc6"},"insert":"2025-08-21 23:59截止 "},{"attributes":{"link":"https://www.bilibili.com/h5/mall/digital-card/home?-Abrowser=live&act_id=178&hybrid_set_header=2&lottery_id=320&f_source=plat&from=PC&f_source=plant&from=topic"},"insert":"红蓝巴萨收藏集 "},{"attributes":{"color":"#ff8cc6"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#99195e"},"insert":"2025-08-18 00:00截止 "},{"attributes":{"link":"https://www.bilibili.com/h5/mall/digital-card/home?-Abrowser=live&act_id=101529&hybrid_set_header=2&lottery_id=103414?f_source=plat&from=ad.share_dynamic"},"insert":"蓝月曼城收藏集 "},{"attributes":{"color":"#99195e"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"color":"#60d837"},"insert":"2030-09-30 00:00截止 "},{"attributes":{"link":"https://www.bilibili.com/v/topic/detail?topic_id=57316"},"insert":"以闪亮之名星赏派对 "},{"attributes":{"color":"#60d837"},"insert":"未知活动 "},{"attributes":{"list":"ordered"},"insert":"\n"},{"attributes":{"class":"cut-off"},"insert":{"cut-off":{"type":"5","url":"https://i0.hdslb.com/bfs/article/02db465212d3c374a43c60fa2625cc1caeaab796.png"}}},{"insert":"\n"}]}
    _a = CvContent(ops=b.get('ops'))
    # c = _a.toOpusContent(OpusType.ARTICLE)
    # print(c)

    print(_a.manualSubmitContent)
