# Generated by the Protocol Buffers compiler. DO NOT EDIT!
# source: bilibili/app/playeronline/v1/playeronline.proto
# plugin: grpclib.plugin.main
import abc
import typing

import grpclib.const
import grpclib.client
if typing.TYPE_CHECKING:
    import grpclib.server

import bilibili.app.playeronline.v1.playeronline_pb2


class PlayerOnlineBase(abc.ABC):

    @abc.abstractmethod
    async def PlayerOnline(self, stream: 'grpclib.server.Stream[bilibili.app.playeronline.v1.playeronline_pb2.PlayerOnlineReq, bilibili.app.playeronline.v1.playeronline_pb2.PlayerOnlineReply]') -> None:
        pass

    @abc.abstractmethod
    async def PremiereInfo(self, stream: 'grpclib.server.Stream[bilibili.app.playeronline.v1.playeronline_pb2.PremiereInfoReq, bilibili.app.playeronline.v1.playeronline_pb2.PremiereInfoReply]') -> None:
        pass

    @abc.abstractmethod
    async def ReportWatch(self, stream: 'grpclib.server.Stream[bilibili.app.playeronline.v1.playeronline_pb2.ReportWatchReq, bilibili.app.playeronline.v1.playeronline_pb2.NoReply]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/bilibili.app.playeronline.v1.PlayerOnline/PlayerOnline': grpclib.const.Handler(
                self.PlayerOnline,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.app.playeronline.v1.playeronline_pb2.PlayerOnlineReq,
                bilibili.app.playeronline.v1.playeronline_pb2.PlayerOnlineReply,
            ),
            '/bilibili.app.playeronline.v1.PlayerOnline/PremiereInfo': grpclib.const.Handler(
                self.PremiereInfo,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.app.playeronline.v1.playeronline_pb2.PremiereInfoReq,
                bilibili.app.playeronline.v1.playeronline_pb2.PremiereInfoReply,
            ),
            '/bilibili.app.playeronline.v1.PlayerOnline/ReportWatch': grpclib.const.Handler(
                self.ReportWatch,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.app.playeronline.v1.playeronline_pb2.ReportWatchReq,
                bilibili.app.playeronline.v1.playeronline_pb2.NoReply,
            ),
        }


class PlayerOnlineStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.PlayerOnline = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.app.playeronline.v1.PlayerOnline/PlayerOnline',
            bilibili.app.playeronline.v1.playeronline_pb2.PlayerOnlineReq,
            bilibili.app.playeronline.v1.playeronline_pb2.PlayerOnlineReply,
        )
        self.PremiereInfo = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.app.playeronline.v1.PlayerOnline/PremiereInfo',
            bilibili.app.playeronline.v1.playeronline_pb2.PremiereInfoReq,
            bilibili.app.playeronline.v1.playeronline_pb2.PremiereInfoReply,
        )
        self.ReportWatch = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.app.playeronline.v1.PlayerOnline/ReportWatch',
            bilibili.app.playeronline.v1.playeronline_pb2.ReportWatchReq,
            bilibili.app.playeronline.v1.playeronline_pb2.NoReply,
        )
