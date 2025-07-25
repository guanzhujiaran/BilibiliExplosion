# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from bilibili.app.show.mixture.v1 import mixture_pb2 as bilibili_dot_app_dot_show_dot_mixture_dot_v1_dot_mixture__pb2


class MixtureStub(object):
    """
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Widget = channel.unary_unary(
                '/bilibili.app.show.mixture.v1.Mixture/Widget',
                request_serializer=bilibili_dot_app_dot_show_dot_mixture_dot_v1_dot_mixture__pb2.WidgetReq.SerializeToString,
                response_deserializer=bilibili_dot_app_dot_show_dot_mixture_dot_v1_dot_mixture__pb2.WidgetReply.FromString,
                )


class MixtureServicer(object):
    """
    """

    def Widget(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_MixtureServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Widget': grpc.unary_unary_rpc_method_handler(
                    servicer.Widget,
                    request_deserializer=bilibili_dot_app_dot_show_dot_mixture_dot_v1_dot_mixture__pb2.WidgetReq.FromString,
                    response_serializer=bilibili_dot_app_dot_show_dot_mixture_dot_v1_dot_mixture__pb2.WidgetReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'bilibili.app.show.mixture.v1.Mixture', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Mixture(object):
    """
    """

    @staticmethod
    def Widget(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bilibili.app.show.mixture.v1.Mixture/Widget',
            bilibili_dot_app_dot_show_dot_mixture_dot_v1_dot_mixture__pb2.WidgetReq.SerializeToString,
            bilibili_dot_app_dot_show_dot_mixture_dot_v1_dot_mixture__pb2.WidgetReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
