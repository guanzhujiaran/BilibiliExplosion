"""RPA 资源 RPC 契约（公共库，2.18.0）。

RPA-Browser 作为 RPC 服务端，be-message 作为 RPC 客户端经 RabbitMQ 按
`message.rpa.rpc.<method>` 同步调用，获取 RPA 资源（action / workflow /
browser / plugin）的详情，随互动状态一并返回前端。

路由键前缀 `message.rpa.rpc` 见 `bili_common.rpc.base`。与既有
`message.pptr.rpc.*` / `message.push.rpc.*` 模式对齐：
- 客户端发布到默认 exchange，用 direct reply-to（`amq.rabbitmq.reply-to`）收响应；
- 服务端返回 `StandardResponse{code, msg, data}`，异常在 RPC 边界翻译成 `error_response` 回包；
- 请求 / 响应模型统一用 SQLModel，保证两端契约一致。
"""

from bili_common.core.enums import StrEnumAutoDoc

from sqlmodel import SQLModel, Field

from datetime import datetime


class RpaRpcMethodName(StrEnumAutoDoc):
    """RPA 资源 RPC 业务方法名枚举。

    枚举值即 method_name，routing_key 自动生成为 `message.rpa.rpc.<method_name>`。
    """

    GET_RESOURCE_DETAIL = "get_resource_detail"
    # 2.39.0：举报处置——归属服务按 bizType 内部路由（lottery→crawler、rpa_*→本地）
    HIDE_RESOURCE = "hide_resource"
    # RPA 资源审核——归属服务对「发布审批单(rpa_approval, action=publish)」置通过/驳回
    REVIEW_RESOURCE = "review_resource"

    # 2.49.0：rpa_tag 全托管——be-message 编排，经本组回调落 RPA 存储
    CREATE_TAG = "create_tag"
    ATTACH_TAG = "attach_tag"
    DETACH_TAG = "detach_tag"
    LIST_TAGS = "list_tags"
    LIST_TAGS_BY_TARGET = "list_tags_by_target"


# ---------------------------------------------------------------------------
# 请求参数
# ---------------------------------------------------------------------------


class GetResourceDetailParams(SQLModel):
    """获取 RPA 资源详情（get_resource_detail）。"""

    bizType: str = Field(description="资源类型：rpa_action / rpa_workflow / rpa_browser / rpa_plugin")
    bizId: int = Field(description="资源 id：action_id / workflow_id / browser_id / plugin_id")


class HideResourceParams(SQLModel):
    """举报处置请求（hide_resource，2.39.0）。

    归属服务（RPA-Browser）按 ``bizType`` 内部路由：
    lottery → be-bilibili-crawler；rpa_* → 本地下架/停用。
    """

    bizType: str = Field(description="资源类型：lottery / rpa_action / rpa_workflow / rpa_browser / rpa_plugin")
    bizId: int = Field(description="资源 id")
    operatorMid: int = Field(description="处置审核员 mid")
    reason: str = Field(default="", description="处置原因（可选）")


class HideResourceResult(SQLModel):
    """hide_resource 返回结果。"""

    success: bool = Field(default=False, description="是否成功处置")
    message: str | None = Field(default=None, description="失败原因 / 补充说明（可选）")


class ReviewResourceParams(SQLModel):
    """RPA 资源审核请求（review_resource）。

    归属服务（RPA-Browser）按 ``bizType`` + ``bizId`` 找到该资源**发布到社区的审批单**
    （`rpa_approval` 表，resource_type 去 rpa_ 前缀、resource_id 为该资源业务 id、
    action=publish），把其 status 置为 ``decision``。只改审批单，不动资源 is_public。
    """

    bizType: str = Field(description="资源类型：rpa_action / rpa_workflow / rpa_plugin")
    bizId: int = Field(description="资源表主键 id（int）")
    decision: str = Field(description="审核结果：approved / rejected")
    operatorMid: int = Field(description="审核员 mid")
    note: str = Field(default="", description="审核意见（可选）")


class ReviewResourceResult(SQLModel):
    """review_resource 返回结果。"""

    success: bool = Field(default=False, description="是否成功审核")
    message: str | None = Field(default=None, description="失败原因 / 补充说明（可选）")
    approvalId: int | None = Field(default=None, description="被审核的审批单 id（无匹配时为 None）")


# ---------------------------------------------------------------------------
# rpa_tag 全托管回调（2.49.0）：be-message 编排、RPA 落库
# ---------------------------------------------------------------------------


class CreateTagParams(SQLModel):
    """创建资源标签（create_tag）→ RPA 落 `auditing`。"""

    name: str = Field(description="标签名称（业务层已查重）")
    color: str = Field(default="#409EFF", description="标签颜色（十六进制）")
    createdMid: int = Field(description="创建者 mid")


class CreateTagResult(SQLModel):
    """create_tag 返回结果。"""

    success: bool = Field(default=False, description="是否成功创建")
    id: int | None = Field(default=None, description="新标签 id（失败为 None）")
    message: str | None = Field(default=None, description="失败原因（可选）")


class AttachTagParams(SQLModel):
    """为资源关联标签（attach_tag）；仅可关联 `normal` 标签。"""

    tagId: int = Field(description="标签 id")
    targetType: str = Field(description="目标资源类型：action / workflow / plugin")
    targetId: str = Field(description="目标资源 id（字符串）")
    createdMid: int = Field(description="关联操作者 mid")


class AttachTagResult(SQLModel):
    """attach_tag 返回结果。"""

    success: bool = Field(default=False, description="是否成功关联")
    alreadyExist: bool = Field(default=False, description="已存在则不再重复插入")
    message: str | None = Field(default=None, description="失败原因（可选）")


class DetachTagParams(SQLModel):
    """移除资源上的标签（detach_tag）。"""

    tagId: int = Field(description="标签 id")
    targetType: str = Field(description="目标资源类型")
    targetId: str = Field(description="目标资源 id（字符串）")


class DetachTagResult(SQLModel):
    """detach_tag 返回结果。"""

    success: bool = Field(default=False, description="是否成功移除")
    message: str | None = Field(default=None, description="失败原因（可选）")


class TagItemRpc(SQLModel):
    """资源标签条目（RPC 数据源）。"""

    id: int = Field(description="标签 id")
    name: str = Field(description="标签名称")
    color: str = Field(default="#409EFF", description="标签颜色")
    createdBy: int | None = Field(default=None, description="创建者 mid")
    auditStatus: str = Field(description="审核状态：auditing / normal / rejected")
    pubTime: datetime | None = Field(default=None, description="审核通过上架时间")
    createdAt: datetime | None = Field(default=None, description="创建时间")


class ListTagsParams(SQLModel):
    """列出标签（list_tags）。`auditStatus` 为 None 时默认仅 `normal`。"""

    auditStatus: str | None = Field(default=None, description="过滤状态；None→normal；'all'→全部（管理端）")
    page: int = Field(default=1, description="页码（从 1 起）")
    perPage: int = Field(default=20, description="每页条数")


class ListTagsResult(SQLModel):
    """list_tags 返回结果。"""

    total: int = Field(default=0, description="总数")
    items: list[TagItemRpc] = Field(default_factory=list, description="标签列表")


class ListTagsByTargetParams(SQLModel):
    """查询某资源关联的标签（list_tags_by_target）；仅返回 `normal`。"""

    targetType: str = Field(description="目标资源类型")
    targetId: str = Field(description="目标资源 id（字符串）")


class ListTagsByTargetResult(SQLModel):
    """list_tags_by_target 返回结果。"""

    items: list[TagItemRpc] = Field(default_factory=list, description="关联的标签列表")


# ---------------------------------------------------------------------------
# 响应
# ---------------------------------------------------------------------------


class ResourceDetail(SQLModel):
    """RPA 资源详情（供前端按 bizType 渲染跳转）。"""

    bizType: str = Field(description="资源类型")
    bizId: int = Field(description="资源 id")
    name: str = Field(default="", description="资源名称")
    cover: str | None = Field(default=None, description="封面图链接（可选）")
    authorMid: str | None = Field(default=None, description="作者 mid（字符串，避免精度丢失）")
    jumpUrl: str | None = Field(default=None, description="落地页跳转地址（可选）")
    extra: dict | None = Field(default=None, description="按类型的扩展字段（可选）")


class GetResourceDetailResult(SQLModel):
    """get_resource_detail 返回结果。"""

    detail: ResourceDetail | None = Field(default=None, description="资源详情；不存在时为 None")


# 方法名 -> (请求模型, 响应模型) 契约映射（文档 / 校验参考）
RPA_RPC_CONTRACT: dict[str, tuple[type[SQLModel], type[SQLModel]]] = {
    RpaRpcMethodName.GET_RESOURCE_DETAIL: (GetResourceDetailParams, GetResourceDetailResult),
    RpaRpcMethodName.HIDE_RESOURCE: (HideResourceParams, HideResourceResult),
    RpaRpcMethodName.REVIEW_RESOURCE: (ReviewResourceParams, ReviewResourceResult),
    RpaRpcMethodName.CREATE_TAG: (CreateTagParams, CreateTagResult),
    RpaRpcMethodName.ATTACH_TAG: (AttachTagParams, AttachTagResult),
    RpaRpcMethodName.DETACH_TAG: (DetachTagParams, DetachTagResult),
    RpaRpcMethodName.LIST_TAGS: (ListTagsParams, ListTagsResult),
    RpaRpcMethodName.LIST_TAGS_BY_TARGET: (ListTagsByTargetParams, ListTagsByTargetResult),
}


__all__ = [
    "RpaRpcMethodName",
    "GetResourceDetailParams",
    "GetResourceDetailResult",
    "HideResourceParams",
    "HideResourceResult",
    "ReviewResourceParams",
    "ReviewResourceResult",
    "CreateTagParams",
    "CreateTagResult",
    "AttachTagParams",
    "AttachTagResult",
    "DetachTagParams",
    "DetachTagResult",
    "ListTagsParams",
    "ListTagsResult",
    "ListTagsByTargetParams",
    "ListTagsByTargetResult",
    "TagItemRpc",
    "ResourceDetail",
    "RPA_RPC_CONTRACT",
]
