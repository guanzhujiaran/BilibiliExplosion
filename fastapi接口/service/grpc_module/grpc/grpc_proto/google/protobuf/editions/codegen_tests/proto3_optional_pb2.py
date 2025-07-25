# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: google/protobuf/editions/codegen_tests/proto3_optional.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='google/protobuf/editions/codegen_tests/proto3_optional.proto',
  package='protobuf_editions_test.proto3',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n<google/protobuf/editions/codegen_tests/proto3_optional.proto\x12\x1dprotobuf_editions_test.proto3\"\xe0\x01\n\x0eProto3Optional\x12\x18\n\x0bint32_field\x18\x01 \x01(\x05H\x00\x88\x01\x01\x12W\n\x10optional_message\x18\x02 \x01(\x0b\x32\x38.protobuf_editions_test.proto3.Proto3Optional.SubMessageH\x01\x88\x01\x01\x1a\x36\n\nSubMessage\x12\x18\n\x0bint32_field\x18\x01 \x01(\x05H\x00\x88\x01\x01\x42\x0e\n\x0c_int32_fieldB\x0e\n\x0c_int32_fieldB\x13\n\x11_optional_messageb\x06proto3'
)




_PROTO3OPTIONAL_SUBMESSAGE = _descriptor.Descriptor(
  name='SubMessage',
  full_name='protobuf_editions_test.proto3.Proto3Optional.SubMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='int32_field', full_name='protobuf_editions_test.proto3.Proto3Optional.SubMessage.int32_field', index=0,
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
    _descriptor.OneofDescriptor(
      name='_int32_field', full_name='protobuf_editions_test.proto3.Proto3Optional.SubMessage._int32_field',
      index=0, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
  ],
  serialized_start=229,
  serialized_end=283,
)

_PROTO3OPTIONAL = _descriptor.Descriptor(
  name='Proto3Optional',
  full_name='protobuf_editions_test.proto3.Proto3Optional',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='int32_field', full_name='protobuf_editions_test.proto3.Proto3Optional.int32_field', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='optional_message', full_name='protobuf_editions_test.proto3.Proto3Optional.optional_message', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[_PROTO3OPTIONAL_SUBMESSAGE, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='_int32_field', full_name='protobuf_editions_test.proto3.Proto3Optional._int32_field',
      index=0, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
    _descriptor.OneofDescriptor(
      name='_optional_message', full_name='protobuf_editions_test.proto3.Proto3Optional._optional_message',
      index=1, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
  ],
  serialized_start=96,
  serialized_end=320,
)

_PROTO3OPTIONAL_SUBMESSAGE.containing_type = _PROTO3OPTIONAL
_PROTO3OPTIONAL_SUBMESSAGE.oneofs_by_name['_int32_field'].fields.append(
  _PROTO3OPTIONAL_SUBMESSAGE.fields_by_name['int32_field'])
_PROTO3OPTIONAL_SUBMESSAGE.fields_by_name['int32_field'].containing_oneof = _PROTO3OPTIONAL_SUBMESSAGE.oneofs_by_name['_int32_field']
_PROTO3OPTIONAL.fields_by_name['optional_message'].message_type = _PROTO3OPTIONAL_SUBMESSAGE
_PROTO3OPTIONAL.oneofs_by_name['_int32_field'].fields.append(
  _PROTO3OPTIONAL.fields_by_name['int32_field'])
_PROTO3OPTIONAL.fields_by_name['int32_field'].containing_oneof = _PROTO3OPTIONAL.oneofs_by_name['_int32_field']
_PROTO3OPTIONAL.oneofs_by_name['_optional_message'].fields.append(
  _PROTO3OPTIONAL.fields_by_name['optional_message'])
_PROTO3OPTIONAL.fields_by_name['optional_message'].containing_oneof = _PROTO3OPTIONAL.oneofs_by_name['_optional_message']
DESCRIPTOR.message_types_by_name['Proto3Optional'] = _PROTO3OPTIONAL
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Proto3Optional = _reflection.GeneratedProtocolMessageType('Proto3Optional', (_message.Message,), {

  'SubMessage' : _reflection.GeneratedProtocolMessageType('SubMessage', (_message.Message,), {
    'DESCRIPTOR' : _PROTO3OPTIONAL_SUBMESSAGE,
    '__module__' : 'google.protobuf.editions.codegen_tests.proto3_optional_pb2'
    # @@protoc_insertion_point(class_scope:protobuf_editions_test.proto3.Proto3Optional.SubMessage)
    })
  ,
  'DESCRIPTOR' : _PROTO3OPTIONAL,
  '__module__' : 'google.protobuf.editions.codegen_tests.proto3_optional_pb2'
  # @@protoc_insertion_point(class_scope:protobuf_editions_test.proto3.Proto3Optional)
  })
_sym_db.RegisterMessage(Proto3Optional)
_sym_db.RegisterMessage(Proto3Optional.SubMessage)


# @@protoc_insertion_point(module_scope)
