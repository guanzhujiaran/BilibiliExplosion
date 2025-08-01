# Generated by the Protocol Buffers compiler. DO NOT EDIT!
# source: bilibili/im/interfaces/inner-interface/v1/api.proto
# plugin: grpclib.plugin.main
import abc
import typing

import grpclib.const
import grpclib.client
if typing.TYPE_CHECKING:
    import grpclib.server

import bilibili.im.interfaces.inner_interface.v1.api_pb2


class InnerInterfaceBase(abc.ABC):

    @abc.abstractmethod
    async def UpdateListInn(self, stream: 'grpclib.server.Stream[bilibili.im.interfaces.inner_interface.v1.api_pb2.ReqOpBlacklist, bilibili.im.interfaces.inner_interface.v1.api_pb2.RspOpBlacklist]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/bilibili.im.interface.inner.interface.v1.InnerInterface/UpdateListInn': grpclib.const.Handler(
                self.UpdateListInn,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.im.interfaces.inner_interface.v1.api_pb2.ReqOpBlacklist,
                bilibili.im.interfaces.inner_interface.v1.api_pb2.RspOpBlacklist,
            ),
        }


class InnerInterfaceStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.UpdateListInn = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.im.interface.inner.interface.v1.InnerInterface/UpdateListInn',
            bilibili.im.interfaces.inner_interface.v1.api_pb2.ReqOpBlacklist,
            bilibili.im.interfaces.inner_interface.v1.api_pb2.RspOpBlacklist,
        )
