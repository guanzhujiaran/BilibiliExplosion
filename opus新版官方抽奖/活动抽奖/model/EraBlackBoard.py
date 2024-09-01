from pydantic import BaseModel, Extra
from typing import Optional, List


class EraTaskIndicator(BaseModel):
    cur_value: int
    limit: int
    name: Optional[str] = ''


class EraTaskCheckPoint(BaseModel):
    alias: str
    awardname: str
    awardsid: str
    awardtype: int
    count: int
    list: List[EraTaskIndicator]
    status: int
    ztasksid: str


class EraLotteryConfigGift(BaseModel):
    id: str
    name: str


class EraTask(BaseModel):
    """
    话题抽奖任务
    """
    accumulativeCount: int
    awardName: str
    btnBehavior: Optional[List[str]] = [""]
    btnTxt: Optional[str] = [""]
    can_edit: int
    checkpoints: List[EraTaskCheckPoint]
    counter: str
    indicators: List[EraTaskIndicator]
    jumpLink: Optional[str] = ""
    jumpPosition: Optional[str] = ""
    periodType: int
    promptText: str
    showBtn: Optional[bool] = False
    statisticType: int
    taskAwardType: int
    taskDes: Optional[str] = ""
    taskIcon: Optional[str] = ""
    taskId: str
    taskName: str
    taskStatus: int
    taskType: int
    topicID: Optional[str] = ""
    topicName: Optional[str] = ""


class EraLotteryConfig(BaseModel):
    """
    话题抽奖内容
    """
    activity_id: str
    gifts: List[EraLotteryConfigGift]
    icon: str
    lottery_id: str
    lottery_type: int
    per_time: int
    point_name: str


class EraVideoSourcePool(BaseModel):
    bonus: Optional[str] = ""
    label: str
    rule: Optional[str] = ""
    value: int


class EraVideoSourceCONFIG(BaseModel):
    """
    视频投稿播放量瓜分现金活动
    """
    poolList: List[EraVideoSourcePool]
    topic_id: int
    topic_name: str
    videoSource_id: str


# region h5抽奖类
class H5ActivityLotteryGiftSource(BaseModel):
    id: int
    img_url: str
    least_mark: int
    name: str
    type: int


class H5ActivityLottery(BaseModel):
    """
    activity的转盘抽奖
    """
    lotteryId: str
    continueTimes: List[int]
    list: List[H5ActivityLotteryGiftSource]


# endregion

class MatchLotteryTask(BaseModel):
    """
    赛事抽奖任务
    """

    class TaskImg(BaseModel):
        url: str
        height: int
        width: int

    btn_text: str
    interact_type: List[str]
    task_desc: str
    task_group_id: List[int]
    task_img: TaskImg
    task_max_count: int
    task_name: str
    task_step: List[str]
    url: Optional[str] = ""


class MatchLottery(BaseModel):
    lottery_id: str
    activity_id: str


class EvaContainerTruck(BaseModel):
    """
    集卡活动
    """
    activityUrl: str
    jikaId: str
    topId: int
    topName: str
