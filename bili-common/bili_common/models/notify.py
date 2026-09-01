"""系统通知公共枚举（公共库）。

供 be-message-service（RPC 服务端）与其它系统（be-gateway / RPA-Browser /
be-bilibili-crawler 等 RPC 客户端）共享：属于「系统通知」RPC 契约的一部分
（见 `bili_common.rpc.notify`），放公共库避免两端各写一份导致取值漂移。

be-message 侧的历史 import 路径 `app.models.enums` 仍可导入同名枚举
（该文件已改为 re-export），存量代码零改动。

落库说明：MySQL 原生 ENUM 存**成员名**，接口序列化为整数，
见 `bili_common.models.IntEnumAutoDoc`。
"""

from bili_common.models import IntEnumAutoDoc


class NotifyTargetTypeEnum(IntEnumAutoDoc):
    """系统通知的目标用户类型（按用户类型推送）。"""

    # 全体用户
    ALL = 1
    # 按角色：target_value 为 root / normal
    ROLE = 2
    # 按等级：target_value 为最低等级，用户 level >= 该值即命中
    LEVEL = 3
    # 仅大会员：命中 vip_status 非空且不为 "0"
    VIP = 4
    # 指定用户：target_value 为逗号分隔的 mid 列表
    CUSTOM = 5


class NotifyLevelEnum(IntEnumAutoDoc):
    """通知重要级别，决定推送策略的激进程度。"""

    NORMAL = 1
    IMPORTANT = 2
    URGENT = 3


__all__ = ["NotifyLevelEnum", "NotifyTargetTypeEnum"]
