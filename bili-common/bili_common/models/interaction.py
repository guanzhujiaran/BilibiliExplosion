"""社区互动通用枚举（收藏 / 点赞等跨服务互动，供各业务系统统一读取）。"""

from typing import Self

from bili_common.models import IntEnumAutoDoc


class InteractionBizTypeEnum(IntEnumAutoDoc):
    """统一业务资源类型（be-message 统一管理收藏/点赞，按该类型区分资源归属）。

    本枚举是「业务资源类型」的唯一真相源（bili-common 收口），下列枚举直接复用本枚举
    的成员而非重新定义：bili-common 各服务的 bizType 列（事件来源类型同样直接复用本枚举成员）。

    **存储**：数据库以 int 存储（值 1~7），减小存储空间、利于索引；
    **对外契约**：API 层经 `from_text` / `to_text` 转换为可读文字
    （`dynamic` / `lottery` / ...），前端 / 跨服务 RPC 契约保持文字不变。
    """

    DYNAMIC = 1  # 动态（bizId = dynId）
    LOTTERY = 2  # 抽奖卡片（bizId = 抽奖卡片 id）
    RPA_ACTION = 3  # RPA 自定义操作（bizId = action_id）
    RPA_WORKFLOW = 4  # RPA 工作流（bizId = workflow_id）
    RPA_BROWSER = 5  # RPA 浏览器实例（bizId = browser_id）
    RPA_PLUGIN = 6  # RPA 插件（bizId = plugin_id）
    # 评论资源：评论本身是可被点赞（事件）/ 举报 / 作为事件来源的资源，
    # 与 dynamic / lottery 同属「业务资源」一类，故收口到本枚举而非另立来源枚举。
    COMMENT = 7  # 评论（bizId = rpid）
    # 用户空间资源：可被举报 / 作为事件来源（如被关注、被 @ 等用户维度事件）。
    USER = 8  # 用户（bizId = mid）
    # RPA 资源标签：共享池 + 审核（模板于 RPA_ACTION 等 RPA 内容，同纳入 be-message
    # 管理与审核栈；bizId = rpa_tag.id）。
    RPA_TAG = 14

    # ===== 审核统计域（`GET /audit/statistics?bizType=` 直接复用本枚举，计划书 §5.13）=====
    # 注意：9~13 为审核域单据 / 聚合口径，仅用于审核统计与审核队列归属，
    # **不作为互动资源 ID**（点赞 / 评论 / 收藏的 bizType 仍限 1~8 的实体资源）。
    TOPIC = 9  # 话题动态（审核域：TMomentTopic）
    DM = 10  # 私信（审核域：DmMessageIndex）
    AVATAR = 11  # 头像审核单（TUserAvatarAudit）
    FOLDER_COVER = 12  # 收藏夹封面审核单（TFolderCoverAudit）
    REPORT = 13  # 举报单聚合域（跨全部举报表的举报审核统计 / 管理列表）

    @classmethod
    def from_text(cls, text: "InteractionBizTypeEnum | str | int | None") -> Self:
        """把对外文字（dynamic/lottery/...）或数值转换为枚举成员（统一入口）。

        - 已是枚举成员：原样返回；
        - 数字 / 数字字符串：按值构造（兼容内部存储读取）；
        - 文字（大小写不敏感，如 dynamic / DYNAMIC）：按成员名解析。
        """
        if isinstance(text, cls):
            return text
        if text is None:
            raise ValueError("不支持的资源类型: None")
        if isinstance(text, int) or (isinstance(text, str) and text.strip().isdigit()):
            return cls(int(text))
        return cls[text.strip().upper()]

    def to_text(self) -> str:
        """转对外可读文字（dynamic / lottery / ...）。"""
        return self.name.lower()


class InteractionActionTypeEnum(IntEnumAutoDoc):
    """统一「互动操作类型」（动作维度；与 `InteractionBizTypeEnum` 资源维度明确区分）。

    本枚举是「互动操作类型」的唯一真相源（bili-common 收口），描述
    **发生了什么动作**（like / reply / at / audit_reject / hide / report_reject /
    report_resolved），与 `InteractionBizTypeEnum`（描述「作用在哪种资源上」）是
    **不同维度**，互不继承、不可混用。

    **合并（2026-09-01）**：已合并原 be-message 内部 `InteractionActionEnum`
    （`interaction_actions/base.py`，已删除）。两者同为「互动操作类型」但取值互相撞车
    （值 2 在本枚举为 `REPLY`、在原枚举为 `DISLIKE`，3~7 同理），**故不可按原值直接合并**。
    取值策略：既有 **1~7 原值一律不动**（`msg_event.event_type` 存量约束），
    新增操作自 **8** 起编号——见下方成员注释。

    **存储**：`msg_event.event_type` / `msg_event_cursor.event_type` 经
    `sqlalchemy.Enum(...)` 落为 **MySQL 原生 ENUM 存成员名**（存量遗留，与
    「禁原生 ENUM」的通用约定不一致），故**新增成员必须同步 ALTER 两表 ENUM 取值**；
    对外契约经 `from_text` / `to_text` 转换为可读文字（like / reply / …）。

    注意：`blocked_silent`（黑名单静默）与 `setting_gate`（消息设置闸门字段）属于
    be-message 的**投递语义**，已下沉到 insite events 的处理器类（`BaseEvent` 子类，
    见 `blocked_silent` / `setting_gate` 类属性），**本枚举只做值载体**，不承载任何业务
    行为元数据，避免最底层 bili-common 反向依赖上层服务。
    """

    LIKE = 1  # 点赞
    REPLY = 2  # 回复
    AT = 3  # @提及
    AUDIT_REJECT = 4  # 内容审核驳回（通知作者）
    # 2.38.0：内容因举报被管理员下架（通知资源作者，资源无作者时不发）
    HIDE = 5
    # 2.40.0：举报未通过审核 / 举报成立已处理（通知举报人）
    REPORT_REJECT = 6
    REPORT_RESOLVED = 7
    # ---- 以下为合并自原 be-message 内部 InteractionActionEnum 的操作（自 8 起编号）----
    # 既有 1~7 为通知事件类型（msg_event 存量约束，勿改）；下列为「用户执行的操作」，
    # 无通知语义，故不在 insite events 的 EVENT_REGISTRY 登记（未登记回落 GenericEvent）。
    DISLIKE = 8  # 点踩 / 取消点踩（EdgeRank 降权）
    FAVORITE = 9  # 收藏 / 取消收藏（多夹 + 用户去重计数）
    SHARE = 10  # 分享上报（shareCount +1，行为上报不幂等）
    REPOST = 11  # 转发 / attach（动态=生成 FORWARD；非动态=attach 行为计数 repostCount +1）
    VIEW = 12  # 浏览上报（弱依赖计数，跨天去重）
    REPORT = 13  # 举报（不改 auditStatus，仅加入审核队列）
    AUDIT_APPROVE = 14  # 审核通过（DAC：仅审核员；驳回复用既有 AUDIT_REJECT=4）

    @classmethod
    def from_text(cls, text: "InteractionActionTypeEnum | str | int | None") -> Self:
        """把对外文字（like/reply/...）或数值转换为枚举成员（统一入口）。

        - 已是枚举成员：原样返回；
        - 数字 / 数字字符串：按值构造（兼容内部存储读取）；
        - 文字（大小写不敏感，如 like / LIKE）：按成员名解析。
        """
        if isinstance(text, cls):
            return text
        if text is None:
            raise ValueError("不支持的操作类型: None")
        if isinstance(text, int) or (isinstance(text, str) and text.strip().isdigit()):
            return cls(int(text))
        return cls[text.strip().upper()]

    def to_text(self) -> str:
        """转对外可读文字（like / reply / ...）。"""
        return self.name.lower()


__all__ = ["InteractionBizTypeEnum", "InteractionActionTypeEnum"]
