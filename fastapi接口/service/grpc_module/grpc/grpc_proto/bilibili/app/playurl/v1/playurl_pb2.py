# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: bilibili/app/playurl/v1/playurl.proto
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
    'bilibili/app/playurl/v1/playurl.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n%bilibili/app/playurl/v1/playurl.proto\x12\x17\x62ilibili.app.playurl.v1\"D\n\x02\x41\x42\x12/\n\x06glance\x18\x01 \x01(\x0b\x32\x1f.bilibili.app.playurl.v1.Glance\x12\r\n\x05group\x18\x02 \x01(\x05\"\x86\x01\n\x07\x41rcConf\x12\x12\n\nis_support\x18\x01 \x01(\x08\x12\x10\n\x08\x64isabled\x18\x02 \x01(\x08\x12<\n\rextra_content\x18\x03 \x01(\x0b\x32%.bilibili.app.playurl.v1.ExtraContent\x12\x17\n\x0funsupport_scene\x18\x04 \x03(\x03\"$\n\x07\x43hronos\x12\x0b\n\x03md5\x18\x01 \x01(\t\x12\x0c\n\x04\x66ile\x18\x02 \x01(\t\"T\n\x0b\x42uttonStyle\x12\x0c\n\x04text\x18\x01 \x01(\t\x12\x12\n\ntext_color\x18\x02 \x01(\t\x12\x10\n\x08\x62g_color\x18\x03 \x01(\t\x12\x11\n\tjump_link\x18\x04 \x01(\t\"\xc1\x01\n\tCloudConf\x12\x0c\n\x04show\x18\x01 \x01(\x08\x12\x34\n\tconf_type\x18\x02 \x01(\x0e\x32!.bilibili.app.playurl.v1.ConfType\x12\x38\n\x0b\x66ield_value\x18\x03 \x01(\x0b\x32#.bilibili.app.playurl.v1.FieldValue\x12\x36\n\nconf_value\x18\x04 \x01(\x0b\x32\".bilibili.app.playurl.v1.ConfValue\"B\n\tConfValue\x12\x14\n\nswitch_val\x18\x01 \x01(\x08H\x00\x12\x16\n\x0cselected_val\x18\x02 \x01(\x03H\x00\x42\x07\n\x05value\"\xa5\x01\n\x08\x44\x61shItem\x12\n\n\x02id\x18\x01 \x01(\r\x12\x0f\n\x07\x62\x61seUrl\x18\x02 \x01(\t\x12\x12\n\nbackup_url\x18\x03 \x03(\t\x12\x11\n\tbandwidth\x18\x04 \x01(\r\x12\x0f\n\x07\x63odecid\x18\x05 \x01(\r\x12\x0b\n\x03md5\x18\x06 \x01(\t\x12\x0c\n\x04size\x18\x07 \x01(\x04\x12\x12\n\nframe_rate\x18\x08 \x01(\t\x12\x15\n\rwidevine_pssh\x18\t \x01(\t\"\xdf\x01\n\tDashVideo\x12\x10\n\x08\x62\x61se_url\x18\x01 \x01(\t\x12\x12\n\nbackup_url\x18\x02 \x03(\t\x12\x11\n\tbandwidth\x18\x03 \x01(\r\x12\x0f\n\x07\x63odecid\x18\x04 \x01(\r\x12\x0b\n\x03md5\x18\x05 \x01(\t\x12\x0c\n\x04size\x18\x06 \x01(\x04\x12\x0f\n\x07\x61udioId\x18\x07 \x01(\r\x12\x12\n\nno_rexcode\x18\x08 \x01(\x08\x12\x12\n\nframe_rate\x18\t \x01(\t\x12\r\n\x05width\x18\n \x01(\x05\x12\x0e\n\x06height\x18\x0b \x01(\x05\x12\x15\n\rwidevine_pssh\x18\x0c \x01(\t\"\x9d\x01\n\tDolbyItem\x12\x35\n\x04type\x18\x01 \x01(\x0e\x32\'.bilibili.app.playurl.v1.DolbyItem.Type\x12\x30\n\x05\x61udio\x18\x02 \x01(\x0b\x32!.bilibili.app.playurl.v1.DashItem\"\'\n\x04Type\x12\x08\n\x04NONE\x10\x00\x12\n\n\x06\x43OMMON\x10\x01\x12\t\n\x05\x41TMOS\x10\x02\"6\n\x05\x45vent\x12-\n\x05shake\x18\x01 \x01(\x0b\x32\x1e.bilibili.app.playurl.v1.Shake\">\n\x0c\x45xtraContent\x12\x17\n\x0f\x64isabled_reason\x18\x01 \x01(\t\x12\x15\n\rdisabled_code\x18\x02 \x01(\x03\"\'\n\nFieldValue\x12\x10\n\x06switch\x18\x01 \x01(\x08H\x00\x42\x07\n\x05value\"\x8d\x01\n\x11\x46ormatDescription\x12\x0f\n\x07quality\x18\x01 \x01(\x05\x12\x0e\n\x06\x66ormat\x18\x02 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x03 \x01(\t\x12\x17\n\x0fnew_description\x18\x04 \x01(\t\x12\x14\n\x0c\x64isplay_desc\x18\x05 \x01(\t\x12\x13\n\x0bsuperscript\x18\x06 \x01(\t\"<\n\x06Glance\x12\x11\n\tcan_watch\x18\x01 \x01(\x08\x12\r\n\x05times\x18\x02 \x01(\x03\x12\x10\n\x08\x64uration\x18\x03 \x01(\x03\"m\n\x0cLossLessItem\x12\x19\n\x11is_lossless_audio\x18\x01 \x01(\x08\x12\x30\n\x05\x61udio\x18\x02 \x01(\x0b\x32!.bilibili.app.playurl.v1.DashItem\x12\x10\n\x08need_vip\x18\x03 \x01(\x08\"\x85\x0e\n\x0fPlayAbilityConf\x12@\n\x14\x62\x61\x63kground_play_conf\x18\x01 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12\x35\n\tflip_conf\x18\x02 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12\x35\n\tcast_conf\x18\x03 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12\x39\n\rfeedback_conf\x18\x04 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12\x39\n\rsubtitle_conf\x18\x05 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12>\n\x12playback_rate_conf\x18\x06 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12\x38\n\x0ctime_up_conf\x18\x07 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12>\n\x12playback_mode_conf\x18\x08 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12;\n\x0fscale_mode_conf\x18\t \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12\x35\n\tlike_conf\x18\n \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12\x38\n\x0c\x64islike_conf\x18\x0b \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12\x35\n\tcoin_conf\x18\x0c \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12\x35\n\telec_conf\x18\r \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12\x36\n\nshare_conf\x18\x0e \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12<\n\x10screen_shot_conf\x18\x0f \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12<\n\x10lock_screen_conf\x18\x10 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12:\n\x0erecommend_conf\x18\x11 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12?\n\x13playback_speed_conf\x18\x12 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12;\n\x0f\x64\x65\x66inition_conf\x18\x13 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12;\n\x0fselections_conf\x18\x14 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12\x35\n\tnext_conf\x18\x15 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12\x38\n\x0c\x65\x64it_dm_conf\x18\x16 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12=\n\x11small_window_conf\x18\x17 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12\x36\n\nshake_conf\x18\x18 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12\x39\n\router_dm_conf\x18\x19 \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12:\n\x0einnerDmDisable\x18\x1a \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12\x39\n\rinner_dm_conf\x18\x1b \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12\x36\n\ndolby_conf\x18\x1c \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12=\n\x11\x63olor_filter_conf\x18\x1d \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\x12:\n\x0eloss_less_conf\x18\x1e \x01(\x0b\x32\".bilibili.app.playurl.v1.CloudConf\"\x85\x0e\n\x0bPlayArcConf\x12>\n\x14\x62\x61\x63kground_play_conf\x18\x01 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x33\n\tflip_conf\x18\x02 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x33\n\tcast_conf\x18\x03 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x37\n\rfeedback_conf\x18\x04 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x37\n\rsubtitle_conf\x18\x05 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12<\n\x12playback_rate_conf\x18\x06 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x36\n\x0ctime_up_conf\x18\x07 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12<\n\x12playback_mode_conf\x18\x08 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x39\n\x0fscale_mode_conf\x18\t \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x33\n\tlike_conf\x18\n \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x36\n\x0c\x64islike_conf\x18\x0b \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x33\n\tcoin_conf\x18\x0c \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x33\n\telec_conf\x18\r \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x34\n\nshare_conf\x18\x0e \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12:\n\x10screen_shot_conf\x18\x0f \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12:\n\x10lock_screen_conf\x18\x10 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x38\n\x0erecommend_conf\x18\x11 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12=\n\x13playback_speed_conf\x18\x12 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x39\n\x0f\x64\x65\x66inition_conf\x18\x13 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x39\n\x0fselections_conf\x18\x14 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x33\n\tnext_conf\x18\x15 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x36\n\x0c\x65\x64it_dm_conf\x18\x16 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12;\n\x11small_window_conf\x18\x17 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x34\n\nshake_conf\x18\x18 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x37\n\router_dm_conf\x18\x19 \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x37\n\rinner_dm_conf\x18\x1a \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x37\n\rpanorama_conf\x18\x1b \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x34\n\ndolby_conf\x18\x1c \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12?\n\x15screen_recording_conf\x18\x1d \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12;\n\x11\x63olor_filter_conf\x18\x1e \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\x12\x38\n\x0eloss_less_conf\x18\x1f \x01(\x0b\x32 .bilibili.app.playurl.v1.ArcConf\"\x13\n\x11PlayConfEditReply\"L\n\x0fPlayConfEditReq\x12\x39\n\tplay_conf\x18\x01 \x03(\x0b\x32&.bilibili.app.playurl.v1.PlayConfState\"L\n\rPlayConfReply\x12;\n\tplay_conf\x18\x01 \x01(\x0b\x32(.bilibili.app.playurl.v1.PlayAbilityConf\"\r\n\x0bPlayConfReq\"\xc5\x01\n\rPlayConfState\x12\x34\n\tconf_type\x18\x01 \x01(\x0e\x32!.bilibili.app.playurl.v1.ConfType\x12\x0c\n\x04show\x18\x02 \x01(\x08\x12\x38\n\x0b\x66ield_value\x18\x03 \x01(\x0b\x32#.bilibili.app.playurl.v1.FieldValue\x12\x36\n\nconf_value\x18\x04 \x01(\x0b\x32\".bilibili.app.playurl.v1.ConfValue\"\x9d\x01\n\tPlayLimit\x12\x34\n\x04\x63ode\x18\x01 \x01(\x0e\x32&.bilibili.app.playurl.v1.PlayLimitCode\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x13\n\x0bsub_message\x18\x03 \x01(\t\x12\x34\n\x06\x62utton\x18\x04 \x01(\x0b\x32$.bilibili.app.playurl.v1.ButtonStyle\"\xc1\x03\n\x0cPlayURLReply\x12\x0f\n\x07quality\x18\x01 \x01(\r\x12\x0e\n\x06\x66ormat\x18\x02 \x01(\t\x12\x12\n\ntimelength\x18\x03 \x01(\x04\x12\x15\n\rvideo_codecid\x18\x04 \x01(\r\x12\r\n\x05\x66nver\x18\x05 \x01(\r\x12\r\n\x05\x66nval\x18\x06 \x01(\r\x12\x15\n\rvideo_project\x18\x07 \x01(\x08\x12\x32\n\x04\x64url\x18\x08 \x03(\x0b\x32$.bilibili.app.playurl.v1.ResponseUrl\x12\x33\n\x04\x64\x61sh\x18\t \x01(\x0b\x32%.bilibili.app.playurl.v1.ResponseDash\x12\x12\n\nno_rexcode\x18\n \x01(\x05\x12<\n\rupgrade_limit\x18\x0b \x01(\x0b\x32%.bilibili.app.playurl.v1.UpgradeLimit\x12\x43\n\x0fsupport_formats\x18\x0c \x03(\x0b\x32*.bilibili.app.playurl.v1.FormatDescription\x12\x30\n\x04type\x18\r \x01(\x0e\x32\".bilibili.app.playurl.v1.VideoType\"\xa8\x01\n\nPlayURLReq\x12\x0b\n\x03\x61id\x18\x01 \x01(\x03\x12\x0b\n\x03\x63id\x18\x02 \x01(\x03\x12\n\n\x02qn\x18\x03 \x01(\x03\x12\r\n\x05\x66nver\x18\x04 \x01(\x05\x12\r\n\x05\x66nval\x18\x05 \x01(\x05\x12\x10\n\x08\x64ownload\x18\x06 \x01(\r\x12\x12\n\nforce_host\x18\x07 \x01(\x05\x12\r\n\x05\x66ourk\x18\x08 \x01(\x08\x12\r\n\x05spmid\x18\t \x01(\t\x12\x12\n\nfrom_spmid\x18\n \x01(\t\"\xbd\x03\n\rPlayViewReply\x12\x36\n\nvideo_info\x18\x01 \x01(\x0b\x32\".bilibili.app.playurl.v1.VideoInfo\x12;\n\tplay_conf\x18\x02 \x01(\x0b\x32(.bilibili.app.playurl.v1.PlayAbilityConf\x12<\n\rupgrade_limit\x18\x03 \x01(\x0b\x32%.bilibili.app.playurl.v1.UpgradeLimit\x12\x31\n\x07\x63hronos\x18\x04 \x01(\x0b\x32 .bilibili.app.playurl.v1.Chronos\x12\x36\n\x08play_arc\x18\x05 \x01(\x0b\x32$.bilibili.app.playurl.v1.PlayArcConf\x12-\n\x05\x65vent\x18\x06 \x01(\x0b\x32\x1e.bilibili.app.playurl.v1.Event\x12\'\n\x02\x61\x62\x18\x07 \x01(\x0b\x32\x1b.bilibili.app.playurl.v1.AB\x12\x36\n\nplay_limit\x18\x08 \x01(\x0b\x32\".bilibili.app.playurl.v1.PlayLimit\"\xcb\x02\n\x0bPlayViewReq\x12\x0b\n\x03\x61id\x18\x01 \x01(\x03\x12\x0b\n\x03\x63id\x18\x02 \x01(\x03\x12\n\n\x02qn\x18\x03 \x01(\x03\x12\r\n\x05\x66nver\x18\x04 \x01(\x05\x12\r\n\x05\x66nval\x18\x05 \x01(\x05\x12\x10\n\x08\x64ownload\x18\x06 \x01(\r\x12\x12\n\nforce_host\x18\x07 \x01(\x05\x12\r\n\x05\x66ourk\x18\x08 \x01(\x08\x12\r\n\x05spmid\x18\t \x01(\t\x12\x12\n\nfrom_spmid\x18\n \x01(\t\x12\x16\n\x0eteenagers_mode\x18\x0b \x01(\x05\x12<\n\x11prefer_codec_type\x18\x0c \x01(\x0e\x32!.bilibili.app.playurl.v1.CodeType\x12\x33\n\x08\x62usiness\x18\r \x01(\x0e\x32!.bilibili.app.playurl.v1.Business\x12\x15\n\rvoice_balance\x18\x0e \x01(\x03\"F\n\x0cProjectReply\x12\x36\n\x07project\x18\x01 \x01(\x0b\x32%.bilibili.app.playurl.v1.PlayURLReply\"\xcf\x01\n\nProjectReq\x12\x0b\n\x03\x61id\x18\x01 \x01(\x03\x12\x0b\n\x03\x63id\x18\x02 \x01(\x03\x12\n\n\x02qn\x18\x03 \x01(\x03\x12\r\n\x05\x66nver\x18\x04 \x01(\x05\x12\r\n\x05\x66nval\x18\x05 \x01(\x05\x12\x10\n\x08\x64ownload\x18\x06 \x01(\r\x12\x12\n\nforce_host\x18\x07 \x01(\x05\x12\r\n\x05\x66ourk\x18\x08 \x01(\x08\x12\r\n\x05spmid\x18\t \x01(\t\x12\x12\n\nfrom_spmid\x18\n \x01(\t\x12\x10\n\x08protocol\x18\x0b \x01(\x05\x12\x13\n\x0b\x64\x65vice_type\x18\x0c \x01(\x05\"r\n\x0cResponseDash\x12\x30\n\x05video\x18\x01 \x03(\x0b\x32!.bilibili.app.playurl.v1.DashItem\x12\x30\n\x05\x61udio\x18\x02 \x03(\x0b\x32!.bilibili.app.playurl.v1.DashItem\"h\n\x0bResponseUrl\x12\r\n\x05order\x18\x01 \x01(\r\x12\x0e\n\x06length\x18\x02 \x01(\x04\x12\x0c\n\x04size\x18\x03 \x01(\x04\x12\x0b\n\x03url\x18\x04 \x01(\t\x12\x12\n\nbackup_url\x18\x05 \x03(\t\x12\x0b\n\x03md5\x18\x06 \x01(\t\"E\n\x0cSegmentVideo\x12\x35\n\x07segment\x18\x01 \x03(\x0b\x32$.bilibili.app.playurl.v1.ResponseUrl\"\x15\n\x05Shake\x12\x0c\n\x04\x66ile\x18\x01 \x01(\t\"\xc7\x01\n\x06Stream\x12\x38\n\x0bstream_info\x18\x01 \x01(\x0b\x32#.bilibili.app.playurl.v1.StreamInfo\x12\x38\n\ndash_video\x18\x02 \x01(\x0b\x32\".bilibili.app.playurl.v1.DashVideoH\x00\x12>\n\rsegment_video\x18\x03 \x01(\x0b\x32%.bilibili.app.playurl.v1.SegmentVideoH\x00\x42\t\n\x07\x63ontent\"\xcc\x02\n\nStreamInfo\x12\x0f\n\x07quality\x18\x01 \x01(\r\x12\x0e\n\x06\x66ormat\x18\x02 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x03 \x01(\t\x12\x32\n\x08\x65rr_code\x18\x04 \x01(\x0e\x32 .bilibili.app.playurl.v1.PlayErr\x12\x33\n\x05limit\x18\x05 \x01(\x0b\x32$.bilibili.app.playurl.v1.StreamLimit\x12\x10\n\x08need_vip\x18\x06 \x01(\x08\x12\x12\n\nneed_login\x18\x07 \x01(\x08\x12\x0e\n\x06intact\x18\x08 \x01(\x08\x12\x12\n\nno_rexcode\x18\t \x01(\x08\x12\x11\n\tattribute\x18\n \x01(\x03\x12\x17\n\x0fnew_description\x18\x0b \x01(\t\x12\x14\n\x0c\x64isplay_desc\x18\x0c \x01(\t\x12\x13\n\x0bsuperscript\x18\r \x01(\t\"6\n\x0bStreamLimit\x12\r\n\x05title\x18\x01 \x01(\t\x12\x0b\n\x03uri\x18\x02 \x01(\t\x12\x0b\n\x03msg\x18\x03 \x01(\t\",\n\rUpgradeButton\x12\r\n\x05title\x18\x01 \x01(\t\x12\x0c\n\x04link\x18\x02 \x01(\t\"t\n\x0cUpgradeLimit\x12\x0c\n\x04\x63ode\x18\x01 \x01(\x05\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\r\n\x05image\x18\x03 \x01(\t\x12\x36\n\x06\x62utton\x18\x04 \x01(\x0b\x32&.bilibili.app.playurl.v1.UpgradeButton\"\xeb\x02\n\tVideoInfo\x12\x0f\n\x07quality\x18\x01 \x01(\r\x12\x0e\n\x06\x66ormat\x18\x02 \x01(\t\x12\x12\n\ntimelength\x18\x03 \x01(\x04\x12\x15\n\rvideo_codecid\x18\x04 \x01(\r\x12\x34\n\x0bstream_list\x18\x05 \x03(\x0b\x32\x1f.bilibili.app.playurl.v1.Stream\x12\x35\n\ndash_audio\x18\x06 \x03(\x0b\x32!.bilibili.app.playurl.v1.DashItem\x12\x31\n\x05\x64olby\x18\x07 \x01(\x0b\x32\".bilibili.app.playurl.v1.DolbyItem\x12\x33\n\x06volume\x18\x08 \x01(\x0b\x32#.bilibili.app.playurl.v1.VolumeInfo\x12=\n\x0eloss_less_item\x18\t \x01(\x0b\x32%.bilibili.app.playurl.v1.LossLessItem\"\xa3\x01\n\nVolumeInfo\x12\x12\n\nmeasured_i\x18\x01 \x01(\x01\x12\x14\n\x0cmeasured_lra\x18\x02 \x01(\x01\x12\x13\n\x0bmeasured_tp\x18\x03 \x01(\x01\x12\x1a\n\x12measured_threshold\x18\x04 \x01(\x01\x12\x15\n\rtarget_offset\x18\x05 \x01(\x01\x12\x10\n\x08target_i\x18\x06 \x01(\x01\x12\x11\n\ttarget_tp\x18\x07 \x01(\x01*\"\n\x08\x42usiness\x12\x0b\n\x07UNKNOWN\x10\x00\x12\t\n\x05STORY\x10\x01*=\n\x08\x43odeType\x12\n\n\x06NOCODE\x10\x00\x12\x0b\n\x07\x43ODE264\x10\x01\x12\x0b\n\x07\x43ODE265\x10\x02\x12\x0b\n\x07\x43ODEAV1\x10\x03*\xbd\x03\n\x08\x43onfType\x12\n\n\x06NoType\x10\x00\x12\x0c\n\x08\x46LIPCONF\x10\x01\x12\x0c\n\x08\x43\x41STCONF\x10\x02\x12\x0c\n\x08\x46\x45\x45\x44\x42\x41\x43K\x10\x03\x12\x0c\n\x08SUBTITLE\x10\x04\x12\x10\n\x0cPLAYBACKRATE\x10\x05\x12\n\n\x06TIMEUP\x10\x06\x12\x10\n\x0cPLAYBACKMODE\x10\x07\x12\r\n\tSCALEMODE\x10\x08\x12\x12\n\x0e\x42\x41\x43KGROUNDPLAY\x10\t\x12\x08\n\x04LIKE\x10\n\x12\x0b\n\x07\x44ISLIKE\x10\x0b\x12\x08\n\x04\x43OIN\x10\x0c\x12\x08\n\x04\x45LEC\x10\r\x12\t\n\x05SHARE\x10\x0e\x12\x0e\n\nSCREENSHOT\x10\x0f\x12\x0e\n\nLOCKSCREEN\x10\x10\x12\r\n\tRECOMMEND\x10\x11\x12\x11\n\rPLAYBACKSPEED\x10\x12\x12\x0e\n\nDEFINITION\x10\x13\x12\x0e\n\nSELECTIONS\x10\x14\x12\x08\n\x04NEXT\x10\x15\x12\n\n\x06\x45\x44ITDM\x10\x16\x12\x0f\n\x0bSMALLWINDOW\x10\x17\x12\t\n\x05SHAKE\x10\x18\x12\x0b\n\x07OUTERDM\x10\x19\x12\x0b\n\x07INNERDM\x10\x1a\x12\x0c\n\x08PANORAMA\x10\x1b\x12\t\n\x05\x44OLBY\x10\x1c\x12\x0f\n\x0b\x43OLORFILTER\x10\x1d\x12\x0c\n\x08LOSSLESS\x10\x1e*.\n\x05Group\x12\x10\n\x0cUnknownGroup\x10\x00\x12\x05\n\x01\x41\x10\x01\x12\x05\n\x01\x42\x10\x02\x12\x05\n\x01\x43\x10\x03*1\n\x07PlayErr\x12\t\n\x05NoErr\x10\x00\x12\x1b\n\x17WithMultiDeviceLoginErr\x10\x01*j\n\rPlayLimitCode\x12\r\n\tPLCUnkown\x10\x00\x12\x12\n\x0ePLCUgcNotPayed\x10\x01\x12\x1a\n\x16PLCChargingPlusNotPass\x10\x02\x12\x1a\n\x16PLCChargingPlusUpgrade\x10\x03*4\n\tVideoType\x12\x0b\n\x07Unknown\x10\x00\x12\x07\n\x03\x46LV\x10\x01\x12\x08\n\x04\x44\x41SH\x10\x02\x12\x07\n\x03MP4\x10\x03\x32\xd1\x03\n\x07PlayURL\x12U\n\x07PlayURL\x12#.bilibili.app.playurl.v1.PlayURLReq\x1a%.bilibili.app.playurl.v1.PlayURLReply\x12U\n\x07Project\x12#.bilibili.app.playurl.v1.ProjectReq\x1a%.bilibili.app.playurl.v1.ProjectReply\x12X\n\x08PlayView\x12$.bilibili.app.playurl.v1.PlayViewReq\x1a&.bilibili.app.playurl.v1.PlayViewReply\x12\x64\n\x0cPlayConfEdit\x12(.bilibili.app.playurl.v1.PlayConfEditReq\x1a*.bilibili.app.playurl.v1.PlayConfEditReply\x12X\n\x08PlayConf\x12$.bilibili.app.playurl.v1.PlayConfReq\x1a&.bilibili.app.playurl.v1.PlayConfReplyb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bilibili.app.playurl.v1.playurl_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_BUSINESS']._serialized_start=9137
  _globals['_BUSINESS']._serialized_end=9171
  _globals['_CODETYPE']._serialized_start=9173
  _globals['_CODETYPE']._serialized_end=9234
  _globals['_CONFTYPE']._serialized_start=9237
  _globals['_CONFTYPE']._serialized_end=9682
  _globals['_GROUP']._serialized_start=9684
  _globals['_GROUP']._serialized_end=9730
  _globals['_PLAYERR']._serialized_start=9732
  _globals['_PLAYERR']._serialized_end=9781
  _globals['_PLAYLIMITCODE']._serialized_start=9783
  _globals['_PLAYLIMITCODE']._serialized_end=9889
  _globals['_VIDEOTYPE']._serialized_start=9891
  _globals['_VIDEOTYPE']._serialized_end=9943
  _globals['_AB']._serialized_start=66
  _globals['_AB']._serialized_end=134
  _globals['_ARCCONF']._serialized_start=137
  _globals['_ARCCONF']._serialized_end=271
  _globals['_CHRONOS']._serialized_start=273
  _globals['_CHRONOS']._serialized_end=309
  _globals['_BUTTONSTYLE']._serialized_start=311
  _globals['_BUTTONSTYLE']._serialized_end=395
  _globals['_CLOUDCONF']._serialized_start=398
  _globals['_CLOUDCONF']._serialized_end=591
  _globals['_CONFVALUE']._serialized_start=593
  _globals['_CONFVALUE']._serialized_end=659
  _globals['_DASHITEM']._serialized_start=662
  _globals['_DASHITEM']._serialized_end=827
  _globals['_DASHVIDEO']._serialized_start=830
  _globals['_DASHVIDEO']._serialized_end=1053
  _globals['_DOLBYITEM']._serialized_start=1056
  _globals['_DOLBYITEM']._serialized_end=1213
  _globals['_DOLBYITEM_TYPE']._serialized_start=1174
  _globals['_DOLBYITEM_TYPE']._serialized_end=1213
  _globals['_EVENT']._serialized_start=1215
  _globals['_EVENT']._serialized_end=1269
  _globals['_EXTRACONTENT']._serialized_start=1271
  _globals['_EXTRACONTENT']._serialized_end=1333
  _globals['_FIELDVALUE']._serialized_start=1335
  _globals['_FIELDVALUE']._serialized_end=1374
  _globals['_FORMATDESCRIPTION']._serialized_start=1377
  _globals['_FORMATDESCRIPTION']._serialized_end=1518
  _globals['_GLANCE']._serialized_start=1520
  _globals['_GLANCE']._serialized_end=1580
  _globals['_LOSSLESSITEM']._serialized_start=1582
  _globals['_LOSSLESSITEM']._serialized_end=1691
  _globals['_PLAYABILITYCONF']._serialized_start=1694
  _globals['_PLAYABILITYCONF']._serialized_end=3491
  _globals['_PLAYARCCONF']._serialized_start=3494
  _globals['_PLAYARCCONF']._serialized_end=5291
  _globals['_PLAYCONFEDITREPLY']._serialized_start=5293
  _globals['_PLAYCONFEDITREPLY']._serialized_end=5312
  _globals['_PLAYCONFEDITREQ']._serialized_start=5314
  _globals['_PLAYCONFEDITREQ']._serialized_end=5390
  _globals['_PLAYCONFREPLY']._serialized_start=5392
  _globals['_PLAYCONFREPLY']._serialized_end=5468
  _globals['_PLAYCONFREQ']._serialized_start=5470
  _globals['_PLAYCONFREQ']._serialized_end=5483
  _globals['_PLAYCONFSTATE']._serialized_start=5486
  _globals['_PLAYCONFSTATE']._serialized_end=5683
  _globals['_PLAYLIMIT']._serialized_start=5686
  _globals['_PLAYLIMIT']._serialized_end=5843
  _globals['_PLAYURLREPLY']._serialized_start=5846
  _globals['_PLAYURLREPLY']._serialized_end=6295
  _globals['_PLAYURLREQ']._serialized_start=6298
  _globals['_PLAYURLREQ']._serialized_end=6466
  _globals['_PLAYVIEWREPLY']._serialized_start=6469
  _globals['_PLAYVIEWREPLY']._serialized_end=6914
  _globals['_PLAYVIEWREQ']._serialized_start=6917
  _globals['_PLAYVIEWREQ']._serialized_end=7248
  _globals['_PROJECTREPLY']._serialized_start=7250
  _globals['_PROJECTREPLY']._serialized_end=7320
  _globals['_PROJECTREQ']._serialized_start=7323
  _globals['_PROJECTREQ']._serialized_end=7530
  _globals['_RESPONSEDASH']._serialized_start=7532
  _globals['_RESPONSEDASH']._serialized_end=7646
  _globals['_RESPONSEURL']._serialized_start=7648
  _globals['_RESPONSEURL']._serialized_end=7752
  _globals['_SEGMENTVIDEO']._serialized_start=7754
  _globals['_SEGMENTVIDEO']._serialized_end=7823
  _globals['_SHAKE']._serialized_start=7825
  _globals['_SHAKE']._serialized_end=7846
  _globals['_STREAM']._serialized_start=7849
  _globals['_STREAM']._serialized_end=8048
  _globals['_STREAMINFO']._serialized_start=8051
  _globals['_STREAMINFO']._serialized_end=8383
  _globals['_STREAMLIMIT']._serialized_start=8385
  _globals['_STREAMLIMIT']._serialized_end=8439
  _globals['_UPGRADEBUTTON']._serialized_start=8441
  _globals['_UPGRADEBUTTON']._serialized_end=8485
  _globals['_UPGRADELIMIT']._serialized_start=8487
  _globals['_UPGRADELIMIT']._serialized_end=8603
  _globals['_VIDEOINFO']._serialized_start=8606
  _globals['_VIDEOINFO']._serialized_end=8969
  _globals['_VOLUMEINFO']._serialized_start=8972
  _globals['_VOLUMEINFO']._serialized_end=9135
  _globals['_PLAYURL']._serialized_start=9946
  _globals['_PLAYURL']._serialized_end=10411
# @@protoc_insertion_point(module_scope)
