# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: google/protobuf/editions/codegen_tests/proto2_group.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='google/protobuf/editions/codegen_tests/proto2_group.proto',
  package='protobuf_editions_test.proto2',
  syntax='proto2',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n9google/protobuf/editions/codegen_tests/proto2_group.proto\x12\x1dprotobuf_editions_test.proto2\"{\n\x0bProto2Group\x12I\n\ngroupfield\x18\x02 \x01(\n25.protobuf_editions_test.proto2.Proto2Group.GroupField\x1a!\n\nGroupField\x12\x13\n\x0bint32_field\x18\x01 \x01(\x05'
)




_PROTO2GROUP_GROUPFIELD = _descriptor.Descriptor(
  name='GroupField',
  full_name='protobuf_editions_test.proto2.Proto2Group.GroupField',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='int32_field', full_name='protobuf_editions_test.proto2.Proto2Group.GroupField.int32_field', index=0,
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
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=182,
  serialized_end=215,
)

_PROTO2GROUP = _descriptor.Descriptor(
  name='Proto2Group',
  full_name='protobuf_editions_test.proto2.Proto2Group',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='groupfield', full_name='protobuf_editions_test.proto2.Proto2Group.groupfield', index=0,
      number=2, type=10, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[_PROTO2GROUP_GROUPFIELD, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=92,
  serialized_end=215,
)

_PROTO2GROUP_GROUPFIELD.containing_type = _PROTO2GROUP
_PROTO2GROUP.fields_by_name['groupfield'].message_type = _PROTO2GROUP_GROUPFIELD
DESCRIPTOR.message_types_by_name['Proto2Group'] = _PROTO2GROUP
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Proto2Group = _reflection.GeneratedProtocolMessageType('Proto2Group', (_message.Message,), {

  'GroupField' : _reflection.GeneratedProtocolMessageType('GroupField', (_message.Message,), {
    'DESCRIPTOR' : _PROTO2GROUP_GROUPFIELD,
    '__module__' : 'google.protobuf.editions.codegen_tests.proto2_group_pb2'
    # @@protoc_insertion_point(class_scope:protobuf_editions_test.proto2.Proto2Group.GroupField)
    })
  ,
  'DESCRIPTOR' : _PROTO2GROUP,
  '__module__' : 'google.protobuf.editions.codegen_tests.proto2_group_pb2'
  # @@protoc_insertion_point(class_scope:protobuf_editions_test.proto2.Proto2Group)
  })
_sym_db.RegisterMessage(Proto2Group)
_sym_db.RegisterMessage(Proto2Group.GroupField)


# @@protoc_insertion_point(module_scope)
