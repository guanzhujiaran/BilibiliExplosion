# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: google/protobuf/editions/codegen_tests/proto3_implicit.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='google/protobuf/editions/codegen_tests/proto3_implicit.proto',
  package='protobuf_editions_test.proto3',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n<google/protobuf/editions/codegen_tests/proto3_implicit.proto\x12\x1dprotobuf_editions_test.proto3\"\x97\x01\n\x0eProto3Implicit\x12\x13\n\x0bint32_field\x18\x01 \x01(\x05\x12M\n\x0bsub_message\x18\x02 \x01(\x0b\x32\x38.protobuf_editions_test.proto3.Proto3Implicit.SubMessage\x1a!\n\nSubMessage\x12\x13\n\x0bint32_field\x18\x01 \x01(\x05\x62\x06proto3'
)




_PROTO3IMPLICIT_SUBMESSAGE = _descriptor.Descriptor(
  name='SubMessage',
  full_name='protobuf_editions_test.proto3.Proto3Implicit.SubMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='int32_field', full_name='protobuf_editions_test.proto3.Proto3Implicit.SubMessage.int32_field', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=214,
  serialized_end=247,
)

_PROTO3IMPLICIT = _descriptor.Descriptor(
  name='Proto3Implicit',
  full_name='protobuf_editions_test.proto3.Proto3Implicit',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='int32_field', full_name='protobuf_editions_test.proto3.Proto3Implicit.int32_field', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='sub_message', full_name='protobuf_editions_test.proto3.Proto3Implicit.sub_message', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[_PROTO3IMPLICIT_SUBMESSAGE, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=96,
  serialized_end=247,
)

_PROTO3IMPLICIT_SUBMESSAGE.containing_type = _PROTO3IMPLICIT
_PROTO3IMPLICIT.fields_by_name['sub_message'].message_type = _PROTO3IMPLICIT_SUBMESSAGE
DESCRIPTOR.message_types_by_name['Proto3Implicit'] = _PROTO3IMPLICIT
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Proto3Implicit = _reflection.GeneratedProtocolMessageType('Proto3Implicit', (_message.Message,), {

  'SubMessage' : _reflection.GeneratedProtocolMessageType('SubMessage', (_message.Message,), {
    'DESCRIPTOR' : _PROTO3IMPLICIT_SUBMESSAGE,
    '__module__' : 'google.protobuf.editions.codegen_tests.proto3_implicit_pb2'
    # @@protoc_insertion_point(class_scope:protobuf_editions_test.proto3.Proto3Implicit.SubMessage)
    })
  ,
  'DESCRIPTOR' : _PROTO3IMPLICIT,
  '__module__' : 'google.protobuf.editions.codegen_tests.proto3_implicit_pb2'
  # @@protoc_insertion_point(class_scope:protobuf_editions_test.proto3.Proto3Implicit)
  })
_sym_db.RegisterMessage(Proto3Implicit)
_sym_db.RegisterMessage(Proto3Implicit.SubMessage)


# @@protoc_insertion_point(module_scope)
