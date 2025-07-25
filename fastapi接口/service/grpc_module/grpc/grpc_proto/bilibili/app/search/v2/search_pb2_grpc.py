# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from bilibili.app.search.v2 import search_pb2 as bilibili_dot_app_dot_search_dot_v2_dot_search__pb2
from bilibili.broadcast.message.main import search_pb2 as bilibili_dot_broadcast_dot_message_dot_main_dot_search__pb2


class SearchStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.CancelChatTask = channel.unary_unary(
                '/bilibili.app.search.v2.Search/CancelChatTask',
                request_serializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.CancelChatTaskReq.SerializeToString,
                response_deserializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.CancelChatTaskReply.FromString,
                )
        self.GetChatAuth = channel.unary_unary(
                '/bilibili.app.search.v2.Search/GetChatAuth',
                request_serializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.GetChatAuthReq.SerializeToString,
                response_deserializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.GetChatAuthReply.FromString,
                )
        self.GetChatResult = channel.unary_unary(
                '/bilibili.app.search.v2.Search/GetChatResult',
                request_serializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.GetChatResultReq.SerializeToString,
                response_deserializer=bilibili_dot_broadcast_dot_message_dot_main_dot_search__pb2.ChatResult.FromString,
                )
        self.QueryRecAfterClick = channel.unary_unary(
                '/bilibili.app.search.v2.Search/QueryRecAfterClick',
                request_serializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.QueryRecAfterClickReq.SerializeToString,
                response_deserializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.QueryRecAfterClickReply.FromString,
                )
        self.SearchEgg = channel.unary_unary(
                '/bilibili.app.search.v2.Search/SearchEgg',
                request_serializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.SearchEggReq.SerializeToString,
                response_deserializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.SearchEggReply.FromString,
                )
        self.SubmitChatTask = channel.unary_unary(
                '/bilibili.app.search.v2.Search/SubmitChatTask',
                request_serializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.SubmitChatTaskReq.SerializeToString,
                response_deserializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.SubmitChatTaskReply.FromString,
                )


class SearchServicer(object):
    """Missing associated documentation comment in .proto file."""

    def CancelChatTask(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetChatAuth(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetChatResult(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def QueryRecAfterClick(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SearchEgg(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SubmitChatTask(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_SearchServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'CancelChatTask': grpc.unary_unary_rpc_method_handler(
                    servicer.CancelChatTask,
                    request_deserializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.CancelChatTaskReq.FromString,
                    response_serializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.CancelChatTaskReply.SerializeToString,
            ),
            'GetChatAuth': grpc.unary_unary_rpc_method_handler(
                    servicer.GetChatAuth,
                    request_deserializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.GetChatAuthReq.FromString,
                    response_serializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.GetChatAuthReply.SerializeToString,
            ),
            'GetChatResult': grpc.unary_unary_rpc_method_handler(
                    servicer.GetChatResult,
                    request_deserializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.GetChatResultReq.FromString,
                    response_serializer=bilibili_dot_broadcast_dot_message_dot_main_dot_search__pb2.ChatResult.SerializeToString,
            ),
            'QueryRecAfterClick': grpc.unary_unary_rpc_method_handler(
                    servicer.QueryRecAfterClick,
                    request_deserializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.QueryRecAfterClickReq.FromString,
                    response_serializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.QueryRecAfterClickReply.SerializeToString,
            ),
            'SearchEgg': grpc.unary_unary_rpc_method_handler(
                    servicer.SearchEgg,
                    request_deserializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.SearchEggReq.FromString,
                    response_serializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.SearchEggReply.SerializeToString,
            ),
            'SubmitChatTask': grpc.unary_unary_rpc_method_handler(
                    servicer.SubmitChatTask,
                    request_deserializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.SubmitChatTaskReq.FromString,
                    response_serializer=bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.SubmitChatTaskReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'bilibili.app.search.v2.Search', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Search(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def CancelChatTask(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bilibili.app.search.v2.Search/CancelChatTask',
            bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.CancelChatTaskReq.SerializeToString,
            bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.CancelChatTaskReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetChatAuth(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bilibili.app.search.v2.Search/GetChatAuth',
            bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.GetChatAuthReq.SerializeToString,
            bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.GetChatAuthReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetChatResult(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bilibili.app.search.v2.Search/GetChatResult',
            bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.GetChatResultReq.SerializeToString,
            bilibili_dot_broadcast_dot_message_dot_main_dot_search__pb2.ChatResult.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def QueryRecAfterClick(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bilibili.app.search.v2.Search/QueryRecAfterClick',
            bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.QueryRecAfterClickReq.SerializeToString,
            bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.QueryRecAfterClickReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SearchEgg(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bilibili.app.search.v2.Search/SearchEgg',
            bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.SearchEggReq.SerializeToString,
            bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.SearchEggReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SubmitChatTask(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bilibili.app.search.v2.Search/SubmitChatTask',
            bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.SubmitChatTaskReq.SerializeToString,
            bilibili_dot_app_dot_search_dot_v2_dot_search__pb2.SubmitChatTaskReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
