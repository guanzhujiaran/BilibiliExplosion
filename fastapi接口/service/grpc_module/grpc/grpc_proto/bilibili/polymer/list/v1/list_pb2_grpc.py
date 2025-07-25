# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from bilibili.polymer.list.v1 import list_pb2 as bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2


class ListStub(object):
    """
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.FavoriteTab = channel.unary_unary(
                '/bilibili.polymer.list.v1.List/FavoriteTab',
                request_serializer=bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.FavoriteTabReq.SerializeToString,
                response_deserializer=bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.FavoriteTabReply.FromString,
                )
        self.CheckAccount = channel.unary_unary(
                '/bilibili.polymer.list.v1.List/CheckAccount',
                request_serializer=bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.CheckAccountReq.SerializeToString,
                response_deserializer=bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.CheckAccountReply.FromString,
                )


class ListServicer(object):
    """
    """

    def FavoriteTab(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CheckAccount(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ListServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'FavoriteTab': grpc.unary_unary_rpc_method_handler(
                    servicer.FavoriteTab,
                    request_deserializer=bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.FavoriteTabReq.FromString,
                    response_serializer=bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.FavoriteTabReply.SerializeToString,
            ),
            'CheckAccount': grpc.unary_unary_rpc_method_handler(
                    servicer.CheckAccount,
                    request_deserializer=bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.CheckAccountReq.FromString,
                    response_serializer=bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.CheckAccountReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'bilibili.polymer.list.v1.List', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class List(object):
    """
    """

    @staticmethod
    def FavoriteTab(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bilibili.polymer.list.v1.List/FavoriteTab',
            bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.FavoriteTabReq.SerializeToString,
            bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.FavoriteTabReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CheckAccount(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bilibili.polymer.list.v1.List/CheckAccount',
            bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.CheckAccountReq.SerializeToString,
            bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.CheckAccountReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
