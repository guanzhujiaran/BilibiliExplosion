# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from bilibili.dynamic.interfaces.campus.v1 import api_pb2 as bilibili_dot_dynamic_dot_interfaces_dot_campus_dot_v1_dot_api__pb2


class CampusStub(object):
    """
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.ActionReport = channel.unary_unary(
                '/bilibili.dynamic.interfaces.campus.v1.Campus/ActionReport',
                request_serializer=bilibili_dot_dynamic_dot_interfaces_dot_campus_dot_v1_dot_api__pb2.ActionReportReq.SerializeToString,
                response_deserializer=bilibili_dot_dynamic_dot_interfaces_dot_campus_dot_v1_dot_api__pb2.ActionReportReply.FromString,
                )


class CampusServicer(object):
    """
    """

    def ActionReport(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_CampusServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'ActionReport': grpc.unary_unary_rpc_method_handler(
                    servicer.ActionReport,
                    request_deserializer=bilibili_dot_dynamic_dot_interfaces_dot_campus_dot_v1_dot_api__pb2.ActionReportReq.FromString,
                    response_serializer=bilibili_dot_dynamic_dot_interfaces_dot_campus_dot_v1_dot_api__pb2.ActionReportReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'bilibili.dynamic.interfaces.campus.v1.Campus', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Campus(object):
    """
    """

    @staticmethod
    def ActionReport(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bilibili.dynamic.interfaces.campus.v1.Campus/ActionReport',
            bilibili_dot_dynamic_dot_interfaces_dot_campus_dot_v1_dot_api__pb2.ActionReportReq.SerializeToString,
            bilibili_dot_dynamic_dot_interfaces_dot_campus_dot_v1_dot_api__pb2.ActionReportReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
