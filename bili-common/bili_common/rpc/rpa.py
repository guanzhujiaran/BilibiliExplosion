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

from bili_common.models import StrEnumAutoDoc

from sqlmodel import SQLModel, Field


class RpaRpcMethodName(StrEnumAutoDoc):
    """RPA 资源 RPC 业务方法名枚举。

    枚举值即 method_name，routing_key 自动生成为 `message.rpa.rpc.<method_name>`。
    """

    GET_RESOURCE_DETAIL = "get_resource_detail"
    # 2.39.0：举报处置——归属服务按 bizType 内部路由（lottery→crawler、rpa_*→本地）
    HIDE_RESOURCE = "hide_resource"
    # RPA 资源审核——归属服务对「发布审批单(rpa_approval, action=publish)」置通过/驳回
    REVIEW_RESOURCE = "review_resource"


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
}


__all__ = [
    "RpaRpcMethodName",
    "GetResourceDetailParams",
    "GetResourceDetailResult",
    "HideResourceParams",
    "HideResourceResult",
    "ReviewResourceParams",
    "ReviewResourceResult",
    "ResourceDetail",
    "RPA_RPC_CONTRACT",
]
