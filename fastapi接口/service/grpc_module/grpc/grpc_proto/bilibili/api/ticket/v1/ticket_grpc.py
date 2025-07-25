# Generated by the Protocol Buffers compiler. DO NOT EDIT!
# source: bilibili/api/ticket/v1/ticket.proto
# plugin: grpclib.plugin.main
import abc
import typing

import grpclib.const
import grpclib.client
if typing.TYPE_CHECKING:
    import grpclib.server

import bilibili.api.ticket.v1.ticket_pb2


class TicketBase(abc.ABC):

    @abc.abstractmethod
    async def GetTicket(self, stream: 'grpclib.server.Stream[bilibili.api.ticket.v1.ticket_pb2.GetTicketRequest, bilibili.api.ticket.v1.ticket_pb2.GetTicketResponse]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/bilibili.api.ticket.v1.Ticket/GetTicket': grpclib.const.Handler(
                self.GetTicket,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.api.ticket.v1.ticket_pb2.GetTicketRequest,
                bilibili.api.ticket.v1.ticket_pb2.GetTicketResponse,
            ),
        }


class TicketStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.GetTicket = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.api.ticket.v1.Ticket/GetTicket',
            bilibili.api.ticket.v1.ticket_pb2.GetTicketRequest,
            bilibili.api.ticket.v1.ticket_pb2.GetTicketResponse,
        )
