# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: bilibili/app/show/popular/v1/popular.proto
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
    'bilibili/app/show/popular/v1/popular.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from bilibili.app.card.v1 import card_pb2 as bilibili_dot_app_dot_card_dot_v1_dot_card__pb2
from bilibili.app.archive.middleware.v1 import preload_pb2 as bilibili_dot_app_dot_archive_dot_middleware_dot_v1_dot_preload__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n*bilibili/app/show/popular/v1/popular.proto\x12\x14\x62ilibili.app.show.v1\x1a\x1f\x62ilibili/app/card/v1/card.proto\x1a\x30\x62ilibili/app/archive/middleware/v1/preload.proto\"@\n\x06\x42ubble\x12\x16\n\x0e\x62ubble_content\x18\x01 \x01(\t\x12\x0f\n\x07version\x18\x02 \x01(\x05\x12\r\n\x05stime\x18\x03 \x01(\x03\"\xf5\x01\n\x06\x43onfig\x12\x12\n\nitem_title\x18\x01 \x01(\t\x12\x13\n\x0b\x62ottom_text\x18\x02 \x01(\t\x12\x19\n\x11\x62ottom_text_cover\x18\x03 \x01(\t\x12\x17\n\x0f\x62ottom_text_url\x18\x04 \x01(\t\x12\x35\n\ttop_items\x18\x05 \x03(\x0b\x32\".bilibili.app.show.v1.EntranceShow\x12\x12\n\nhead_image\x18\x06 \x01(\t\x12\x36\n\npage_items\x18\x07 \x03(\x0b\x32\".bilibili.app.show.v1.EntranceShow\x12\x0b\n\x03hit\x18\x08 \x01(\x05\"\xb8\x01\n\x0c\x45ntranceShow\x12\x0c\n\x04icon\x18\x01 \x01(\t\x12\r\n\x05title\x18\x02 \x01(\t\x12\x11\n\tmodule_id\x18\x03 \x01(\t\x12\x0b\n\x03uri\x18\x04 \x01(\t\x12,\n\x06\x62ubble\x18\x05 \x01(\x0b\x32\x1c.bilibili.app.show.v1.Bubble\x12\x13\n\x0b\x65ntrance_id\x18\x06 \x01(\x03\x12\x11\n\ttop_photo\x18\x07 \x01(\t\x12\x15\n\rentrance_type\x18\x08 \x01(\x05\"t\n\x0cPopularReply\x12)\n\x05items\x18\x01 \x03(\x0b\x32\x1a.bilibili.app.card.v1.Card\x12,\n\x06\x63onfig\x18\x02 \x01(\x0b\x32\x1c.bilibili.app.show.v1.Config\x12\x0b\n\x03ver\x18\x03 \x01(\t\"\xc3\x02\n\x10PopularResultReq\x12\x0b\n\x03idx\x18\x01 \x01(\x03\x12\x13\n\x0blogin_event\x18\x02 \x01(\x05\x12\n\n\x02qn\x18\x03 \x01(\x05\x12\r\n\x05\x66nver\x18\x04 \x01(\x05\x12\r\n\x05\x66nval\x18\x05 \x01(\x05\x12\x12\n\nforce_host\x18\x06 \x01(\x05\x12\r\n\x05\x66ourk\x18\x07 \x01(\x05\x12\r\n\x05spmid\x18\x08 \x01(\t\x12\x12\n\nlast_param\x18\t \x01(\t\x12\x0b\n\x03ver\x18\n \x01(\t\x12\x13\n\x0b\x65ntrance_id\x18\x0b \x01(\x03\x12\x14\n\x0clocation_ids\x18\x0c \x01(\t\x12\x11\n\tsource_id\x18\r \x01(\x05\x12\r\n\x05\x66lush\x18\x0e \x01(\x05\x12\x43\n\x0bplayer_args\x18\x0f \x01(\x0b\x32..bilibili.app.archive.middleware.v1.PlayerArgs2^\n\x07Popular\x12S\n\x05Index\x12&.bilibili.app.show.v1.PopularResultReq\x1a\".bilibili.app.show.v1.PopularReplyb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bilibili.app.show.popular.v1.popular_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_BUBBLE']._serialized_start=151
  _globals['_BUBBLE']._serialized_end=215
  _globals['_CONFIG']._serialized_start=218
  _globals['_CONFIG']._serialized_end=463
  _globals['_ENTRANCESHOW']._serialized_start=466
  _globals['_ENTRANCESHOW']._serialized_end=650
  _globals['_POPULARREPLY']._serialized_start=652
  _globals['_POPULARREPLY']._serialized_end=768
  _globals['_POPULARRESULTREQ']._serialized_start=771
  _globals['_POPULARRESULTREQ']._serialized_end=1094
  _globals['_POPULAR']._serialized_start=1096
  _globals['_POPULAR']._serialized_end=1190
# @@protoc_insertion_point(module_scope)
