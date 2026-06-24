"""B站动态详情解析结果的 pydantic 模型

替代原先 `__solve_dynamic_item_detail` 返回的 dict 结构，避免字段混乱。
"""
from typing import Any

from pydantic import ConfigDict

from Models.base.custom_pydantic import CustomBaseModel


class DynamicDetailParsed(CustomBaseModel):
    """B站动态详情解析结果

    封装 `BiliDynamicItem.__solve_dynamic_item_detail` 的返回内容，
    替代原先的 dict 结构，便于类型检查与字段访问。
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # 原始 item 数据（B站动态详情接口 data.item 的完整内容）
    rawJSON: dict | None = None
    # 动态 id（id_str）
    dynamic_id: str | None = None
    # 原始 item 引用（与 rawJSON 相同，保留以兼容旧逻辑）
    dynamic_item: dict | None = None
    # module_dynamic.desc（rich_text_nodes 等结构）
    desc: dict | None = None
    # 动态类型: '8' 视频 / '4' 转发 / '2' 图片 / '64' 文章
    type: str | None = None
    # 评论区 rid（comment_id_str）
    rid: str | None = None
    # 是否关注了作者: 1 已关注 / 0 未关注
    relation: int | None = None
    # 是否点赞（保留字段，目前固定为 0）
    is_liked: int | None = None
    # 作者 uid
    author_uid: int | None = None
    # 作者昵称
    author_name: str | None = None
    # 评论数
    comment_count: int | None = None
    # 转发数
    forward_count: int | None = None
    # 点赞数
    like_count: int | None = None
    # 动态正文内容（desc.text + major 中的文本拼接）
    dynamic_content: str | None = None
    # 发布时间字符串（如 '2026年06月17日 21:18'）
    pub_time: str | None = None
    # 发布时间戳（秒）
    pub_ts: int | None = None
    # 官方认证类型: -1 无认证 / 0 个人 / 1 机构
    official_verify_type: int | None = None
    # module_dynamic 完整 dict（用于判断官方/充电/预约抽奖）
    module_dynamic: dict | None = None
    # 动态卡片类型（如 DYNAMIC_TYPE_DRAW / DYNAMIC_TYPE_FORWARD）
    card_stype: str | None = None
    # 是否是置顶动态: True / False / None（未知）
    top_dynamic: bool | None = None

    # ---- 转发动态的原动态信息（非转发动态时均为 None）----
    # 原动态 id
    orig_dynamic_id: str | None = None
    # 原动态原始 item（dynamic_item.orig）
    dynamic_orig: dict | None = None
    # 原动态作者 uid
    orig_mid: int | None = None
    # 原动态作者昵称
    orig_name: str | None = None
    # 原动态发布时间戳（秒）
    orig_pub_ts: int | None = None
    # 原动态官方认证类型
    orig_official_verify: int | None = None
    # 原动态评论数（目前未提取，保留为 None）
    orig_comment_count: int | None = None
    # 原动态转发数（目前未提取，保留为 None）
    orig_forward_count: int | None = None
    # 原动态点赞数（目前未提取，保留为 None）
    orig_like_count: int | None = None
    # 原动态正文内容
    orig_dynamic_content: str | None = None
    # 原动态关注关系: 1 已关注 / 0 未关注
    orig_relation: int | None = None
    # 原动态 desc 结构
    orig_desc: dict | None = None

    def is_valid(self) -> bool:
        """是否是有效的解析结果（动态存在且解析成功）"""
        return bool(self.dynamic_id)
