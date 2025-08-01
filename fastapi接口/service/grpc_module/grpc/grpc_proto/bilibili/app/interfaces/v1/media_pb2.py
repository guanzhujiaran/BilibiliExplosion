# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: bilibili/app/interfaces/v1/media.proto
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
    'bilibili/app/interfaces/v1/media.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n&bilibili/app/interfaces/v1/media.proto\x12\x19\x62ilibili.app.interface.v1\"\xc3\x02\n\x07\x42igItem\x12\r\n\x05title\x18\x01 \x01(\t\x12\x17\n\x0f\x63over_image_uri\x18\x02 \x01(\t\x12\x0b\n\x03uri\x18\x03 \x01(\t\x12\x18\n\x10\x63over_right_text\x18\x04 \x01(\t\x12\x18\n\x10\x63over_left_text1\x18\x05 \x01(\t\x12\x18\n\x10\x63over_left_icon1\x18\x06 \x01(\x03\x12\x18\n\x10\x63over_left_text2\x18\x07 \x01(\t\x12\x18\n\x10\x63over_left_icon2\x18\x08 \x01(\x03\x12\x36\n\tuser_card\x18\t \x01(\x0b\x32#.bilibili.app.interface.v1.UserCard\x12:\n\x0blike_button\x18\n \x01(\x0b\x32%.bilibili.app.interface.v1.LikeButton\x12\r\n\x05param\x18\x0b \x01(\x03\"\x9e\x01\n\x06\x42utton\x12\r\n\x05title\x18\x01 \x01(\t\x12\x0c\n\x04link\x18\x02 \x01(\t\x12\n\n\x02id\x18\x03 \x01(\t\x12\x0c\n\x04icon\x18\x04 \x01(\x03\x12\x34\n\x08\x62ut_type\x18\x05 \x01(\x0e\x32\".bilibili.app.interface.v1.ButType\x12\x14\n\x0c\x66ollow_state\x18\x06 \x01(\x05\x12\x11\n\thas_title\x18\x07 \x01(\t\"M\n\x04\x43\x61st\x12\x36\n\x06person\x18\x01 \x03(\x0b\x32&.bilibili.app.interface.v1.MediaPerson\x12\r\n\x05title\x18\x02 \x01(\t\"5\n\x0b\x43hannelInfo\x12\x12\n\nchannel_id\x18\x01 \x01(\x03\x12\x12\n\nsubscribed\x18\x02 \x01(\x08\"\x9b\x03\n\nLikeButton\x12\x0b\n\x03\x61id\x18\x01 \x01(\x03\x12\r\n\x05\x63ount\x18\x02 \x01(\x05\x12\x12\n\nshow_count\x18\x03 \x01(\x08\x12\r\n\x05\x65vent\x18\x04 \x01(\t\x12\x10\n\x08selected\x18\x05 \x01(\x05\x12\x10\n\x08\x65vent_v2\x18\x06 \x01(\t\x12\x44\n\rlike_resource\x18\x07 \x01(\x0b\x32-.bilibili.app.interface.v1.LikeButtonResource\x12H\n\x11\x64is_like_resource\x18\x08 \x01(\x0b\x32-.bilibili.app.interface.v1.LikeButtonResource\x12J\n\x13like_night_resource\x18\t \x01(\x0b\x32-.bilibili.app.interface.v1.LikeButtonResource\x12N\n\x17\x64is_like_night_resource\x18\n \x01(\x0b\x32-.bilibili.app.interface.v1.LikeButtonResource\"/\n\x12LikeButtonResource\x12\x0b\n\x03url\x18\x01 \x01(\t\x12\x0c\n\x04hash\x18\x02 \x01(\t\"+\n\x08LikeCard\x12\x0c\n\x04like\x18\x01 \x01(\x03\x12\x11\n\tis_follow\x18\x02 \x01(\x08\"\x81\x01\n\tMediaCard\x12\r\n\x05\x63over\x18\x01 \x01(\t\x12\x11\n\tcur_title\x18\x02 \x01(\t\x12\r\n\x05style\x18\x03 \x01(\t\x12\r\n\x05label\x18\x04 \x01(\t\x12\x34\n\tbut_first\x18\x05 \x01(\x0b\x32!.bilibili.app.interface.v1.Button\"$\n\x11MediaCommentReply\x12\x0f\n\x07\x65rr_msg\x18\x01 \x01(\t\"\x1d\n\x0fMediaCommentReq\x12\n\n\x02id\x18\x01 \x01(\t\"\xa9\x01\n\x10MediaDetailReply\x12-\n\x04\x63\x61st\x18\x01 \x01(\x0b\x32\x1f.bilibili.app.interface.v1.Cast\x12/\n\x05staff\x18\x02 \x01(\x0b\x32 .bilibili.app.interface.v1.Staff\x12\x35\n\x08overview\x18\x03 \x01(\x0b\x32#.bilibili.app.interface.v1.Overview\"2\n\x0eMediaDetailReq\x12\x0e\n\x06\x62iz_id\x18\x01 \x01(\x03\x12\x10\n\x08\x62iz_type\x18\x02 \x01(\x03\"\x12\n\x10MediaFollowReply\"*\n\x0eMediaFollowReq\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0c\n\x04type\x18\x02 \x01(\x05\"h\n\x0bMediaPerson\x12\x11\n\treal_name\x18\x01 \x01(\t\x12\x12\n\nsquare_url\x18\x02 \x01(\t\x12\x11\n\tcharacter\x18\x03 \x01(\t\x12\x11\n\tperson_id\x18\x04 \x01(\x03\x12\x0c\n\x04type\x18\x05 \x01(\t\"j\n\x12MediaRelationReply\x12\x0e\n\x06offset\x18\x01 \x01(\t\x12\x10\n\x08has_more\x18\x02 \x01(\x08\x12\x32\n\x04list\x18\x03 \x03(\x0b\x32$.bilibili.app.interface.v1.SmallItem\"a\n\x10MediaRelationReq\x12\x0e\n\x06\x62iz_id\x18\x01 \x01(\x03\x12\x10\n\x08\x62iz_type\x18\x02 \x01(\x03\x12\x0f\n\x07\x66\x65\x65\x64_id\x18\x03 \x01(\x03\x12\x0e\n\x06offset\x18\x05 \x01(\t\x12\n\n\x02ps\x18\x06 \x01(\x05\"\xd3\x01\n\rMediaTabReply\x12\x38\n\nmedia_card\x18\x01 \x01(\x0b\x32$.bilibili.app.interface.v1.MediaCard\x12/\n\x03tab\x18\x02 \x03(\x0b\x32\".bilibili.app.interface.v1.ShowTab\x12\x19\n\x11\x64\x65\x66\x61ult_tab_index\x18\x03 \x01(\x03\x12<\n\x0c\x63hannel_info\x18\x04 \x01(\x0b\x32&.bilibili.app.interface.v1.ChannelInfo\"\xbb\x01\n\x0bMediaTabReq\x12\x0e\n\x06\x62iz_id\x18\x01 \x01(\x03\x12\x10\n\x08\x62iz_type\x18\x02 \x01(\x03\x12\x0e\n\x06source\x18\x03 \x01(\t\x12\r\n\x05spmid\x18\x04 \x01(\t\x12>\n\x04\x61rgs\x18\x05 \x03(\x0b\x32\x30.bilibili.app.interface.v1.MediaTabReq.ArgsEntry\x1a+\n\tArgsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"e\n\x0fMediaVideoReply\x12\x0e\n\x06offset\x18\x01 \x01(\t\x12\x10\n\x08has_more\x18\x02 \x01(\x08\x12\x30\n\x04list\x18\x03 \x03(\x0b\x32\".bilibili.app.interface.v1.BigItem\"^\n\rMediaVideoReq\x12\x0e\n\x06\x62iz_id\x18\x01 \x01(\x03\x12\x10\n\x08\x62iz_type\x18\x02 \x01(\x03\x12\x0f\n\x07\x66\x65\x65\x64_id\x18\x03 \x01(\x03\x12\x0e\n\x06offset\x18\x05 \x01(\t\x12\n\n\x02ps\x18\x06 \x01(\x05\"\'\n\x08Overview\x12\r\n\x05title\x18\x01 \x01(\t\x12\x0c\n\x04text\x18\x02 \x01(\t\"[\n\x07ShowTab\x12\x34\n\x08tab_type\x18\x01 \x01(\x0e\x32\".bilibili.app.interface.v1.TabType\x12\r\n\x05title\x18\x02 \x01(\t\x12\x0b\n\x03url\x18\x03 \x01(\t\"\xde\x01\n\tSmallItem\x12\r\n\x05title\x18\x01 \x01(\t\x12\x17\n\x0f\x63over_image_uri\x18\x02 \x01(\t\x12\x0b\n\x03uri\x18\x03 \x01(\t\x12\x18\n\x10\x63over_right_text\x18\x04 \x01(\t\x12\x18\n\x10\x63over_left_text1\x18\x05 \x01(\t\x12\x18\n\x10\x63over_left_icon1\x18\x06 \x01(\x03\x12\x18\n\x10\x63over_left_text2\x18\x07 \x01(\t\x12\x18\n\x10\x63over_left_icon2\x18\x08 \x01(\x03\x12\r\n\x05param\x18\t \x01(\x03\x12\x0b\n\x03mid\x18\n \x01(\x03\"$\n\x05Staff\x12\r\n\x05title\x18\x01 \x01(\t\x12\x0c\n\x04text\x18\x02 \x01(\t\"O\n\x08UserCard\x12\x11\n\tuser_name\x18\x01 \x01(\t\x12\x11\n\tuser_face\x18\x02 \x01(\t\x12\x10\n\x08user_url\x18\x03 \x01(\t\x12\x0b\n\x03mid\x18\x04 \x01(\x03*:\n\x07\x42utType\x12\x0f\n\x0b\x42UT_INVALID\x10\x00\x12\x10\n\x0c\x42UT_REDIRECT\x10\x01\x12\x0c\n\x08\x42UT_LIKE\x10\x02*g\n\x07TabType\x12\x0f\n\x0bTAB_INVALID\x10\x00\x12\x12\n\x0eTAB_OGV_DETAIL\x10\x06\x12\x11\n\rTAB_OGV_REPLY\x10\x07\x12\x10\n\x0cTAB_FEED_BID\x10\x08\x12\x12\n\x0eTAB_FEED_SMALL\x10\t2\xee\x04\n\x05Media\x12h\n\x0cMediaComment\x12*.bilibili.app.interface.v1.MediaCommentReq\x1a,.bilibili.app.interface.v1.MediaCommentReply\x12\x65\n\x0bMediaDetail\x12).bilibili.app.interface.v1.MediaDetailReq\x1a+.bilibili.app.interface.v1.MediaDetailReply\x12\x65\n\x0bMediaFollow\x12).bilibili.app.interface.v1.MediaFollowReq\x1a+.bilibili.app.interface.v1.MediaFollowReply\x12k\n\rMediaRelation\x12+.bilibili.app.interface.v1.MediaRelationReq\x1a-.bilibili.app.interface.v1.MediaRelationReply\x12\\\n\x08MediaTab\x12&.bilibili.app.interface.v1.MediaTabReq\x1a(.bilibili.app.interface.v1.MediaTabReply\x12\x62\n\nMediaVideo\x12(.bilibili.app.interface.v1.MediaVideoReq\x1a*.bilibili.app.interface.v1.MediaVideoReplyb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bilibili.app.interfaces.v1.media_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_MEDIATABREQ_ARGSENTRY']._loaded_options = None
  _globals['_MEDIATABREQ_ARGSENTRY']._serialized_options = b'8\001'
  _globals['_BUTTYPE']._serialized_start=3081
  _globals['_BUTTYPE']._serialized_end=3139
  _globals['_TABTYPE']._serialized_start=3141
  _globals['_TABTYPE']._serialized_end=3244
  _globals['_BIGITEM']._serialized_start=70
  _globals['_BIGITEM']._serialized_end=393
  _globals['_BUTTON']._serialized_start=396
  _globals['_BUTTON']._serialized_end=554
  _globals['_CAST']._serialized_start=556
  _globals['_CAST']._serialized_end=633
  _globals['_CHANNELINFO']._serialized_start=635
  _globals['_CHANNELINFO']._serialized_end=688
  _globals['_LIKEBUTTON']._serialized_start=691
  _globals['_LIKEBUTTON']._serialized_end=1102
  _globals['_LIKEBUTTONRESOURCE']._serialized_start=1104
  _globals['_LIKEBUTTONRESOURCE']._serialized_end=1151
  _globals['_LIKECARD']._serialized_start=1153
  _globals['_LIKECARD']._serialized_end=1196
  _globals['_MEDIACARD']._serialized_start=1199
  _globals['_MEDIACARD']._serialized_end=1328
  _globals['_MEDIACOMMENTREPLY']._serialized_start=1330
  _globals['_MEDIACOMMENTREPLY']._serialized_end=1366
  _globals['_MEDIACOMMENTREQ']._serialized_start=1368
  _globals['_MEDIACOMMENTREQ']._serialized_end=1397
  _globals['_MEDIADETAILREPLY']._serialized_start=1400
  _globals['_MEDIADETAILREPLY']._serialized_end=1569
  _globals['_MEDIADETAILREQ']._serialized_start=1571
  _globals['_MEDIADETAILREQ']._serialized_end=1621
  _globals['_MEDIAFOLLOWREPLY']._serialized_start=1623
  _globals['_MEDIAFOLLOWREPLY']._serialized_end=1641
  _globals['_MEDIAFOLLOWREQ']._serialized_start=1643
  _globals['_MEDIAFOLLOWREQ']._serialized_end=1685
  _globals['_MEDIAPERSON']._serialized_start=1687
  _globals['_MEDIAPERSON']._serialized_end=1791
  _globals['_MEDIARELATIONREPLY']._serialized_start=1793
  _globals['_MEDIARELATIONREPLY']._serialized_end=1899
  _globals['_MEDIARELATIONREQ']._serialized_start=1901
  _globals['_MEDIARELATIONREQ']._serialized_end=1998
  _globals['_MEDIATABREPLY']._serialized_start=2001
  _globals['_MEDIATABREPLY']._serialized_end=2212
  _globals['_MEDIATABREQ']._serialized_start=2215
  _globals['_MEDIATABREQ']._serialized_end=2402
  _globals['_MEDIATABREQ_ARGSENTRY']._serialized_start=2359
  _globals['_MEDIATABREQ_ARGSENTRY']._serialized_end=2402
  _globals['_MEDIAVIDEOREPLY']._serialized_start=2404
  _globals['_MEDIAVIDEOREPLY']._serialized_end=2505
  _globals['_MEDIAVIDEOREQ']._serialized_start=2507
  _globals['_MEDIAVIDEOREQ']._serialized_end=2601
  _globals['_OVERVIEW']._serialized_start=2603
  _globals['_OVERVIEW']._serialized_end=2642
  _globals['_SHOWTAB']._serialized_start=2644
  _globals['_SHOWTAB']._serialized_end=2735
  _globals['_SMALLITEM']._serialized_start=2738
  _globals['_SMALLITEM']._serialized_end=2960
  _globals['_STAFF']._serialized_start=2962
  _globals['_STAFF']._serialized_end=2998
  _globals['_USERCARD']._serialized_start=3000
  _globals['_USERCARD']._serialized_end=3079
  _globals['_MEDIA']._serialized_start=3247
  _globals['_MEDIA']._serialized_end=3869
# @@protoc_insertion_point(module_scope)
