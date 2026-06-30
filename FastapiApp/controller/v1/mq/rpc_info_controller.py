"""
RPC 服务信息控制器

提供通用接口查询 FastapiApp 暴露的所有 RPC 方法元数据，
供 RPA-Browser 或前端获取可选 RPC 方法列表。

单一数据源：方法元数据统一定义在 Models/rpc_models.py 的 ALLOWED_RPC_METHODS，
本控制器仅负责对外暴露，避免在多处维护重复列表。
"""

from fastapi import APIRouter

from ApiRoutes import RouterPrefix, RouterTags, RouterPaths
from Models.common import CommonResponseModel
from Models.rpc_models import RpcMethodInfoResponse, build_method_responses

router = APIRouter()
router.tags = [RouterTags.RPC]
router.prefix = RouterPrefix.RPC


@router.get(
    RouterPaths.GET_RPC_METHODS,
    response_model=CommonResponseModel[list[RpcMethodInfoResponse]],
    summary="获取所有 RPC 方法信息",
    description=(
        "返回 FastapiApp 当前注册的所有 RPC 业务方法元数据列表，"
        "包含 method_name、display_name、description、routing_key。"
        "RPA-Browser 的获取外部数据 Action（RPC 模式）可从此接口获取可选方法列表。"
    ),
)
async def list_rpc_methods() -> CommonResponseModel[list[RpcMethodInfoResponse]]:
    """获取所有 RPC 方法信息"""
    return CommonResponseModel(data=build_method_responses())
