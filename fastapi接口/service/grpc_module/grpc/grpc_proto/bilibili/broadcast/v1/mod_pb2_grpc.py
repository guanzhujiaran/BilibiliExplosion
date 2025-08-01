# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

from bilibili.broadcast.v1 import mod_pb2 as bilibili_dot_broadcast_dot_v1_dot_mod__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2

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
        + f' but the generated code in bilibili/broadcast/v1/mod_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class ModManagerStub(object):
    """ModManager
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.WatchResource = channel.unary_stream(
                '/bilibili.broadcast.v1.ModManager/WatchResource',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=bilibili_dot_broadcast_dot_v1_dot_mod__pb2.ModResourceResp.FromString,
                _registered_method=True)


class ModManagerServicer(object):
    """ModManager
    """

    def WatchResource(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ModManagerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'WatchResource': grpc.unary_stream_rpc_method_handler(
                    servicer.WatchResource,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=bilibili_dot_broadcast_dot_v1_dot_mod__pb2.ModResourceResp.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'bilibili.broadcast.v1.ModManager', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('bilibili.broadcast.v1.ModManager', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class ModManager(object):
    """ModManager
    """

    @staticmethod
    def WatchResource(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(
            request,
            target,
            '/bilibili.broadcast.v1.ModManager/WatchResource',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            bilibili_dot_broadcast_dot_v1_dot_mod__pb2.ModResourceResp.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
