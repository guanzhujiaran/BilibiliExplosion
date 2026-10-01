"""GeoIP 属地 RPC 契约（公共库）。

be-message-service 作为 RPC 服务端，其它系统（RPA-Browser 等）作为客户端，
经 RabbitMQ 按 `message.geoip.rpc.<method>` 同步调用，把客户端 IP 解析成可读属地。

为什么是 be-message 提供、而不是各服务各装一份 geoip2：

- **mmdb 单一来源**：GeoLite2 库（含 66MB 的 `GeoLite2-City.mmdb`）与下载 / 更新流程
  都只在本服务侧（`docker_vol/geoip/mmdb`，见其 `scripts/download_geoip_mmdb.py`）。
  各服务各存一份，等于一份库要更新 N 次、内存里多开 N 个 Reader；
- **口径一致**：评论 / 动态的 `lbsPoi` 与「谁在看」的地域标签出自同一段解析
  （`be-message-service/app/services/infrastructure/geo_ip.py`），
  不会出现「动态显示浙江、观看者显示杭州」这类不一致；
- **调用方零新依赖**：只用既有的 `bili_common.rpc.client.RpcClient`。

与既有 RPC 模式对齐：
- 路由键前缀 `message.geoip.rpc` 见 `bili_common.rpc.base`；
- 服务端返回 `StandardResponse{code, msg, data}`，异常在 RPC 边界由
  `bili_common.rpc.safe.rpc_safe` 翻译成 `error_response` 回包（客户端不会干等到超时）；
- 请求 / 响应模型统一用 SQLModel，保证两端契约一致。
"""

from bili_common.core.enums import StrEnumAutoDoc

from sqlmodel import SQLModel, Field


class GeoIpRpcMethodName(StrEnumAutoDoc):
    """GeoIP 属地 RPC 业务方法名枚举。

    枚举值即 method_name，routing_key 自动生成为 `message.geoip.rpc.<method_name>`。
    """

    RESOLVE_IP_REGION = "resolve_ip_region"


class ResolveIpRegionParams(SQLModel):
    """按 IP 解析属地请求"""

    ip: str = Field(
        default="",
        description=(
            "待解析的客户端 IP（网关注入的 x-bili-client-ip）；"
            "空串 / 内网 / 回环地址直接返回空属地"
        ),
    )


class ResolveIpRegionResult(SQLModel):
    """按 IP 解析属地结果（属地 + 运营商，一次调用一并返回）"""

    region: str = Field(
        default="",
        description=(
            "可读属地，形如「浙江 杭州」（GeoLite2-City 库）；解析不出"
            "（内网 / 未命中 / 库缺失）为空串，由调用方决定回退文案（前端显示「未知属地」）"
        ),
    )
    isp: str = Field(
        default="",
        description=(
            "运营商 / ISP（GeoLite2-ASN 库的 ASN 组织名，如 `China Unicom Shanghai network`；"
            "⚠️ 英文，该库无中文本地化）；解析不出（无 ASN 库 / 未命中）为空串"
            "（前端显示「未知运营商」）"
        ),
    )


__all__ = [
    "GeoIpRpcMethodName",
    "ResolveIpRegionParams",
    "ResolveIpRegionResult",
]
