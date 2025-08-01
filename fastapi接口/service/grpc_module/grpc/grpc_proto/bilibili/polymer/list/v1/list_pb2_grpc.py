# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

from bilibili.polymer.list.v1 import list_pb2 as bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2

GRPC_GENERATED_VERSION = '1.74.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in bilibili/polymer/list/v1/list_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


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
                _registered_method=True)
        self.CheckAccount = channel.unary_unary(
                '/bilibili.polymer.list.v1.List/CheckAccount',
                request_serializer=bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.CheckAccountReq.SerializeToString,
                response_deserializer=bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.CheckAccountReply.FromString,
                _registered_method=True)


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
    server.add_registered_method_handlers('bilibili.polymer.list.v1.List', rpc_method_handlers)


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
        return grpc.experimental.unary_unary(
            request,
            target,
            '/bilibili.polymer.list.v1.List/FavoriteTab',
            bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.FavoriteTabReq.SerializeToString,
            bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.FavoriteTabReply.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

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
        return grpc.experimental.unary_unary(
            request,
            target,
            '/bilibili.polymer.list.v1.List/CheckAccount',
            bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.CheckAccountReq.SerializeToString,
            bilibili_dot_polymer_dot_list_dot_v1_dot_list__pb2.CheckAccountReply.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
