# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from google.protobuf import unittest_custom_options_pb2 as google_dot_protobuf_dot_unittest__custom__options__pb2


class TestServiceWithCustomOptionsStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Foo = channel.unary_unary(
                '/protobuf_unittest.TestServiceWithCustomOptions/Foo',
                request_serializer=google_dot_protobuf_dot_unittest__custom__options__pb2.CustomOptionFooRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_unittest__custom__options__pb2.CustomOptionFooResponse.FromString,
                )


class TestServiceWithCustomOptionsServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Foo(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_TestServiceWithCustomOptionsServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Foo': grpc.unary_unary_rpc_method_handler(
                    servicer.Foo,
                    request_deserializer=google_dot_protobuf_dot_unittest__custom__options__pb2.CustomOptionFooRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_unittest__custom__options__pb2.CustomOptionFooResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'protobuf_unittest.TestServiceWithCustomOptions', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class TestServiceWithCustomOptions(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Foo(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/protobuf_unittest.TestServiceWithCustomOptions/Foo',
            google_dot_protobuf_dot_unittest__custom__options__pb2.CustomOptionFooRequest.SerializeToString,
            google_dot_protobuf_dot_unittest__custom__options__pb2.CustomOptionFooResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class AggregateServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Method = channel.unary_unary(
                '/protobuf_unittest.AggregateService/Method',
                request_serializer=google_dot_protobuf_dot_unittest__custom__options__pb2.AggregateMessage.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_unittest__custom__options__pb2.AggregateMessage.FromString,
                )


class AggregateServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Method(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_AggregateServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Method': grpc.unary_unary_rpc_method_handler(
                    servicer.Method,
                    request_deserializer=google_dot_protobuf_dot_unittest__custom__options__pb2.AggregateMessage.FromString,
                    response_serializer=google_dot_protobuf_dot_unittest__custom__options__pb2.AggregateMessage.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'protobuf_unittest.AggregateService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class AggregateService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Method(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/protobuf_unittest.AggregateService/Method',
            google_dot_protobuf_dot_unittest__custom__options__pb2.AggregateMessage.SerializeToString,
            google_dot_protobuf_dot_unittest__custom__options__pb2.AggregateMessage.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
