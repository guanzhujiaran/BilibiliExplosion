# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: bilibili/broadcast/message/fission/notify.proto
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
    'bilibili/broadcast/message/fission/notify.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n/bilibili/broadcast/message/fission/notify.proto\x12\"bilibili.broadcast.message.fission\x1a\x1bgoogle/protobuf/empty.proto\"-\n\x0fGameNotifyReply\x12\x0c\n\x04type\x18\x01 \x01(\r\x12\x0c\n\x04\x64\x61ta\x18\x02 \x01(\t2f\n\x07\x46ission\x12[\n\nGameNotify\x12\x16.google.protobuf.Empty\x1a\x33.bilibili.broadcast.message.fission.GameNotifyReply0\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bilibili.broadcast.message.fission.notify_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_GAMENOTIFYREPLY']._serialized_start=116
  _globals['_GAMENOTIFYREPLY']._serialized_end=161
  _globals['_FISSION']._serialized_start=163
  _globals['_FISSION']._serialized_end=265
# @@protoc_insertion_point(module_scope)
