# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: bilibili/polymer/list/v1/list.proto
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
    'bilibili/polymer/list/v1/list.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n#bilibili/polymer/list/v1/list.proto\x12\x18\x62ilibili.polymer.list.v1\"#\n\x11\x43heckAccountReply\x12\x0e\n\x06is_new\x18\x01 \x01(\x08\"/\n\x0f\x43heckAccountReq\x12\x0b\n\x03uid\x18\x01 \x01(\x03\x12\x0f\n\x07periods\x18\x02 \x01(\t\":\n\x0f\x46\x61voriteTabItem\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0b\n\x03uri\x18\x02 \x01(\t\x12\x0c\n\x04type\x18\x03 \x01(\t\"L\n\x10\x46\x61voriteTabReply\x12\x38\n\x05items\x18\x01 \x03(\x0b\x32).bilibili.polymer.list.v1.FavoriteTabItem\"\x10\n\x0e\x46\x61voriteTabReq2\xd3\x01\n\x04List\x12\x63\n\x0b\x46\x61voriteTab\x12(.bilibili.polymer.list.v1.FavoriteTabReq\x1a*.bilibili.polymer.list.v1.FavoriteTabReply\x12\x66\n\x0c\x43heckAccount\x12).bilibili.polymer.list.v1.CheckAccountReq\x1a+.bilibili.polymer.list.v1.CheckAccountReplyb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bilibili.polymer.list.v1.list_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_CHECKACCOUNTREPLY']._serialized_start=65
  _globals['_CHECKACCOUNTREPLY']._serialized_end=100
  _globals['_CHECKACCOUNTREQ']._serialized_start=102
  _globals['_CHECKACCOUNTREQ']._serialized_end=149
  _globals['_FAVORITETABITEM']._serialized_start=151
  _globals['_FAVORITETABITEM']._serialized_end=209
  _globals['_FAVORITETABREPLY']._serialized_start=211
  _globals['_FAVORITETABREPLY']._serialized_end=287
  _globals['_FAVORITETABREQ']._serialized_start=289
  _globals['_FAVORITETABREQ']._serialized_end=305
  _globals['_LIST']._serialized_start=308
  _globals['_LIST']._serialized_end=519
# @@protoc_insertion_point(module_scope)
