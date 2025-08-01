# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

from bilibili.app.interfaces.v1 import space_pb2 as bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2

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
        + f' but the generated code in bilibili/app/interfaces/v1/space_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class SpaceStub(object):
    """
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.SearchTab = channel.unary_unary(
                '/bilibili.app.interface.v1.Space/SearchTab',
                request_serializer=bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchTabReq.SerializeToString,
                response_deserializer=bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchTabReply.FromString,
                _registered_method=True)
        self.SearchArchive = channel.unary_unary(
                '/bilibili.app.interface.v1.Space/SearchArchive',
                request_serializer=bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchArchiveReq.SerializeToString,
                response_deserializer=bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchArchiveReply.FromString,
                _registered_method=True)
        self.SearchDynamic = channel.unary_unary(
                '/bilibili.app.interface.v1.Space/SearchDynamic',
                request_serializer=bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchDynamicReq.SerializeToString,
                response_deserializer=bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchDynamicReply.FromString,
                _registered_method=True)


class SpaceServicer(object):
    """
    """

    def SearchTab(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SearchArchive(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SearchDynamic(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_SpaceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'SearchTab': grpc.unary_unary_rpc_method_handler(
                    servicer.SearchTab,
                    request_deserializer=bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchTabReq.FromString,
                    response_serializer=bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchTabReply.SerializeToString,
            ),
            'SearchArchive': grpc.unary_unary_rpc_method_handler(
                    servicer.SearchArchive,
                    request_deserializer=bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchArchiveReq.FromString,
                    response_serializer=bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchArchiveReply.SerializeToString,
            ),
            'SearchDynamic': grpc.unary_unary_rpc_method_handler(
                    servicer.SearchDynamic,
                    request_deserializer=bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchDynamicReq.FromString,
                    response_serializer=bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchDynamicReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'bilibili.app.interface.v1.Space', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('bilibili.app.interface.v1.Space', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class Space(object):
    """
    """

    @staticmethod
    def SearchTab(request,
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
            '/bilibili.app.interface.v1.Space/SearchTab',
            bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchTabReq.SerializeToString,
            bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchTabReply.FromString,
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
    def SearchArchive(request,
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
            '/bilibili.app.interface.v1.Space/SearchArchive',
            bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchArchiveReq.SerializeToString,
            bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchArchiveReply.FromString,
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
    def SearchDynamic(request,
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
            '/bilibili.app.interface.v1.Space/SearchDynamic',
            bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchDynamicReq.SerializeToString,
            bilibili_dot_app_dot_interfaces_dot_v1_dot_space__pb2.SearchDynamicReply.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
