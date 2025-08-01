# Generated by the Protocol Buffers compiler. DO NOT EDIT!
# source: bilibili/app/playurl/v1/playurl.proto
# plugin: grpclib.plugin.main
import abc
import typing

import grpclib.const
import grpclib.client
if typing.TYPE_CHECKING:
    import grpclib.server

import bilibili.app.playurl.v1.playurl_pb2


class PlayURLBase(abc.ABC):

    @abc.abstractmethod
    async def PlayURL(self, stream: 'grpclib.server.Stream[bilibili.app.playurl.v1.playurl_pb2.PlayURLReq, bilibili.app.playurl.v1.playurl_pb2.PlayURLReply]') -> None:
        pass

    @abc.abstractmethod
    async def Project(self, stream: 'grpclib.server.Stream[bilibili.app.playurl.v1.playurl_pb2.ProjectReq, bilibili.app.playurl.v1.playurl_pb2.ProjectReply]') -> None:
        pass

    @abc.abstractmethod
    async def PlayView(self, stream: 'grpclib.server.Stream[bilibili.app.playurl.v1.playurl_pb2.PlayViewReq, bilibili.app.playurl.v1.playurl_pb2.PlayViewReply]') -> None:
        pass

    @abc.abstractmethod
    async def PlayConfEdit(self, stream: 'grpclib.server.Stream[bilibili.app.playurl.v1.playurl_pb2.PlayConfEditReq, bilibili.app.playurl.v1.playurl_pb2.PlayConfEditReply]') -> None:
        pass

    @abc.abstractmethod
    async def PlayConf(self, stream: 'grpclib.server.Stream[bilibili.app.playurl.v1.playurl_pb2.PlayConfReq, bilibili.app.playurl.v1.playurl_pb2.PlayConfReply]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/bilibili.app.playurl.v1.PlayURL/PlayURL': grpclib.const.Handler(
                self.PlayURL,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.app.playurl.v1.playurl_pb2.PlayURLReq,
                bilibili.app.playurl.v1.playurl_pb2.PlayURLReply,
            ),
            '/bilibili.app.playurl.v1.PlayURL/Project': grpclib.const.Handler(
                self.Project,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.app.playurl.v1.playurl_pb2.ProjectReq,
                bilibili.app.playurl.v1.playurl_pb2.ProjectReply,
            ),
            '/bilibili.app.playurl.v1.PlayURL/PlayView': grpclib.const.Handler(
                self.PlayView,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.app.playurl.v1.playurl_pb2.PlayViewReq,
                bilibili.app.playurl.v1.playurl_pb2.PlayViewReply,
            ),
            '/bilibili.app.playurl.v1.PlayURL/PlayConfEdit': grpclib.const.Handler(
                self.PlayConfEdit,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.app.playurl.v1.playurl_pb2.PlayConfEditReq,
                bilibili.app.playurl.v1.playurl_pb2.PlayConfEditReply,
            ),
            '/bilibili.app.playurl.v1.PlayURL/PlayConf': grpclib.const.Handler(
                self.PlayConf,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.app.playurl.v1.playurl_pb2.PlayConfReq,
                bilibili.app.playurl.v1.playurl_pb2.PlayConfReply,
            ),
        }


class PlayURLStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.PlayURL = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.app.playurl.v1.PlayURL/PlayURL',
            bilibili.app.playurl.v1.playurl_pb2.PlayURLReq,
            bilibili.app.playurl.v1.playurl_pb2.PlayURLReply,
        )
        self.Project = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.app.playurl.v1.PlayURL/Project',
            bilibili.app.playurl.v1.playurl_pb2.ProjectReq,
            bilibili.app.playurl.v1.playurl_pb2.ProjectReply,
        )
        self.PlayView = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.app.playurl.v1.PlayURL/PlayView',
            bilibili.app.playurl.v1.playurl_pb2.PlayViewReq,
            bilibili.app.playurl.v1.playurl_pb2.PlayViewReply,
        )
        self.PlayConfEdit = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.app.playurl.v1.PlayURL/PlayConfEdit',
            bilibili.app.playurl.v1.playurl_pb2.PlayConfEditReq,
            bilibili.app.playurl.v1.playurl_pb2.PlayConfEditReply,
        )
        self.PlayConf = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.app.playurl.v1.PlayURL/PlayConf',
            bilibili.app.playurl.v1.playurl_pb2.PlayConfReq,
            bilibili.app.playurl.v1.playurl_pb2.PlayConfReply,
        )
