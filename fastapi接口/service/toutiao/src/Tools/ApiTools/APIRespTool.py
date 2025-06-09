# encoding=utf-8
import json
from dataclasses import dataclass, field
from typing import Any, Union
from enum import Enum

from loguru import logger


class CellType(Enum):
    视频 = 0
    微头条 = 32
    评论转发详情 = 56
    文章 = 60


@dataclass
class User:
    id: int
    name: str
    user_id: str
    user_verified: int
    verified_content: str

    def jumpUrl(self):
        return f"https://www.toutiao.com/c/user/token/{self.user_id}/"


@dataclass
class CommentBase:
    content: str
    create_time: int
    group_id: int

    def jumpUrl(self) -> str:
        return f'https://www.toutiao.com/w/{self.group_id}/'


@dataclass
class OriginThread:
    attach_card_info: Any
    brand_info: str
    content: str
    cell_type: int
    create_time: int
    thread_id: int
    thread_id_str: str
    title: str
    publish_time: int
    user: User

    def jumpUrl(self) -> str:
        return f'https://www.toutiao.com/w/{self.thread_id}/'


@dataclass
class FeedData:
    publish_time: int  # 发布时间
    behot_time: int  # 刷新时间？
    cell_type: int  # 文章的类型
    comment_count: int  # 评论数量
    data_type: int  # 数据类型？
    id: int  # 头条id
    id_str: str
    content: str  # 头条内容
    abstract: str  # 当cell_type是60时出现
    origin_thread: Union[OriginThread, None]  # 当cell_type是评论转发详情 56时出现
    comment_base: Union[CommentBase, None]  # 当cell_type是评论转发详情 56时出现
    title: str

    def jumpUrl(self) -> str:
        return f'https://www.toutiao.com/w/{self.id}/'


@dataclass
class FeedListApiResp:
    data: list[FeedData]
    has_more: bool
    message: str
    max_behot_time: int
    offset: int


class FeedListApi:
    RespJsonStr: str
    UsefulInfo: FeedListApiResp
    RespDict: dict = field(default_factory=dict)

    def __init__(self, RespJsonStr):
        self.RespJsonStr = RespJsonStr
        self.RespDict = json.loads(self.RespJsonStr, strict=False)
        self.UsefulInfo = self.resolve()

    def resolve(self) -> FeedListApiResp:
        has_more = self.RespDict.get('has_more', False)
        message = self.RespDict.get('message')
        max_behot_time = self.RespDict.get('next').get('max_behot_time')
        offset = self.RespDict.get('offset')
        data = list()
        for da in self.RespDict.get('data'):
            try:
                publish_time: int = da.get('publish_time')
                behot_time: int = da.get('behot_time')  # 刷新时间？
                cell_type: int = da.get('cell_type')  # 文章的类型
                comment_count: int = da.get('comment_count')  # 评论数量
                data_type: int = da.get('data_type')  # 数据类型？
                origin_thread: Union[OriginThread, None] = None
                comment_base: Union[CommentBase, None] = None
                title: str = da.get('data_type')
                content: str = ''
                abstract: str = ''
                _id: int = 0
                id_str: str = ''
                if cell_type == CellType.视频.value:
                    _id = int(da.get('id'))
                    id_str = da.get('id')
                elif cell_type == CellType.文章.value:
                    abstract = da.get('abstract')
                    _id = int(da.get('id'))
                    id_str = da.get('id')
                elif cell_type == CellType.评论转发详情.value:
                    _id = da.get('id')
                    id_str = da.get('id_str')
                    CommentBaseDict = da.get('comment_base')
                    CommentBasecontent: str = CommentBaseDict.get('content')
                    create_time: int = CommentBaseDict.get('create_time')
                    publish_time: int = create_time
                    group_id: int = CommentBaseDict.get('group_id')
                    comment_base = CommentBase(content=CommentBasecontent, create_time=create_time, group_id=group_id)
                    if OriginThreadDict := da.get('origin_thread'):
                        attach_card_info = OriginThreadDict.get('attach_card_info')
                        brand_info = OriginThreadDict.get('brand_info')
                        OriginThread_cell_type = OriginThreadDict.get('cell_type')
                        OriginThread_content = OriginThreadDict.get('content')
                        OriginThread_create_time = OriginThreadDict.get('create_time')
                        OriginThread_thread_id = OriginThreadDict.get('thread_id')
                        OriginThread_thread_id_str = OriginThreadDict.get('thread_id_str')
                        OriginThread_title = OriginThreadDict.get('title')
                        OriginThread_publish_time = OriginThreadDict.get('publish_time')
                        UserDict = OriginThreadDict.get('user')

                        User_id = UserDict.get('id')
                        User_name = UserDict.get('name')
                        User_user_id = UserDict.get('user_id')
                        User_user_verified = UserDict.get('user_verified')
                        User_verified_content = UserDict.get('verified_content')
                        user = User(
                            id=User_id,
                            name=User_name,
                            user_id=User_user_id,
                            user_verified=User_user_verified,
                            verified_content=User_verified_content
                        )
                        origin_thread = OriginThread(
                            attach_card_info=attach_card_info,
                            brand_info=brand_info,
                            cell_type=OriginThread_cell_type,
                            content=OriginThread_content,
                            create_time=OriginThread_create_time,
                            thread_id=OriginThread_thread_id,
                            thread_id_str=OriginThread_thread_id_str,
                            title=OriginThread_title,
                            publish_time=OriginThread_publish_time,
                            user=user
                        )
                elif cell_type == CellType.微头条.value:
                    content = da.get('content')
                    _id = da.get('thread_id')
                    id_str = da.get('thread_id_str')
                else:
                    logger.error(f'未知cell_type类型！cell_type:{cell_type}\n{da}')
                feedData = FeedData(
                    publish_time=publish_time,
                    behot_time=behot_time,
                    comment_count=comment_count,
                    data_type=data_type,
                    origin_thread=origin_thread,
                    comment_base=comment_base,
                    title=title,
                    abstract=abstract,
                    cell_type=cell_type,
                    id=_id,
                    id_str=id_str,
                    content=content
                )
                data.append(feedData)
            except Exception as e:
                logger.error(f'解析单个空间数据失败！\n{da}\n{e}')
        feedListApiResp = FeedListApiResp(
            has_more=has_more,
            message=message,
            max_behot_time=max_behot_time,
            offset=offset,
            data=data
        )
        return feedListApiResp


