# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: bilibili/broadcast/message/main/resource.proto
# Protobuf Python Version: 6.31.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    6,
    31,
    1,
    '',
    'bilibili/broadcast/message/main/resource.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n.bilibili/broadcast/message/main/resource.proto\x12\x1f\x62ilibili.broadcast.message.main\x1a\x1bgoogle/protobuf/empty.proto\"\\\n\x10TopActivityReply\x12:\n\x06online\x18\x01 \x01(\x0b\x32*.bilibili.broadcast.message.main.TopOnline\x12\x0c\n\x04hash\x18\x02 \x01(\t\"\xdc\x01\n\tTopOnline\x12\x0c\n\x04type\x18\x01 \x01(\x05\x12\x0c\n\x04icon\x18\x02 \x01(\t\x12\x0b\n\x03uri\x18\x03 \x01(\t\x12\x11\n\tunique_id\x18\x04 \x01(\t\x12\x39\n\x07\x61nimate\x18\x05 \x01(\x0b\x32(.bilibili.broadcast.message.main.Animate\x12\x38\n\x07red_dot\x18\x06 \x01(\x0b\x32\'.bilibili.broadcast.message.main.RedDot\x12\x0c\n\x04name\x18\x07 \x01(\t\x12\x10\n\x08interval\x18\x08 \x01(\x03\"@\n\x07\x41nimate\x12\x0c\n\x04icon\x18\x01 \x01(\t\x12\x0c\n\x04json\x18\x02 \x01(\t\x12\x0b\n\x03svg\x18\x03 \x01(\t\x12\x0c\n\x04loop\x18\x04 \x01(\x05\"&\n\x06RedDot\x12\x0c\n\x04type\x18\x01 \x01(\x05\x12\x0e\n\x06number\x18\x02 \x01(\x05\x32\x66\n\x08Resource\x12Z\n\x0bTopActivity\x12\x16.google.protobuf.Empty\x1a\x31.bilibili.broadcast.message.main.TopActivityReply0\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bilibili.broadcast.message.main.resource_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_TOPACTIVITYREPLY']._serialized_start=112
  _globals['_TOPACTIVITYREPLY']._serialized_end=204
  _globals['_TOPONLINE']._serialized_start=207
  _globals['_TOPONLINE']._serialized_end=427
  _globals['_ANIMATE']._serialized_start=429
  _globals['_ANIMATE']._serialized_end=493
  _globals['_REDDOT']._serialized_start=495
  _globals['_REDDOT']._serialized_end=533
  _globals['_RESOURCE']._serialized_start=535
  _globals['_RESOURCE']._serialized_end=637
# @@protoc_insertion_point(module_scope)
