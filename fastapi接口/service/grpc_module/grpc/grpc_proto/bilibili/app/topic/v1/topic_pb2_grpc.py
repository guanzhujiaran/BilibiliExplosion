# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

from bilibili.app.topic.v1 import topic_pb2 as bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2

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
        + f' but the generated code in bilibili/app/topic/v1/topic_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class TopicStub(object):
    """
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.TopicDetailsAll = channel.unary_unary(
                '/bilibili.app.topic.v1.Topic/TopicDetailsAll',
                request_serializer=bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicDetailsAllReq.SerializeToString,
                response_deserializer=bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicDetailsAllReply.FromString,
                _registered_method=True)
        self.TopicDetailsFold = channel.unary_unary(
                '/bilibili.app.topic.v1.Topic/TopicDetailsFold',
                request_serializer=bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicDetailsFoldReq.SerializeToString,
                response_deserializer=bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicDetailsFoldReply.FromString,
                _registered_method=True)
        self.TopicSetDetails = channel.unary_unary(
                '/bilibili.app.topic.v1.Topic/TopicSetDetails',
                request_serializer=bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicSetDetailsReq.SerializeToString,
                response_deserializer=bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicSetDetailsReply.FromString,
                _registered_method=True)


class TopicServicer(object):
    """
    """

    def TopicDetailsAll(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def TopicDetailsFold(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def TopicSetDetails(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_TopicServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'TopicDetailsAll': grpc.unary_unary_rpc_method_handler(
                    servicer.TopicDetailsAll,
                    request_deserializer=bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicDetailsAllReq.FromString,
                    response_serializer=bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicDetailsAllReply.SerializeToString,
            ),
            'TopicDetailsFold': grpc.unary_unary_rpc_method_handler(
                    servicer.TopicDetailsFold,
                    request_deserializer=bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicDetailsFoldReq.FromString,
                    response_serializer=bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicDetailsFoldReply.SerializeToString,
            ),
            'TopicSetDetails': grpc.unary_unary_rpc_method_handler(
                    servicer.TopicSetDetails,
                    request_deserializer=bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicSetDetailsReq.FromString,
                    response_serializer=bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicSetDetailsReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'bilibili.app.topic.v1.Topic', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('bilibili.app.topic.v1.Topic', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class Topic(object):
    """
    """

    @staticmethod
    def TopicDetailsAll(request,
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
            '/bilibili.app.topic.v1.Topic/TopicDetailsAll',
            bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicDetailsAllReq.SerializeToString,
            bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicDetailsAllReply.FromString,
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
    def TopicDetailsFold(request,
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
            '/bilibili.app.topic.v1.Topic/TopicDetailsFold',
            bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicDetailsFoldReq.SerializeToString,
            bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicDetailsFoldReply.FromString,
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
    def TopicSetDetails(request,
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
            '/bilibili.app.topic.v1.Topic/TopicSetDetails',
            bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicSetDetailsReq.SerializeToString,
            bilibili_dot_app_dot_topic_dot_v1_dot_topic__pb2.TopicSetDetailsReply.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
