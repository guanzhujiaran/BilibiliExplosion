# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: bilibili/app/distribution/setting/night.proto
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
    'bilibili/app/distribution/setting/night.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from bilibili.app.distribution.v1 import distribution_pb2 as bilibili_dot_app_dot_distribution_dot_v1_dot_distribution__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n-bilibili/app/distribution/setting/night.proto\x12\'bilibili.app.distribution.setting.night\x1a/bilibili/app/distribution/v1/distribution.proto\"^\n\x13NightSettingsConfig\x12G\n\x16is_night_follow_system\x18\x01 \x01(\x0b\x32\'.bilibili.app.distribution.v1.BoolValueb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bilibili.app.distribution.setting.night_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_NIGHTSETTINGSCONFIG']._serialized_start=139
  _globals['_NIGHTSETTINGSCONFIG']._serialized_end=233
# @@protoc_insertion_point(module_scope)
