"""pptr 用户网关接口（`/api/v1/user/*`）的请求 / 响应模型。

**背景**：pptr（Express）原先自行实现 `/api/v1/user/nav`、`/user_info/update`、
`/role/set`、`/search` 四个纯数据接口。这些接口不依赖任何 Node 独有能力
（JWT 签发 / Redis 黑名单 / Casdoor SDK），业务逻辑已整体下沉 be-message，
故 pptr 退化为反向代理，仅负责 JWT 验签并注入 `x-bili-*` 可信身份头。

**响应统一走 `StandardResponse`**（`code=0` 表示成功），不再沿用 pptr 旧的
`{code, data, msg, ttl}` 格式；前端需同步改造为读取 `StandardResponse`。

bigint（uid / mid）一律以字符串返回，避免 JS 端 Number 精度丢失，与
`PptrUserSearchItem` 的既有口径保持一致。
"""



from sqlmodel import SQLModel, Field

from bili_common.models.user_search import (
    PptrUserLevelInfo,
    PptrUserRoleInfo,
)


class PptrUserNavData(SQLModel):
    """`GET /api/v1/user/nav` 的响应数据。

    对齐 pptr 旧 `UserLevelService.get_user_nav_with_level` 的出参结构：
    调用时会顺带触发「每日首次登录加经验」（幂等，由 be-message 侧判定）。
    """

    uid: str = Field(default="", description="用户ID（字符串，防精度丢失）")
    user_name: str = Field(default="", description="展示名：优先昵称 uname，缺失时回落注册名")
    role_info: PptrUserRoleInfo = Field(default_factory=PptrUserRoleInfo)
    face: str | None = Field(default=None, description="头像URL；无头像时为 null，由前端回落到默认头像")
    level_info: PptrUserLevelInfo = Field(default_factory=PptrUserLevelInfo)
    email: str | None = Field(default=None, description="邮箱（脱敏）")
    jwt_token: str | None = Field(default=None, description="JWT 续期时注入的新 token（非当天签发的 token 需刷新）")


class PptrUserInfoUpdateParams(SQLModel):
    """`POST /api/v1/user/user_info/update` 的请求体。

    各字段均为可选（只传要修改的字段），空串表示该字段不修改。
    校验规则对齐 pptr 旧 express-validator：昵称 2~24 字（有值时）、签名 ≤70 字、
    性别限定枚举；生日为 ISO 日期字符串。
    """

    uname: str = Field(default="", max_length=24, description="昵称（空串=不修改；非空时 2-24 字，接口层校验最短 2 字）")
    usersign: str = Field(default="", max_length=70, description="个性签名（最多 70 字）")
    sex: str = Field(default="保密", description="性别：男 / 女 / 保密 / 武装直升机 / 永雏塔菲")
    birthday: str = Field(default="", description="生日（ISO 日期字符串）")
    avatar: str = Field(
        default="",
        max_length=1024,
        description="头像图片 URL（http/https，2.16.0 新增；后端下载校验：1s 内下载完成且 ≤1MB；空串表示不修改）",
    )


class PptrUserInfoUpdateResult(SQLModel):
    """用户信息更新结果。"""

    uid: str = Field(default="", description="被更新的用户ID")
    updated: bool = Field(default=False, description="是否更新成功")
    uname_recorded: bool = Field(
        default=False, description="昵称发生变更并已写入昵称历史表 TUserNameRecord"
    )
    avatar_status: str | None = Field(
        default=None,
        description="头像字段处理结果：'pending'（已提交审核，未即时生效）/ 'none'（本次未修改头像）",
    )


class PptrUserRoleSetParams(SQLModel):
    """`POST /api/v1/user/role/set` 的请求体（仅 root 可调用）。

    命名上与 RPC 侧的 `PptrSetUserRoleParams`（bili_common.models.pptr_user_rpc）区分：
    本模型是**网关 HTTP 接口**的入参（含 target_uid，操作者身份来自 x-bili-* 头），
    RPC 侧那个是 be-message 内部落库用的参数。
    """

    target_uid: str = Field(description="目标用户UID")
    role: str = Field(description="目标角色：level0..level6 或 root")


class PptrUserRoleSetResult(SQLModel):
    """角色设置结果。"""

    target_uid: str = Field(default="", description="目标用户UID")
    target_user_name: str = Field(default="", description="目标用户注册名")
    role: str = Field(default="", description="设置后的角色标识")
    role_name: str = Field(default="", description="角色中文名")
    role_description: str = Field(default="", description="角色中文描述")


# 性别允许值，与 pptr 旧 express-validator 的 isIn 校验保持一致
VALID_SEX_VALUES = ("男", "女", "保密", "武装直升机", "永雏塔菲")

# 合法角色，与 pptr `user_role_const.VALID_ROLES` 对齐
VALID_ROLES = (
    "level0",
    "level1",
    "level2",
    "level3",
    "level4",
    "level5",
    "level6",
    "root",
)
ROLE_ROOT = "root"


__all__ = [
    "PptrUserNavData",
    "PptrUserInfoUpdateParams",
    "PptrUserInfoUpdateResult",
    "PptrUserRoleSetParams",
    "PptrUserRoleSetResult",
    "VALID_SEX_VALUES",
    "VALID_ROLES",
    "ROLE_ROOT",
]
