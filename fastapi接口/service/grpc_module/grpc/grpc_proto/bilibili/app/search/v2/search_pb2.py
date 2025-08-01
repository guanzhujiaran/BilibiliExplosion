# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: bilibili/app/search/v2/search.proto
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
    'bilibili/app/search/v2/search.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from bilibili.broadcast.message.main import search_pb2 as bilibili_dot_broadcast_dot_message_dot_main_dot_search__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n#bilibili/app/search/v2/search.proto\x12\x16\x62ilibili.app.search.v2\x1a,bilibili/broadcast/message/main/search.proto\"<\n\x11\x43\x61ncelChatTaskReq\x12\x12\n\nsession_id\x18\x01 \x01(\t\x12\x13\n\x0b\x66rom_source\x18\x02 \x01(\t\"#\n\x13\x43\x61ncelChatTaskReply\x12\x0c\n\x04\x63ode\x18\x01 \x01(\x05\"\x10\n\x0eGetChatAuthReq\"\x84\x01\n\x10GetChatAuthReply\x12\x0f\n\x07\x64isplay\x18\x01 \x01(\x08\x12\x0c\n\x04icon\x18\x02 \x01(\t\x12\x12\n\nicon_night\x18\x03 \x01(\t\x12\x11\n\tjump_link\x18\x04 \x01(\t\x12\x12\n\ntext_guide\x18\x05 \x01(\t\x12\x16\n\x0ejump_link_type\x18\x06 \x01(\x05\"\\\n\x10GetChatResultReq\x12\r\n\x05query\x18\x01 \x01(\t\x12\x12\n\nsession_id\x18\x02 \x01(\t\x12\x13\n\x0b\x66rom_source\x18\x03 \x01(\t\x12\x10\n\x08track_id\x18\x04 \x01(\t\"\x87\x01\n\x16QueryRecAfterClickItem\x12\x11\n\tshow_name\x18\x01 \x01(\t\x12\x18\n\x10recommend_reason\x18\x02 \x01(\t\x12\x11\n\ticon_type\x18\x03 \x01(\x05\x12\x0b\n\x03url\x18\x04 \x01(\t\x12\x0c\n\x04icon\x18\x05 \x01(\t\x12\x12\n\nicon_night\x18\x06 \x01(\t\"s\n\x17QueryRecAfterClickReply\x12\x0c\n\x04\x63ode\x18\x01 \x01(\x05\x12J\n\x10query_rec_result\x18\x02 \x01(\x0b\x32\x30.bilibili.app.search.v2.QueryRecAfterClickResult\"\x8d\x01\n\x15QueryRecAfterClickReq\x12\r\n\x05param\x18\x01 \x01(\t\x12\x0b\n\x03pos\x18\x02 \x01(\x05\x12\x10\n\x08track_id\x18\x03 \x01(\t\x12\r\n\x05qv_id\x18\x04 \x01(\t\x12\x0f\n\x07keyword\x18\x05 \x01(\t\x12\x11\n\tclick_url\x18\x06 \x01(\t\x12\x13\n\x0b\x66rom_source\x18\x07 \x01(\t\"\xcb\x01\n\x18QueryRecAfterClickResult\x12\x46\n\x0equery_rec_list\x18\x01 \x03(\x0b\x32..bilibili.app.search.v2.QueryRecAfterClickItem\x12\x15\n\rrelated_title\x18\x02 \x01(\t\x12\r\n\x05param\x18\x03 \x01(\t\x12\x0c\n\x04goto\x18\x04 \x01(\t\x12\x10\n\x08linktype\x18\x05 \x01(\t\x12\x10\n\x08position\x18\x06 \x01(\x05\x12\x0f\n\x07trackid\x18\x07 \x01(\t\"\xf2\x01\n\rSearchEggInfo\x12\x10\n\x08\x65gg_type\x18\x01 \x01(\x05\x12\n\n\x02id\x18\x02 \x01(\x03\x12\x15\n\ris_commercial\x18\x03 \x01(\x05\x12\x12\n\nmask_color\x18\x04 \x01(\t\x12\x19\n\x11mask_transparency\x18\x05 \x01(\x03\x12\x0b\n\x03md5\x18\x06 \x01(\t\x12\x0f\n\x07re_type\x18\x07 \x01(\x05\x12\x0e\n\x06re_url\x18\x08 \x01(\t\x12\x10\n\x08re_value\x18\t \x01(\t\x12\x12\n\nshow_count\x18\n \x01(\x05\x12\x0c\n\x04size\x18\x0b \x01(\x03\x12\x0e\n\x06source\x18\x0c \x01(\x03\x12\x0b\n\x03url\x18\r \x01(\t\"I\n\x0eSearchEggInfos\x12\x37\n\x08\x65gg_info\x18\x01 \x03(\x0b\x32%.bilibili.app.search.v2.SearchEggInfo\"d\n\x0eSearchEggReply\x12\x0c\n\x04\x63ode\x18\x01 \x01(\x05\x12\x0c\n\x04seid\x18\x02 \x01(\t\x12\x36\n\x06result\x18\x03 \x01(\x0b\x32&.bilibili.app.search.v2.SearchEggInfos\"\x0e\n\x0cSearchEggReq\"7\n\x13SubmitChatTaskReply\x12\x0c\n\x04\x63ode\x18\x01 \x01(\x05\x12\x12\n\nsession_id\x18\x02 \x01(\t\"I\n\x11SubmitChatTaskReq\x12\r\n\x05query\x18\x01 \x01(\t\x12\x10\n\x08track_id\x18\x02 \x01(\t\x12\x13\n\x0b\x66rom_source\x18\x03 \x01(\t2\xf6\x04\n\x06Search\x12h\n\x0e\x43\x61ncelChatTask\x12).bilibili.app.search.v2.CancelChatTaskReq\x1a+.bilibili.app.search.v2.CancelChatTaskReply\x12_\n\x0bGetChatAuth\x12&.bilibili.app.search.v2.GetChatAuthReq\x1a(.bilibili.app.search.v2.GetChatAuthReply\x12\x66\n\rGetChatResult\x12(.bilibili.app.search.v2.GetChatResultReq\x1a+.bilibili.broadcast.message.main.ChatResult\x12t\n\x12QueryRecAfterClick\x12-.bilibili.app.search.v2.QueryRecAfterClickReq\x1a/.bilibili.app.search.v2.QueryRecAfterClickReply\x12Y\n\tSearchEgg\x12$.bilibili.app.search.v2.SearchEggReq\x1a&.bilibili.app.search.v2.SearchEggReply\x12h\n\x0eSubmitChatTask\x12).bilibili.app.search.v2.SubmitChatTaskReq\x1a+.bilibili.app.search.v2.SubmitChatTaskReplyb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bilibili.app.search.v2.search_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_CANCELCHATTASKREQ']._serialized_start=109
  _globals['_CANCELCHATTASKREQ']._serialized_end=169
  _globals['_CANCELCHATTASKREPLY']._serialized_start=171
  _globals['_CANCELCHATTASKREPLY']._serialized_end=206
  _globals['_GETCHATAUTHREQ']._serialized_start=208
  _globals['_GETCHATAUTHREQ']._serialized_end=224
  _globals['_GETCHATAUTHREPLY']._serialized_start=227
  _globals['_GETCHATAUTHREPLY']._serialized_end=359
  _globals['_GETCHATRESULTREQ']._serialized_start=361
  _globals['_GETCHATRESULTREQ']._serialized_end=453
  _globals['_QUERYRECAFTERCLICKITEM']._serialized_start=456
  _globals['_QUERYRECAFTERCLICKITEM']._serialized_end=591
  _globals['_QUERYRECAFTERCLICKREPLY']._serialized_start=593
  _globals['_QUERYRECAFTERCLICKREPLY']._serialized_end=708
  _globals['_QUERYRECAFTERCLICKREQ']._serialized_start=711
  _globals['_QUERYRECAFTERCLICKREQ']._serialized_end=852
  _globals['_QUERYRECAFTERCLICKRESULT']._serialized_start=855
  _globals['_QUERYRECAFTERCLICKRESULT']._serialized_end=1058
  _globals['_SEARCHEGGINFO']._serialized_start=1061
  _globals['_SEARCHEGGINFO']._serialized_end=1303
  _globals['_SEARCHEGGINFOS']._serialized_start=1305
  _globals['_SEARCHEGGINFOS']._serialized_end=1378
  _globals['_SEARCHEGGREPLY']._serialized_start=1380
  _globals['_SEARCHEGGREPLY']._serialized_end=1480
  _globals['_SEARCHEGGREQ']._serialized_start=1482
  _globals['_SEARCHEGGREQ']._serialized_end=1496
  _globals['_SUBMITCHATTASKREPLY']._serialized_start=1498
  _globals['_SUBMITCHATTASKREPLY']._serialized_end=1553
  _globals['_SUBMITCHATTASKREQ']._serialized_start=1555
  _globals['_SUBMITCHATTASKREQ']._serialized_end=1628
  _globals['_SEARCH']._serialized_start=1631
  _globals['_SEARCH']._serialized_end=2261
# @@protoc_insertion_point(module_scope)
