"""pptr 用户系统 RPC 契约（公共库）。

供 be-message-service（RPC 服务端，直接读写 pptr Postgres）与
be-gateway（RPC 客户端，Node.js amqplib）统一复用。
路由键前缀 `message.pptr.rpc`（见 `bili_common.rpc.base`）。

字段对齐 be-message-service/app/models/pptr_db.py 中的
PptrUserInfo / PptrUserDetail / PptrUserLevel / PptrUserVip。

约定（应对 Node.js Number 精度问题）：
- 业务侧整型字段一律声明为 int（Python 用 int 计算，最自然）；
- 反序列化（JS -> Python）时，借助 _IntStrMixin 的 before-validator 把字符串
  "87" 自动解析为 int 87，因此 JS 端可用字符串传大整数而不丢精度；
- 序列化（Python -> JS）时，借助 _IntStrMixin 的 serializer 把 int 再转回字符串，
  因此网络上始终以字符串传输，JS 端用 String 接收，不会被 Number 截断。
"""

from typing import ClassVar

from sqlmodel import SQLModel, Field

from bili_common.models._int_str import _IntStrMixin
from bili_common.models.pptr_user_gateway import PptrUserNavData  # noqa: F401
from bili_common.models.user_search import (  # noqa: F401
    PptrUserLevelInfo,
    PptrUserRoleInfo,
    PptrUserSearchResult,
    UserSearchParams,
)
from bili_common.rpc.base import (  # noqa: F401
    PPTR_RPC_ROUTING_KEY_PREFIX,
    RpcMethodName,
    pptr_routing_key_for,
)


# ---------------------------------------------------------------------------
# 请求参数
# ---------------------------------------------------------------------------


class PptrGetUserInfoParams(_IntStrMixin):
    """按 uid 或 user_name 查询完整用户信息（TUserInfo + TUserDetail + TUserLevel + TUserVip）。

    优先用 uid；uid 为 0 时改用 user_name 查（登录鉴权场景常用 user_name）。
    """

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid",)

    uid: int = Field(default=0, description="用户 UID（主键，0 表示改用 user_name 查）")
    user_name: str = Field(default="", description="登录用户名（uid 为 0 时使用）")


class PptrGetUserCardParams(_IntStrMixin):
    """按 uid 查询卡片简略信息（TUserInfo 核心字段 + TUserDetail 昵称/头像）"""

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid",)

    uid: int = Field(description="用户 UID（主键）")


class PptrCreateUserParams(_IntStrMixin):
    """创建用户（一次性写入 TUserInfo + TUserDetail + TUserLevel + TUserVip）。

    be-message 侧直接接管 pptr Postgres，pptr 不再维护本地 sequelize 用户表。
    与 CasdoorService.createLocalUserFromCasdoor 同步的字段一一对应。

    uid 默认 0 表示由服务端自增生成主键（pptr 侧登录时尚不知道 uid）。
    """

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid", "current_level", "vip_type", "vip_due_date", "vip_status")

    uid: int = Field(default=0, description="用户 UID（主键，0 表示服务端自增）")
    ip: str | None = Field(default=None, description="注册来源 IP（为空则不写注册 IP 信息）")
    ua: str | None = Field(default=None, description="注册来源 User-Agent（随 IP 一并记录）")
    user_name: str = Field(description="登录用户名（唯一）")
    pwd: str = Field(default="", description="登录密码 / Casdoor token 仓库（默认空）")
    createdAt: str = Field(default="", description="创建时间（ISO 字符串，空则服务端填当前）")

    # TUserDetail（face 在 DB 中列名为 avatar）
    uname: str = Field(default="", description="B站昵称 / Casdoor displayName")
    face: str | None = Field(default=None, description="头像 URL（映射到 TUserDetail.avatar）；无头像时为 None")
    sign: str = Field(default="", description="个性签名（映射到 TUserDetail.sign）")
    sex: str = Field(default="保密", description="性别（映射到 TUserDetail.sex）")
    email: str = Field(default="", description="邮箱（映射到 TUserDetail.email）")
    birthday: str = Field(default="", description="生日（ISO 字符串，映射到 TUserDetail.birthday）")
    # TUserLevel
    current_level: int = Field(default=0, description="当前等级")
    # TUserVip（vip_due_date 在 DB 中为整型时间戳，单位秒）
    vip_type: int = Field(default=0, description="大会员类型")
    vip_due_date: int = Field(default=0, description="大会员到期时间戳（秒）")
    vip_status: int = Field(default=0, description="大会员状态")


class PptrUpdateUserInfoParams(_IntStrMixin):
    """更新用户（按 uid 或 user_name 更新 TUserInfo 的 pwd / reg_ip_info_id）。

    供 Casdoor token 落库、注册 IP 登记等使用；pptr 彻底不碰本地用户表。
    """

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid", "reg_ip_info_id")

    uid: int = Field(default=0, description="用户 UID（主键，0 表示改用 user_name 查）")
    user_name: str = Field(default="", description="登录用户名（uid 为 0 时使用）")
    pwd: str = Field(default="", description="新密码 / Casdoor token（空则不更新）")
    reg_ip_info_id: int = Field(default=0, description="注册 IP 信息 id（0 则不更新）")


# ---------------------------------------------------------------------------
# 响应
# ---------------------------------------------------------------------------


class PptrUserCard(_IntStrMixin):
    """卡片简略信息（get_user_card 返回）"""

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid",)

    uid: int
    user_name: str = ""
    uname: str = ""
    face: str | None = None  # 前端/Node 侧称 face，对应 TUserDetail.avatar；无头像时为 None


class PptrUserProfile(_IntStrMixin):
    """完整用户信息（get_user_info 返回）"""

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid", "level", "current_level", "vip_type", "vip_due_date", "vip_status")

    uid: int
    user_name: str = ""
    role: str = Field(default="", description="用户角色（如 root / level0，供网关注入 x-bili-role 头）")
    pwd: str = ""
    createdAt: str = ""
    level: int = Field(default=0, description="TUserLevel.current_level 的别名，兼容调用方 localUser.level")
    # TUserDetail（face 对应 TUserDetail.avatar）
    uname: str = ""
    face: str | None = None
    email: str = ""
    # TUserLevel
    current_level: int = Field(default=0)
    # TUserVip（vip_due_date 为整型时间戳，单位秒）
    vip_type: int = Field(default=0)
    vip_due_date: int = Field(default=0)
    vip_status: int = Field(default=0)


class PptrCreateUserResult(_IntStrMixin):
    """创建用户结果（create_user 返回）"""

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid",)

    uid: int
    created: bool = Field(default=True, description="true=新建，false=已存在未重复创建")


class PptrUpdateUserInfoResult(_IntStrMixin):
    """更新用户结果（update_user_info 返回）"""

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid",)

    uid: int
    updated: bool = Field(default=True, description="true=更新成功，false=用户不存在")


class PptrGetUserLevelParams(_IntStrMixin):
    """按 uid 取等级信息（TUserLevel）。"""

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid",)

    uid: int = Field(description="用户 UID（主键）")


# PptrUserLevelInfo 定义在 user_search.py，本模块复用（见顶部 import）


class PptrSetUserLevelParams(_IntStrMixin):
    """原子写入等级经验（set_user_level）。

    经验/等级算法已在 be-message 侧完成（add_exp / add_daily_login_exp 内部调用），
    此处仅做原子落库，避免跨 RPC 事务。
    """

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid", "current_level", "current_exp", "current_min")

    uid: int
    current_level: int = Field(default=0)
    current_exp: int = Field(default=0)
    current_min: int = Field(default=0)


class PptrAddExpParams(_IntStrMixin):
    """增加经验值（add_exp，业务逻辑在 be-message 侧完成）。"""

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid", "exp")

    uid: int = Field(description="用户 UID（主键）")
    exp: int = Field(default=0, description="本次新增的经验值")
    action_type: str = Field(default="", description="行为类型，如 daily_login、post_comment 等，用于记录经验来源")


class PptrAddExpResult(_IntStrMixin):
    """add_exp 返回结果（含升级信息，业务逻辑已下沉 be-message）。"""

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid", "old_exp", "new_exp", "old_level", "new_level")

    uid: int
    old_exp: int = Field(default=0)
    new_exp: int = Field(default=0)
    old_level: int = Field(default=0)
    new_level: int = Field(default=0)
    leveled_up: bool = False
    role_updated: bool = False


class PptrAddDailyLoginExpParams(_IntStrMixin):
    """每日首次登录加经验（add_daily_login_exp，业务逻辑在 be-message 侧完成）。"""

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid",)

    uid: int = Field(description="用户 UID（主键）")


class PptrAddDailyLoginExpResult(_IntStrMixin):
    """add_daily_login_exp 返回结果。"""

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid", "old_exp", "new_exp", "old_level", "new_level")

    uid: int
    can_add_exp: bool = True
    old_exp: int = Field(default=0)
    new_exp: int = Field(default=0)
    old_level: int = Field(default=0)
    new_level: int = Field(default=0)
    leveled_up: bool = False
    role_updated: bool = False
    level_info: PptrUserLevelInfo | None = None


class PptrSetUserDetailParams(_IntStrMixin):
    """更新用户详情（set_user_detail，映射到 TUserDetail）。"""

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid",)

    uid: int
    uname: str = ""
    face: str | None = None
    sign: str = ""
    sex: str = "保密"
    email: str = ""
    birthday: str = ""


class PptrSetUserRoleParams(_IntStrMixin):
    """更新用户角色（set_user_role，映射到 TUserInfo.role）。"""

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid",)

    uid: int
    role: str = "level0"


class PptrSetResult(_IntStrMixin):
    """通用写结果。"""

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid",)

    uid: int
    updated: bool = True


class PptrAddUsernameRecordParams(_IntStrMixin):
    """记录昵称历史（add_username_record，映射到 TUserNameRecord）。"""

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid",)

    uid: int = Field(description="用户 UID（主键，对应 TUserNameRecord.mid）")
    prev_uname: str = Field(default="", description="改名前的旧昵称（写入 prev_uname）")


class PptrAddUsernameRecordResult(_IntStrMixin):
    """add_username_record 返回结果。"""

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid",)

    uid: int
    created: bool = Field(default=True, description="true=已写入历史，false=写入失败")


class PptrGetUserNavParams(_IntStrMixin):
    """按 uid 获取导航信息（get_user_nav）。

    pptr 通过一次 RPC 调用直接拿到 nav 所需全部数据（含等级计算、邮件脱敏），
    不再走多次 RPC 或 HTTP 反向代理。
    """

    _int_fields_: ClassVar[tuple[str, ...]] = ("uid",)

    uid: int = Field(description="用户 UID（主键）")


# PptrUserNavData 即 get_user_nav 的响应数据，定义在 pptr_user_gateway.py，此处复用。


# 方法名 -> 请求模型 -> 响应模型 的契约映射（仅供文档/校验参考）
PPTR_USER_RPC_CONTRACT: dict[str, tuple[type[SQLModel], type[SQLModel]]] = {
    RpcMethodName.GET_USER_INFO: (PptrGetUserInfoParams, PptrUserProfile),
    RpcMethodName.GET_USER_CARD: (PptrGetUserCardParams, PptrUserCard),
    RpcMethodName.CREATE_USER: (PptrCreateUserParams, PptrCreateUserResult),
    RpcMethodName.UPDATE_USER_INFO: (PptrUpdateUserInfoParams, PptrUpdateUserInfoResult),
    RpcMethodName.GET_USER_LEVEL: (PptrGetUserLevelParams, PptrUserLevelInfo),
    RpcMethodName.SET_USER_LEVEL: (PptrSetUserLevelParams, PptrSetResult),
    RpcMethodName.SET_USER_DETAIL: (PptrSetUserDetailParams, PptrSetResult),
    RpcMethodName.SET_USER_ROLE: (PptrSetUserRoleParams, PptrSetResult),
    RpcMethodName.SEARCH_USERS: (UserSearchParams, PptrUserSearchResult),
    RpcMethodName.ADD_EXP: (PptrAddExpParams, PptrAddExpResult),
    RpcMethodName.ADD_DAILY_LOGIN_EXP: (PptrAddDailyLoginExpParams, PptrAddDailyLoginExpResult),
    RpcMethodName.ADD_USERNAME_RECORD: (PptrAddUsernameRecordParams, PptrAddUsernameRecordResult),
    RpcMethodName.GET_USER_NAV: (PptrGetUserNavParams, PptrUserNavData),
}


__all__ = [
    "pptr_routing_key_for",
    "PptrGetUserInfoParams",
    "PptrGetUserCardParams",
    "PptrCreateUserParams",
    "PptrUpdateUserInfoParams",
    "PptrUserCard",
    "PptrUserProfile",
    "PptrCreateUserResult",
    "PptrUpdateUserInfoResult",
    "PptrGetUserLevelParams",
    "PptrUserLevelInfo",
    "PptrSetUserLevelParams",
    "PptrSetUserDetailParams",
    "PptrSetUserRoleParams",
    "PptrSetResult",
    "PptrAddExpParams",
    "PptrAddExpResult",
    "PptrAddDailyLoginExpParams",
    "PptrAddDailyLoginExpResult",
    "PptrAddUsernameRecordParams",
    "PptrAddUsernameRecordResult",
    "PptrGetUserNavParams",
    "PPTR_USER_RPC_CONTRACT",
    "UserSearchParams",
    "PptrUserSearchResult",
]
