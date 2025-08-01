# Generated by the Protocol Buffers compiler. DO NOT EDIT!
# source: bilibili/app/interfaces/v1/media.proto
# plugin: grpclib.plugin.main
import abc
import typing

import grpclib.const
import grpclib.client
if typing.TYPE_CHECKING:
    import grpclib.server

import bilibili.app.interfaces.v1.media_pb2


class MediaBase(abc.ABC):

    @abc.abstractmethod
    async def MediaTab(self, stream: 'grpclib.server.Stream[bilibili.app.interfaces.v1.media_pb2.MediaTabReq, bilibili.app.interfaces.v1.media_pb2.MediaTabReply]') -> None:
        pass

    @abc.abstractmethod
    async def MediaDetail(self, stream: 'grpclib.server.Stream[bilibili.app.interfaces.v1.media_pb2.MediaDetailReq, bilibili.app.interfaces.v1.media_pb2.MediaDetailReply]') -> None:
        pass

    @abc.abstractmethod
    async def MediaVideo(self, stream: 'grpclib.server.Stream[bilibili.app.interfaces.v1.media_pb2.MediaVideoReq, bilibili.app.interfaces.v1.media_pb2.MediaVideoReply]') -> None:
        pass

    @abc.abstractmethod
    async def MediaRelation(self, stream: 'grpclib.server.Stream[bilibili.app.interfaces.v1.media_pb2.MediaRelationReq, bilibili.app.interfaces.v1.media_pb2.MediaRelationReply]') -> None:
        pass

    @abc.abstractmethod
    async def MediaFollow(self, stream: 'grpclib.server.Stream[bilibili.app.interfaces.v1.media_pb2.MediaFollowReq, bilibili.app.interfaces.v1.media_pb2.MediaFollowReply]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/bilibili.app.interface.v1.Media/MediaTab': grpclib.const.Handler(
                self.MediaTab,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.app.interfaces.v1.media_pb2.MediaTabReq,
                bilibili.app.interfaces.v1.media_pb2.MediaTabReply,
            ),
            '/bilibili.app.interface.v1.Media/MediaDetail': grpclib.const.Handler(
                self.MediaDetail,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.app.interfaces.v1.media_pb2.MediaDetailReq,
                bilibili.app.interfaces.v1.media_pb2.MediaDetailReply,
            ),
            '/bilibili.app.interface.v1.Media/MediaVideo': grpclib.const.Handler(
                self.MediaVideo,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.app.interfaces.v1.media_pb2.MediaVideoReq,
                bilibili.app.interfaces.v1.media_pb2.MediaVideoReply,
            ),
            '/bilibili.app.interface.v1.Media/MediaRelation': grpclib.const.Handler(
                self.MediaRelation,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.app.interfaces.v1.media_pb2.MediaRelationReq,
                bilibili.app.interfaces.v1.media_pb2.MediaRelationReply,
            ),
            '/bilibili.app.interface.v1.Media/MediaFollow': grpclib.const.Handler(
                self.MediaFollow,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.app.interfaces.v1.media_pb2.MediaFollowReq,
                bilibili.app.interfaces.v1.media_pb2.MediaFollowReply,
            ),
        }


class MediaStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.MediaTab = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.app.interface.v1.Media/MediaTab',
            bilibili.app.interfaces.v1.media_pb2.MediaTabReq,
            bilibili.app.interfaces.v1.media_pb2.MediaTabReply,
        )
        self.MediaDetail = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.app.interface.v1.Media/MediaDetail',
            bilibili.app.interfaces.v1.media_pb2.MediaDetailReq,
            bilibili.app.interfaces.v1.media_pb2.MediaDetailReply,
        )
        self.MediaVideo = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.app.interface.v1.Media/MediaVideo',
            bilibili.app.interfaces.v1.media_pb2.MediaVideoReq,
            bilibili.app.interfaces.v1.media_pb2.MediaVideoReply,
        )
        self.MediaRelation = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.app.interface.v1.Media/MediaRelation',
            bilibili.app.interfaces.v1.media_pb2.MediaRelationReq,
            bilibili.app.interfaces.v1.media_pb2.MediaRelationReply,
        )
        self.MediaFollow = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.app.interface.v1.Media/MediaFollow',
            bilibili.app.interfaces.v1.media_pb2.MediaFollowReq,
            bilibili.app.interfaces.v1.media_pb2.MediaFollowReply,
        )
