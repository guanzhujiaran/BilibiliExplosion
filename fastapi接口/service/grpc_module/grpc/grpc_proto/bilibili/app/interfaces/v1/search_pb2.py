# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: bilibili/app/interfaces/v1/search.proto
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
    'bilibili/app/interfaces/v1/search.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\'bilibili/app/interfaces/v1/search.proto\x12\x19\x62ilibili.app.interface.v1\"\x9e\x01\n\x11\x44\x65\x66\x61ultWordsReply\x12\x0f\n\x07trackid\x18\x01 \x01(\t\x12\r\n\x05param\x18\x02 \x01(\t\x12\x0c\n\x04show\x18\x03 \x01(\t\x12\x0c\n\x04word\x18\x04 \x01(\t\x12\x12\n\nshow_front\x18\x05 \x01(\x03\x12\x0f\n\x07\x65xp_str\x18\x06 \x01(\t\x12\x0c\n\x04goto\x18\x07 \x01(\t\x12\r\n\x05value\x18\x08 \x01(\t\x12\x0b\n\x03uri\x18\t \x01(\t\"E\n\x0bNftFaceIcon\x12\x13\n\x0bregion_type\x18\x01 \x01(\x05\x12\x0c\n\x04icon\x18\x02 \x01(\t\x12\x13\n\x0bshow_status\x18\x03 \x01(\x05\"\xbc\x01\n\x0f\x44\x65\x66\x61ultWordsReq\x12\x0c\n\x04\x66rom\x18\x01 \x01(\x03\x12\x13\n\x0blogin_event\x18\x02 \x01(\x03\x12\x16\n\x0eteenagers_mode\x18\x03 \x01(\x05\x12\x14\n\x0clessons_mode\x18\x04 \x01(\x05\x12\x0b\n\x03tab\x18\x05 \x01(\t\x12\x10\n\x08\x65vent_id\x18\x06 \x01(\t\x12\x0c\n\x04\x61vid\x18\x07 \x01(\t\x12\r\n\x05query\x18\x08 \x01(\t\x12\n\n\x02\x61n\x18\t \x01(\x03\x12\x10\n\x08is_fresh\x18\n \x01(\x03\"o\n\x16SuggestionResult3Reply\x12\x0f\n\x07trackid\x18\x01 \x01(\t\x12\x33\n\x04list\x18\x02 \x03(\x0b\x32%.bilibili.app.interface.v1.ResultItem\x12\x0f\n\x07\x65xp_str\x18\x03 \x01(\t\"R\n\x14SuggestionResult3Req\x12\x0f\n\x07keyword\x18\x01 \x01(\t\x12\x11\n\thighlight\x18\x02 \x01(\x05\x12\x16\n\x0eteenagers_mode\x18\x03 \x01(\x05\"\xf4\x04\n\nResultItem\x12\x0c\n\x04\x66rom\x18\x01 \x01(\t\x12\r\n\x05title\x18\x02 \x01(\t\x12\x0f\n\x07keyword\x18\x03 \x01(\t\x12\x10\n\x08position\x18\x04 \x01(\x05\x12\r\n\x05\x63over\x18\x05 \x01(\t\x12\x12\n\ncover_size\x18\x06 \x01(\x01\x12\x10\n\x08sug_type\x18\x07 \x01(\t\x12\x11\n\tterm_type\x18\x08 \x01(\x05\x12\x0c\n\x04goto\x18\t \x01(\t\x12\x0b\n\x03uri\x18\n \x01(\t\x12\x42\n\x0fofficial_verify\x18\x0b \x01(\x0b\x32).bilibili.app.interface.v1.OfficialVerify\x12\r\n\x05param\x18\x0c \x01(\t\x12\x0b\n\x03mid\x18\r \x01(\x03\x12\x0c\n\x04\x66\x61ns\x18\x0e \x01(\x05\x12\r\n\x05level\x18\x0f \x01(\x05\x12\x10\n\x08\x61rchives\x18\x10 \x01(\x05\x12\r\n\x05ptime\x18\x11 \x01(\x03\x12\x18\n\x10season_type_name\x18\x12 \x01(\t\x12\x0c\n\x04\x61rea\x18\x13 \x01(\t\x12\r\n\x05style\x18\x14 \x01(\t\x12\r\n\x05label\x18\x15 \x01(\t\x12\x0e\n\x06rating\x18\x16 \x01(\x01\x12\x0c\n\x04vote\x18\x17 \x01(\x05\x12\x36\n\x06\x62\x61\x64ges\x18\x18 \x03(\x0b\x32&.bilibili.app.interface.v1.ReasonStyle\x12\x0e\n\x06styles\x18\x19 \x01(\t\x12\x11\n\tmodule_id\x18\x1a \x01(\x03\x12\x11\n\tlive_link\x18\x1b \x01(\t\x12\x14\n\x0c\x66\x61\x63\x65_nft_new\x18\x1c \x01(\x05\x12=\n\rnft_face_icon\x18\x1d \x01(\x0b\x32&.bilibili.app.interface.v1.NftFaceIcon\",\n\x0eOfficialVerify\x12\x0c\n\x04type\x18\x01 \x01(\x05\x12\x0c\n\x04\x64\x65sc\x18\x02 \x01(\t\"\xb7\x01\n\x0bReasonStyle\x12\x0c\n\x04text\x18\x01 \x01(\t\x12\x12\n\ntext_color\x18\x02 \x01(\t\x12\x18\n\x10text_color_night\x18\x03 \x01(\t\x12\x10\n\x08\x62g_color\x18\x04 \x01(\t\x12\x16\n\x0e\x62g_color_night\x18\x05 \x01(\t\x12\x14\n\x0c\x62order_color\x18\x06 \x01(\t\x12\x1a\n\x12\x62order_color_night\x18\x07 \x01(\t\x12\x10\n\x08\x62g_style\x18\x08 \x01(\x05\x32\xe2\x01\n\x06Search\x12n\n\x08Suggest3\x12/.bilibili.app.interface.v1.SuggestionResult3Req\x1a\x31.bilibili.app.interface.v1.SuggestionResult3Reply\x12h\n\x0c\x44\x65\x66\x61ultWords\x12*.bilibili.app.interface.v1.DefaultWordsReq\x1a,.bilibili.app.interface.v1.DefaultWordsReply2|\n\nSearchTest\x12n\n\x08NotExist\x12/.bilibili.app.interface.v1.SuggestionResult3Req\x1a\x31.bilibili.app.interface.v1.SuggestionResult3Replyb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bilibili.app.interfaces.v1.search_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_DEFAULTWORDSREPLY']._serialized_start=71
  _globals['_DEFAULTWORDSREPLY']._serialized_end=229
  _globals['_NFTFACEICON']._serialized_start=231
  _globals['_NFTFACEICON']._serialized_end=300
  _globals['_DEFAULTWORDSREQ']._serialized_start=303
  _globals['_DEFAULTWORDSREQ']._serialized_end=491
  _globals['_SUGGESTIONRESULT3REPLY']._serialized_start=493
  _globals['_SUGGESTIONRESULT3REPLY']._serialized_end=604
  _globals['_SUGGESTIONRESULT3REQ']._serialized_start=606
  _globals['_SUGGESTIONRESULT3REQ']._serialized_end=688
  _globals['_RESULTITEM']._serialized_start=691
  _globals['_RESULTITEM']._serialized_end=1319
  _globals['_OFFICIALVERIFY']._serialized_start=1321
  _globals['_OFFICIALVERIFY']._serialized_end=1365
  _globals['_REASONSTYLE']._serialized_start=1368
  _globals['_REASONSTYLE']._serialized_end=1551
  _globals['_SEARCH']._serialized_start=1554
  _globals['_SEARCH']._serialized_end=1780
  _globals['_SEARCHTEST']._serialized_start=1782
  _globals['_SEARCHTEST']._serialized_end=1906
# @@protoc_insertion_point(module_scope)
