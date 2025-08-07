# -*- coding: utf-8 -*-


class dynAllDetail:
    """
    写入动态数据库里面的数据
    """
    rid: str
    dynamic_id: str
    dynData: dict
    lot_id: str
    dynamic_created_time: str
    dynamic_id_int :int

    def __init__(self, rid: str = '', dynamic_id: str = '', dynData=None, lot_id=None, dynamic_created_time='',*args,**kwargs):
        self.rid = rid
        self.dynamic_id = dynamic_id
        self.dynData = dynData
        self.lot_id = lot_id
        self.dynamic_created_time = dynamic_created_time
        self.dynamic_id_int = int(dynamic_id)

class lotDetail:
    """
    官方抽奖的notice关键信息
    """
    business_id: str
    status: int
    lottery_time: int
    lottery_at_num: int
    lottery_feed_limit: int
    first_prize: int
    second_prize: int
    third_prize: int
    first_prize_cmt: str
    second_prize_cmt: str
    third_prize_cmt: str
    first_prize_pic: str
    second_prize_pic: str
    third_prize_pic: str
    need_post: int
    business_type: int
    sender_uid: int
    pay_status: int
    ts: int
    lottery_id: int
    has_charge_right: int
    participated: int
    participants: int
    _gt_: int

    def __init__(self, d: dict):
        self.__dict__.update(d)


class lotDynData:
    """
    普通动态抽奖信息
    """
    dyn_url: str = '' # 动态链接
    author_name: str = '' # 发布者昵称
    author_space: str = '' # 发布者空间链接
    official_verify_type: str = '' # 发布者的账号类型
    pub_time: str = ''
    dynamic_content: str = ''
    comment_count: str = ''
    forward_count: str = ''
    like_count: str = ''
    Manual_judge: bool = False
    high_lights_list: list = []
    lot_type: str = ''
    lot_rid: str = ''
    premsg: str = ''

    def __init__(self, d=None):
        if d is None:
            d = {}
        self.__dict__.update(d)
