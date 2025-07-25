# Generated by the Protocol Buffers compiler. DO NOT EDIT!
# source: bilibili/relation/interfaces/api.proto
# plugin: grpclib.plugin.main
import abc
import typing

import grpclib.const
import grpclib.client
if typing.TYPE_CHECKING:
    import grpclib.server

import bilibili.relation.interfaces.api_pb2


class RelationInterfaceBase(abc.ABC):

    @abc.abstractmethod
    async def AtSearch(self, stream: 'grpclib.server.Stream[bilibili.relation.interfaces.api_pb2.AtSearchReq, bilibili.relation.interfaces.api_pb2.AtSearchReply]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/bilibili.relation.interface.v1.RelationInterface/AtSearch': grpclib.const.Handler(
                self.AtSearch,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.relation.interfaces.api_pb2.AtSearchReq,
                bilibili.relation.interfaces.api_pb2.AtSearchReply,
            ),
        }


class RelationInterfaceStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.AtSearch = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.relation.interface.v1.RelationInterface/AtSearch',
            bilibili.relation.interfaces.api_pb2.AtSearchReq,
            bilibili.relation.interfaces.api_pb2.AtSearchReply,
        )
