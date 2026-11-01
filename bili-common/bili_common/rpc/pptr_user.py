"""pptr 用户系统 RPC 契约（公共库）。

供 be-message-service（RPC 服务端，直接读写 pptr Postgres）与
be-gateway（RPC 客户端，Node.js amqplib）统一复用。
路由键前缀 `message.pptr.rpc`（见 `bili_common.rpc.base`）。

字段对齐 be-message-service/app/models/pptr_db.py 中的
PptrUserInfo / PptrUserDetail / PptrUserLevel / PptrUserVip。

约定（应对 Node.js Number 精度问题）：
- **入参**（JS -> Python）：雪花 ID 一律声明为 `StrInt`（`anyOf[int, str]`），
  JS 端可用字符串传大整数，后端入口自动归一为 int，内部一律 int 计算；
- **出参**（Python -> JS）：雪花 ID 声明为 int，字符串版由 `@auto_str` 自动派生
  （本模块统一用 `Str` 后缀，`uid` -> `uidStr`），JS 端只消费字符串版，
  不会被 Number 截断。
"""

from sqlmodel import SQLModel, Field

from bili_common.models.auto_str import auto_str
from bili_common.models.str_int import StrInt
from bili_common.models.pptr_user_gateway import PptrUserNavData
from bili_common.models.user_search import (
    PptrUserLevelInfo,
    PptrUserRoleInfo,
    PptrUserSearchResult,
    UserSearchParams,
)
from bili_common.rpc.base import (
    PPTR_RPC_ROUTING_KEY_PREFIX,
    RpcMethodName,
    pptr_routing_key_for,
)


# ---------------------------------------------------------------------------
# 请求参数
# ---------------------------------------------------------------------------


class PptrGetUserInfoParams(SQLModel):
    """按 uid 或 user_name 查询完整用户信息（TUserInfo + TUserDetail + TUserLevel + TUserVip）。

    优先用 uid；uid 为 0 时改用 user_name 查（登录鉴权场景常用 user_name）。
    """

    uid: StrInt = Field(
        default=0, description="用户 UID（主键，0 表示改用 user_name 查）"
    )
    user_name: str = Field(default="", description="登录用户名（uid 为 0 时使用）")


class PptrGetUserCardParams(SQLModel):
    """按 uid 查询卡片简略信息（TUserInfo 核心字段 + TUserDetail 昵称/头像）"""

    uid: StrInt = Field(description="用户 UID（主键）")


class PptrCreateUserParams(SQLModel):
    """创建用户（一次性写入 TUserInfo + TUserDetail + TUserLevel + TUserVip）。

    be-message 侧直接接管 pptr Postgres，pptr 不再维护本地 sequelize 用户表。
    与 CasdoorService.createLocalUserFromCasdoor 同步的字段一一对应。

    uid 默认 0 表示由服务端自增生成主键（pptr 侧登录时尚不知道 uid）。
    """

    uid: StrInt = Field(default=0, description="用户 UID（主键，0 表示服务端自增）")
    ip: str | None = Field(
        default=None, description="注册来源 IP（为空则不写注册 IP 信息）"
    )
    ua: str | None = Field(
        default=None, description="注册来源 User-Agent（随 IP 一并记录）"
    )
    user_name: str = Field(description="登录用户名（唯一）")
    pwd: str = Field(default="", description="登录密码 / Casdoor token 仓库（默认空）")
    createdAt: str = Field(
        default="", description="创建时间（ISO 字符串，空则服务端填当前）"
    )

    # TUserDetail（face 在 DB 中列名为 avatar）
    uname: str = Field(default="", description="B站昵称 / Casdoor displayName")
    face: str | None = Field(
        default=None,
        description="头像 URL（映射到 TUserDetail.avatar）；无头像时为 None",
    )
    sign: str = Field(default="", description="个性签名（映射到 TUserDetail.sign）")
    sex: str = Field(default="保密", description="性别（映射到 TUserDetail.sex）")
    email: str = Field(default="", description="邮箱（映射到 TUserDetail.email）")
    birthday: str = Field(
        default="", description="生日（ISO 字符串，映射到 TUserDetail.birthday）"
    )
    # TUserLevel
    current_level: int = Field(default=0, description="当前等级")
    # TUserVip（vip_due_date 在 DB 中为整型时间戳，单位秒）
    vip_type: int = Field(default=0, description="大会员类型")
    vip_due_date: int = Field(default=0, description="大会员到期时间戳（秒）")
    vip_status: int = Field(default=0, description="大会员状态")


class PptrUpdateUserInfoParams(SQLModel):
    """更新用户（按 uid 或 user_name 更新 TUserInfo 的 pwd / reg_ip_info_id）。

    供 Casdoor token 落库、注册 IP 登记等使用；pptr 彻底不碰本地用户表。
    """

    uid: StrInt = Field(
        default=0, description="用户 UID（主键，0 表示改用 user_name 查）"
    )
    user_name: str = Field(default="", description="登录用户名（uid 为 0 时使用）")
    pwd: str = Field(default="", description="新密码 / Casdoor token（空则不更新）")
    reg_ip_info_id: int = Field(default=0, description="注册 IP 信息 id（0 则不更新）")


# ---------------------------------------------------------------------------
# 响应
# ---------------------------------------------------------------------------


@auto_str
class PptrUserCard(SQLModel):
    """卡片简略信息（get_user_card 返回）"""

    uid: int
    user_name: str = ""
    uname: str = ""
    face: str | None = (
        None  # 前端/Node 侧称 face，对应 TUserDetail.avatar；无头像时为 None
    )


@auto_str
class PptrUserProfile(SQLModel):
    """完整用户信息（get_user_info 返回）"""

    uid: int
    user_name: str = ""
    role: str = Field(
        default="",
        description="用户角色（如 root / level0，供网关注入 x-bili-role 头）",
    )
    pwd: str = ""
    createdAt: str = ""
    level: int = Field(
        default=0,
        description="TUserLevel.current_level 的别名，兼容调用方 localUser.level",
    )
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


@auto_str
class PptrCreateUserResult(SQLModel):
    """创建用户结果（create_user 返回）"""

    uid: int
    created: bool = Field(default=True, description="true=新建，false=已存在未重复创建")


@auto_str
class PptrUpdateUserInfoResult(SQLModel):
    """更新用户结果（update_user_info 返回）"""

    uid: int
    updated: bool = Field(default=True, description="true=更新成功，false=用户不存在")


class PptrGetUserLevelParams(SQLModel):
    """按 uid 取等级信息（TUserLevel）。"""

    uid: StrInt = Field(description="用户 UID（主键）")


# PptrUserLevelInfo 定义在 user_search.py，本模块复用（见顶部 import）


class PptrSetUserLevelParams(SQLModel):
    """原子写入等级经验（set_user_level）。

    经验/等级算法已在 be-message 侧完成（add_exp / add_daily_login_exp 内部调用），
    此处仅做原子落库，避免跨 RPC 事务。
    """

    uid: StrInt
    current_level: int = Field(default=0)
    current_exp: int = Field(default=0)
    current_min: int = Field(default=0)


class PptrAddExpParams(SQLModel):
    """增加经验值（add_exp，业务逻辑在 be-message 侧完成）。"""

    uid: StrInt = Field(description="用户 UID（主键）")
    exp: int = Field(default=0, description="本次新增的经验值")
    action_type: str = Field(
        default="",
        description="行为类型，如 daily_login、post_comment 等，用于记录经验来源",
    )


@auto_str
class PptrAddExpResult(SQLModel):
    """add_exp 返回结果（含升级信息，业务逻辑已下沉 be-message）。"""

    uid: int
    old_exp: int = Field(default=0)
    new_exp: int = Field(default=0)
    old_level: int = Field(default=0)
    new_level: int = Field(default=0)
    leveled_up: bool = False
    role_updated: bool = False


class PptrAddDailyLoginExpParams(SQLModel):
    """每日首次登录加经验（add_daily_login_exp，业务逻辑在 be-message 侧完成）。"""

    uid: StrInt = Field(description="用户 UID（主键）")


@auto_str
class PptrAddDailyLoginExpResult(SQLModel):
    """add_daily_login_exp 返回结果。"""

    uid: int
    can_add_exp: bool = True
    old_exp: int = Field(default=0)
    new_exp: int = Field(default=0)
    old_level: int = Field(default=0)
    new_level: int = Field(default=0)
    leveled_up: bool = False
    role_updated: bool = False
    level_info: PptrUserLevelInfo | None = None


class PptrSetUserDetailParams(SQLModel):
    """更新用户详情（set_user_detail，映射到 TUserDetail）。"""

    uid: StrInt
    uname: str = ""
    face: str | None = None
    sign: str = ""
    sex: str = "保密"
    email: str = ""
    birthday: str = ""


class PptrSetUserRoleParams(SQLModel):
    """更新用户角色（set_user_role，映射到 TUserInfo.role）。"""

    uid: StrInt
    role: str = "level0"


@auto_str
class PptrSetResult(SQLModel):
    """通用写结果。"""

    uid: int
    updated: bool = True


class PptrAddUsernameRecordParams(SQLModel):
    """记录昵称历史（add_username_record，映射到 TUserNameRecord）。"""

    uid: StrInt = Field(description="用户 UID（主键，对应 TUserNameRecord.mid）")
    prev_uname: str = Field(default="", description="改名前的旧昵称（写入 prev_uname）")


@auto_str
class PptrAddUsernameRecordResult(SQLModel):
    """add_username_record 返回结果。"""

    uid: int
    created: bool = Field(default=True, description="true=已写入历史，false=写入失败")


class PptrGetUserNavParams(SQLModel):
    """按 uid 获取导航信息（get_user_nav）。

    pptr 通过一次 RPC 调用直接拿到 nav 所需全部数据（含等级计算、邮件脱敏），
    不再走多次 RPC 或 HTTP 反向代理。
    """

    uid: StrInt = Field(description="用户 UID（主键）")


# PptrUserNavData 即 get_user_nav 的响应数据，定义在 pptr_user_gateway.py，此处复用。


# 方法名 -> 请求模型 -> 响应模型 的契约映射（仅供文档/校验参考）
PPTR_USER_RPC_CONTRACT: dict[str, tuple[type[SQLModel], type[SQLModel]]] = {
    RpcMethodName.GET_USER_INFO: (PptrGetUserInfoParams, PptrUserProfile),
    RpcMethodName.GET_USER_CARD: (PptrGetUserCardParams, PptrUserCard),
    RpcMethodName.CREATE_USER: (PptrCreateUserParams, PptrCreateUserResult),
    RpcMethodName.UPDATE_USER_INFO: (
        PptrUpdateUserInfoParams,
        PptrUpdateUserInfoResult,
    ),
    RpcMethodName.GET_USER_LEVEL: (PptrGetUserLevelParams, PptrUserLevelInfo),
    RpcMethodName.SET_USER_LEVEL: (PptrSetUserLevelParams, PptrSetResult),
    RpcMethodName.SET_USER_DETAIL: (PptrSetUserDetailParams, PptrSetResult),
    RpcMethodName.SET_USER_ROLE: (PptrSetUserRoleParams, PptrSetResult),
    RpcMethodName.SEARCH_USERS: (UserSearchParams, PptrUserSearchResult),
    RpcMethodName.ADD_EXP: (PptrAddExpParams, PptrAddExpResult),
    RpcMethodName.ADD_DAILY_LOGIN_EXP: (
        PptrAddDailyLoginExpParams,
        PptrAddDailyLoginExpResult,
    ),
    RpcMethodName.ADD_USERNAME_RECORD: (
        PptrAddUsernameRecordParams,
        PptrAddUsernameRecordResult,
    ),
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
