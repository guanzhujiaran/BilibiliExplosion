# Generated by the Protocol Buffers compiler. DO NOT EDIT!
# source: bilibili/broadcast/v2/laser.proto
# plugin: grpclib.plugin.main
import abc
import typing

import grpclib.const
import grpclib.client
if typing.TYPE_CHECKING:
    import grpclib.server

import google.protobuf.empty_pb2
import bilibili.broadcast.v2.laser_pb2


class LaserBase(abc.ABC):

    @abc.abstractmethod
    async def WatchEvent(self, stream: 'grpclib.server.Stream[google.protobuf.empty_pb2.Empty, bilibili.broadcast.v2.laser_pb2.LaserEventResp]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/bilibili.broadcast.v2.Laser/WatchEvent': grpclib.const.Handler(
                self.WatchEvent,
                grpclib.const.Cardinality.UNARY_STREAM,
                google.protobuf.empty_pb2.Empty,
                bilibili.broadcast.v2.laser_pb2.LaserEventResp,
            ),
        }


class LaserStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.WatchEvent = grpclib.client.UnaryStreamMethod(
            channel,
            '/bilibili.broadcast.v2.Laser/WatchEvent',
            google.protobuf.empty_pb2.Empty,
            bilibili.broadcast.v2.laser_pb2.LaserEventResp,
        )
