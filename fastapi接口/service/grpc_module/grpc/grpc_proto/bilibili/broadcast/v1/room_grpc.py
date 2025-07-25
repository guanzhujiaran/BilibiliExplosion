# Generated by the Protocol Buffers compiler. DO NOT EDIT!
# source: bilibili/broadcast/v1/room.proto
# plugin: grpclib.plugin.main
import abc
import typing

import grpclib.const
import grpclib.client
if typing.TYPE_CHECKING:
    import grpclib.server

import bilibili.rpc.status_pb2
import bilibili.broadcast.v1.room_pb2


class BroadcastRoomBase(abc.ABC):

    @abc.abstractmethod
    async def Enter(self, stream: 'grpclib.server.Stream[bilibili.broadcast.v1.room_pb2.RoomReq, bilibili.broadcast.v1.room_pb2.RoomResp]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/bilibili.broadcast.v1.BroadcastRoom/Enter': grpclib.const.Handler(
                self.Enter,
                grpclib.const.Cardinality.STREAM_STREAM,
                bilibili.broadcast.v1.room_pb2.RoomReq,
                bilibili.broadcast.v1.room_pb2.RoomResp,
            ),
        }


class BroadcastRoomStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.Enter = grpclib.client.StreamStreamMethod(
            channel,
            '/bilibili.broadcast.v1.BroadcastRoom/Enter',
            bilibili.broadcast.v1.room_pb2.RoomReq,
            bilibili.broadcast.v1.room_pb2.RoomResp,
        )
