# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: bilibili/dynamic/common/dynamic.proto
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
    'bilibili/dynamic/common/dynamic.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from bilibili.app.dynamic.v2 import dynamic_pb2 as bilibili_dot_app_dot_dynamic_dot_v2_dot_dynamic__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n%bilibili/dynamic/common/dynamic.proto\x12\x17\x62ilibili.dynamic.common\x1a%bilibili/app/dynamic/v2/dynamic.proto\"\x97\x01\n\x07\x41rticle\x12\x13\n\x0b\x63\x61tegory_id\x18\x01 \x01(\x03\x12\x0f\n\x07list_id\x18\x02 \x01(\x03\x12\x13\n\x0boriginality\x18\x03 \x01(\x05\x12\x12\n\nreproduced\x18\x04 \x01(\x05\x12+\n\x05\x63over\x18\x05 \x03(\x0b\x32\x1c.bilibili.dynamic.common.Pic\x12\x10\n\x08\x62iz_tags\x18\x06 \x03(\t\"\x87\x01\n\x07\x41tGroup\x12\x38\n\ngroup_type\x18\x01 \x01(\x0e\x32$.bilibili.dynamic.common.AtGroupType\x12\x12\n\ngroup_name\x18\x02 \x01(\t\x12.\n\x05items\x18\x03 \x03(\x0b\x32\x1f.bilibili.dynamic.common.AtItem\"]\n\x06\x41tItem\x12\x0b\n\x03uid\x18\x01 \x01(\x03\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x0c\n\x04\x66\x61\x63\x65\x18\x03 \x01(\t\x12\x0c\n\x04\x66\x61ns\x18\x04 \x01(\x05\x12\x1c\n\x14official_verify_type\x18\x05 \x01(\x05\"\x18\n\tAtListReq\x12\x0b\n\x03uid\x18\x01 \x01(\x03\"=\n\tAtListRsp\x12\x30\n\x06groups\x18\x01 \x03(\x0b\x32 .bilibili.dynamic.common.AtGroup\"+\n\x0b\x41tSearchReq\x12\x0b\n\x03uid\x18\x01 \x01(\x03\x12\x0f\n\x07keyword\x18\x02 \x01(\t\"+\n\x0e\x42ottomBusiness\x12\x0b\n\x03rid\x18\x01 \x01(\x03\x12\x0c\n\x04type\x18\x02 \x01(\x03\"V\n\rCardParagraph\x12/\n\x04\x63\x61rd\x18\x01 \x01(\x0b\x32!.bilibili.dynamic.common.LinkNode\x12\x14\n\x0c\x64\x65\x66\x61ult_text\x18\x02 \x01(\t\".\n\rCodeParagraph\x12\x0c\n\x04lang\x18\x01 \x01(\t\x12\x0f\n\x07\x63ontent\x18\x02 \x01(\t\"0\n\x06\x43olors\x12\x11\n\tcolor_day\x18\x01 \x01(\t\x12\x13\n\x0b\x63olor_night\x18\x02 \x01(\t\"f\n\x0e\x43reateActivity\x12\x13\n\x0b\x61\x63tivity_id\x18\x01 \x01(\x03\x12\x16\n\x0e\x61\x63tivity_state\x18\x02 \x01(\x05\x12\x17\n\x0fis_new_activity\x18\x03 \x01(\x05\x12\x0e\n\x06\x61\x63tion\x18\x04 \x01(\x05\"\xd4\x01\n\x10\x43reateAttachCard\x12\x37\n\x05goods\x18\x01 \x01(\x0b\x32(.bilibili.dynamic.common.CreateGoodsCard\x12\x44\n\x0b\x63ommon_card\x18\x02 \x01(\x0b\x32/.bilibili.dynamic.common.CreateCommonAttachCard\x12\x41\n\ncommercial\x18\x03 \x01(\x0b\x32-.bilibili.dynamic.common.CreateCommercialCard\"\xbb\x02\n\x0f\x43reateCheckResp\x12\x38\n\x07setting\x18\x01 \x01(\x0b\x32\'.bilibili.dynamic.common.PublishSetting\x12\x39\n\npermission\x18\x02 \x01(\x0b\x32%.bilibili.dynamic.common.UpPermission\x12\x39\n\nshare_info\x18\x03 \x01(\x0b\x32%.bilibili.dynamic.common.ShareChannel\x12=\n\nyellow_bar\x18\x04 \x01(\x0b\x32).bilibili.dynamic.common.PublishYellowBar\x12\x39\n\x0cplus_red_dot\x18\x05 \x01(\x0b\x32#.bilibili.dynamic.common.PlusRedDot\"T\n\x14\x43reateCommercialCard\x12\x1e\n\x16\x63ommercial_entity_type\x18\x01 \x01(\x03\x12\x1c\n\x14\x63ommercial_entity_id\x18\x02 \x01(\x03\"\x90\x01\n\x16\x43reateCommonAttachCard\x12\x35\n\x04type\x18\x01 \x01(\x0e\x32\'.bilibili.dynamic.common.AttachCardType\x12\x0e\n\x06\x62iz_id\x18\x02 \x01(\x03\x12\x16\n\x0ereserve_source\x18\x03 \x01(\x05\x12\x17\n\x0freserve_lottery\x18\x04 \x01(\x05\"\\\n\rCreateContent\x12<\n\x08\x63ontents\x18\x01 \x03(\x0b\x32*.bilibili.dynamic.common.CreateContentItem\x12\r\n\x05title\x18\x02 \x01(\t\"\x9f\x01\n\x11\x43reateContentItem\x12\x10\n\x08raw_text\x18\x01 \x01(\t\x12\x32\n\x04type\x18\x02 \x01(\x0e\x32$.bilibili.dynamic.common.ContentType\x12\x0e\n\x06\x62iz_id\x18\x03 \x01(\t\x12\x34\n\x05goods\x18\x04 \x01(\x0b\x32%.bilibili.dynamic.common.GoodsContent\"\x82\x06\n\x0e\x43reateDynVideo\x12\x15\n\rrelation_from\x18\x01 \x01(\t\x12\x10\n\x08\x62iz_from\x18\x03 \x01(\x05\x12\x11\n\tcopyright\x18\x04 \x01(\x05\x12\x11\n\tno_public\x18\x05 \x01(\x05\x12\x12\n\nno_reprint\x18\x06 \x01(\x05\x12\x0e\n\x06source\x18\x07 \x01(\t\x12\r\n\x05\x63over\x18\x08 \x01(\t\x12\r\n\x05title\x18\t \x01(\t\x12\x0b\n\x03tid\x18\n \x01(\x03\x12\x0b\n\x03tag\x18\x0b \x01(\t\x12\x0c\n\x04\x64\x65sc\x18\x0c \x01(\t\x12\x16\n\x0e\x64\x65sc_format_id\x18\r \x01(\x03\x12\x11\n\topen_elec\x18\x0e \x01(\x05\x12\r\n\x05\x64time\x18\x0f \x01(\x05\x12\x37\n\x06videos\x18\x10 \x03(\x0b\x32\'.bilibili.dynamic.common.DynVideoMultiP\x12=\n\twatermark\x18\x11 \x01(\x0b\x32*.bilibili.dynamic.common.DynVideoWatermark\x12\x12\n\nmission_id\x18\x12 \x01(\x03\x12\x0f\n\x07\x64ynamic\x18\x13 \x01(\t\x12\x19\n\x11\x64ynamic_extension\x18\x14 \x01(\t\x12\x14\n\x0c\x64ynamic_ctrl\x18\x15 \x01(\t\x12\x14\n\x0c\x64ynamic_from\x18\x16 \x01(\t\x12\x12\n\nlottery_id\x18\x17 \x01(\x03\x12\x33\n\x04vote\x18\x18 \x01(\x0b\x32%.bilibili.dynamic.common.DynVideoVote\x12\x1a\n\x12up_selection_reply\x18\x19 \x01(\x08\x12\x16\n\x0eup_close_reply\x18\x1a \x01(\x08\x12\x16\n\x0eup_close_danmu\x18\x1b \x01(\x08\x12\x0f\n\x07up_from\x18\x1c \x01(\x03\x12\x10\n\x08\x64uration\x18\x1d \x01(\x03\x12\x10\n\x08topic_id\x18\x1e \x01(\x03\x12\x11\n\tupload_id\x18\x1f \x01(\t\x12<\n\x0ctopic_detail\x18  \x01(\x0b\x32&.bilibili.dynamic.common.DynVideoTopic\"\xc0\x01\n\x14\x43reateDynVideoResult\x12\x0b\n\x03\x61id\x18\x01 \x01(\x03\x12\x0f\n\x07message\x18\x02 \x01(\t\x12J\n\x10submitact_banner\x18\x03 \x01(\x0b\x32\x30.bilibili.dynamic.common.DynVideoSubmitActBanner\x12>\n\npush_intro\x18\x04 \x01(\x0b\x32*.bilibili.dynamic.common.DynVideoPushIntro\"\"\n\x0f\x43reateGoodsCard\x12\x0f\n\x07item_id\x18\x01 \x03(\t\"\x83\x03\n\x0c\x43reateOption\x12\x19\n\x11up_choose_comment\x18\x01 \x01(\x05\x12\x15\n\rclose_comment\x18\x02 \x01(\x05\x12\x14\n\x0c\x66old_exclude\x18\x03 \x01(\x05\x12\x13\n\x0b\x61udit_level\x18\x04 \x01(\x05\x12\x17\n\x0fsync_to_comment\x18\x05 \x01(\x05\x12\x41\n\x10video_share_info\x18\x06 \x01(\x0b\x32\'.bilibili.dynamic.common.VideoShareInfo\x12\x39\n\x08\x61\x63tivity\x18\x07 \x01(\x0b\x32\'.bilibili.dynamic.common.CreateActivity\x12\x10\n\x08pic_mode\x18\n \x01(\x05\x12\x11\n\tonly_fans\x18\x0b \x01(\x03\x12\x15\n\rlimit_pegasus\x18\x0c \x01(\x05\x12\x14\n\x0climit_search\x18\r \x01(\x05\x12\x16\n\x0etimer_pub_time\x18\x0e \x01(\x03\x12\x15\n\ronly_fans_dnd\x18\x0f \x01(\x03\"\x8e\x01\n\tCreatePic\x12\x0f\n\x07img_src\x18\x01 \x01(\t\x12\x11\n\timg_width\x18\x02 \x01(\x01\x12\x12\n\nimg_height\x18\x03 \x01(\x01\x12\x10\n\x08img_size\x18\x04 \x01(\x01\x12\x37\n\x08img_tags\x18\x05 \x03(\x0b\x32%.bilibili.dynamic.common.CreatePicTag\"\xea\x01\n\x0c\x43reatePicTag\x12\x0f\n\x07item_id\x18\x01 \x01(\x03\x12\x0b\n\x03tid\x18\x02 \x01(\x03\x12\x0b\n\x03mid\x18\x03 \x01(\x03\x12\x0c\n\x04text\x18\x04 \x01(\t\x12\x13\n\x0btext_string\x18\x05 \x01(\t\x12\x0c\n\x04type\x18\x06 \x01(\x03\x12\x13\n\x0bsource_type\x18\x07 \x01(\x03\x12\x0b\n\x03url\x18\x08 \x01(\t\x12\x12\n\nschema_url\x18\t \x01(\t\x12\x10\n\x08jump_url\x18\n \x01(\t\x12\x13\n\x0borientation\x18\x0b \x01(\x03\x12\t\n\x01x\x18\x0c \x01(\x03\x12\t\n\x01y\x18\r \x01(\x03\x12\x0b\n\x03poi\x18\x0e \x01(\t\"\x90\x02\n\nCreateResp\x12\x0e\n\x06\x64yn_id\x18\x01 \x01(\x03\x12\x12\n\ndyn_id_str\x18\x02 \x01(\t\x12\x10\n\x08\x64yn_type\x18\x03 \x01(\x03\x12\x0f\n\x07\x64yn_rid\x18\x04 \x01(\x03\x12\x37\n\tfake_card\x18\x05 \x01(\x0b\x32$.bilibili.app.dynamic.v2.DynamicItem\x12\x43\n\x0cvideo_result\x18\x06 \x01(\x0b\x32-.bilibili.dynamic.common.CreateDynVideoResult\x12=\n\x0cshare_window\x18\x07 \x01(\x0b\x32\'.bilibili.dynamic.common.ShareDynWindow\"\xb0\x01\n\tCreateTag\x12,\n\x03lbs\x18\x01 \x01(\x0b\x32\x1f.bilibili.dynamic.common.ExtLbs\x12\x39\n\x08sdk_game\x18\x02 \x01(\x0b\x32\'.bilibili.dynamic.common.BottomBusiness\x12:\n\tdiversion\x18\x03 \x01(\x0b\x32\'.bilibili.dynamic.common.BottomBusiness\"k\n\x0b\x43reateTopic\x12\n\n\x02id\x18\x01 \x01(\x03\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x13\n\x0b\x66rom_source\x18\x03 \x01(\t\x12\x15\n\rfrom_topic_id\x18\x04 \x01(\x03\x12\x16\n\x0esuper_topic_id\x18\x05 \x01(\x03\"R\n\x0b\x44ynIdentity\x12\x0e\n\x06\x64yn_id\x18\x01 \x01(\x03\x12\x33\n\x07revs_id\x18\x02 \x01(\x0b\x32\".bilibili.dynamic.common.DynRevsId\"*\n\tDynRevsId\x12\x10\n\x08\x64yn_type\x18\x01 \x01(\x03\x12\x0b\n\x03rid\x18\x02 \x01(\x03\"\x89\x06\n\x0e\x44ynVideoEditor\x12\x0b\n\x03\x63id\x18\x01 \x01(\x03\x12\x0e\n\x06upfrom\x18\x02 \x01(\x05\x12\x0f\n\x07\x66ilters\x18\x03 \x01(\t\x12\r\n\x05\x66onts\x18\x04 \x01(\t\x12\x11\n\tsubtitles\x18\x05 \x01(\t\x12\x0c\n\x04\x62gms\x18\x06 \x01(\t\x12\x10\n\x08stickers\x18\x07 \x01(\t\x12\x18\n\x10videoup_stickers\x18\x08 \x01(\t\x12\r\n\x05trans\x18\t \x01(\t\x12\x0f\n\x07makeups\x18\n \x01(\t\x12\x10\n\x08surgerys\x18\x0b \x01(\t\x12\x10\n\x08videofxs\x18\x0c \x01(\t\x12\x0e\n\x06themes\x18\r \x01(\t\x12\x12\n\ncooperates\x18\x0e \x01(\t\x12\x0f\n\x07rhythms\x18\x0f \x01(\t\x12\x0f\n\x07\x65\x66\x66\x65\x63ts\x18\x10 \x01(\t\x12\x13\n\x0b\x62\x61\x63kgrounds\x18\x11 \x01(\t\x12\x0e\n\x06videos\x18\x12 \x01(\t\x12\x0e\n\x06sounds\x18\x13 \x01(\t\x12\x0f\n\x07\x66lowers\x18\x14 \x01(\t\x12\x17\n\x0f\x63over_templates\x18\x15 \x01(\t\x12\x0b\n\x03tts\x18\x16 \x01(\t\x12\x10\n\x08openings\x18\x17 \x01(\t\x12\x13\n\x0brecord_text\x18\x18 \x01(\x08\x12\x0e\n\x06vupers\x18\x19 \x01(\t\x12\x10\n\x08\x66\x65\x61tures\x18\x1a \x01(\t\x12\x15\n\rbcut_features\x18\x1b \x01(\t\x12\x14\n\x0c\x61udio_record\x18\x1c \x01(\x05\x12\x0e\n\x06\x63\x61mera\x18\x1d \x01(\x05\x12\r\n\x05speed\x18\x1e \x01(\x05\x12\x15\n\rcamera_rotate\x18\x1f \x01(\x05\x12\x15\n\rscreen_record\x18  \x01(\x05\x12\x13\n\x0b\x64\x65\x66\x61ult_end\x18! \x01(\x05\x12\x10\n\x08\x64uration\x18\" \x01(\x05\x12\x11\n\tpic_count\x18# \x01(\x05\x12\x13\n\x0bvideo_count\x18$ \x01(\x05\x12\x15\n\rshot_duration\x18% \x01(\x05\x12\x11\n\tshot_game\x18& \x01(\t\x12\x11\n\thighlight\x18\' \x01(\x08\x12\x15\n\rhighlight_cnt\x18( \x01(\x05\x12\x11\n\tpip_count\x18) \x01(\x05\"t\n\x0e\x44ynVideoHotAct\x12\x0e\n\x06\x61\x63t_id\x18\x01 \x01(\x03\x12\r\n\x05\x65time\x18\x02 \x01(\x03\x12\n\n\x02id\x18\x03 \x01(\x03\x12\x0b\n\x03pic\x18\x04 \x01(\t\x12\r\n\x05stime\x18\x05 \x01(\x03\x12\r\n\x05title\x18\x06 \x01(\t\x12\x0c\n\x04link\x18\x07 \x01(\t\"w\n\x0e\x44ynVideoMultiP\x12\r\n\x05title\x18\x01 \x01(\t\x12\x10\n\x08\x66ilename\x18\x02 \x01(\t\x12\x0b\n\x03\x63id\x18\x03 \x01(\x03\x12\x37\n\x06\x65\x64itor\x18\x04 \x01(\x0b\x32\'.bilibili.dynamic.common.DynVideoEditor\"/\n\x11\x44ynVideoPushIntro\x12\x0c\n\x04show\x18\x01 \x01(\x05\x12\x0c\n\x04text\x18\x02 \x01(\t\"y\n\x17\x44ynVideoSubmitActBanner\x12\x13\n\x0bhotact_text\x18\x01 \x01(\t\x12\x12\n\nhotact_url\x18\x02 \x01(\t\x12\x35\n\x04list\x18\x03 \x03(\x0b\x32\'.bilibili.dynamic.common.DynVideoHotAct\";\n\rDynVideoTopic\x12\x13\n\x0b\x66rom_source\x18\x01 \x01(\t\x12\x15\n\rfrom_topic_id\x18\x02 \x01(\x03\"J\n\x0c\x44ynVideoVote\x12\x0f\n\x07vote_id\x18\x01 \x01(\x03\x12\x12\n\nvote_title\x18\x02 \x01(\t\x12\x15\n\rtop_for_reply\x18\x03 \x01(\x05\"B\n\x11\x44ynVideoWatermark\x12\r\n\x05state\x18\x01 \x01(\x05\x12\x0c\n\x04type\x18\x02 \x01(\x05\x12\x10\n\x08position\x18\x03 \x01(\x05\"\x1d\n\tEmoteNode\x12\x10\n\x08raw_text\x18\x01 \x01(\t\"\xb3\x01\n\x06\x45xtLbs\x12\x0f\n\x07\x61\x64\x64ress\x18\x01 \x01(\t\x12\x10\n\x08\x64istance\x18\x02 \x01(\x03\x12\x0c\n\x04type\x18\x03 \x01(\x03\x12\x0b\n\x03poi\x18\x04 \x01(\t\x12\x31\n\x08location\x18\x05 \x01(\x0b\x32\x1f.bilibili.dynamic.common.LbsLoc\x12\x12\n\nshow_title\x18\x06 \x01(\t\x12\r\n\x05title\x18\x07 \x01(\t\x12\x15\n\rshow_distance\x18\x08 \x01(\t\"w\n\x0b\x46ormulaNode\x12\x15\n\rlatex_content\x18\x01 \x01(\t\x12\x39\n\nimage_spec\x18\x02 \x01(\x0b\x32%.bilibili.dynamic.common.ImgInlineCfg\x12\x16\n\x0epng_image_data\x18\x03 \x01(\x0c\" \n\x0fGetUidByNameReq\x12\r\n\x05names\x18\x01 \x03(\t\"\x80\x01\n\x0fGetUidByNameRsp\x12@\n\x04uids\x18\x01 \x03(\x0b\x32\x32.bilibili.dynamic.common.GetUidByNameRsp.UidsEntry\x1a+\n\tUidsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x03:\x02\x38\x01\"E\n\x0cGoodsContent\x12\x13\n\x0bsource_type\x18\x01 \x01(\x05\x12\x0f\n\x07item_id\x18\x02 \x01(\x03\x12\x0f\n\x07shop_id\x18\x03 \x01(\x03\"]\n\x0cImgInlineCfg\x12\r\n\x05width\x18\x01 \x01(\x01\x12\x0e\n\x06height\x18\x02 \x01(\x01\x12.\n\x05\x63olor\x18\x03 \x01(\x0b\x32\x1f.bilibili.dynamic.common.Colors\"\xb1\x01\n\x10LaunchedActivity\x12\x14\n\x0cmodule_title\x18\x01 \x01(\t\x12\x41\n\nactivities\x18\x02 \x03(\x0b\x32-.bilibili.dynamic.common.LaunchedActivityItem\x12\x44\n\tshow_more\x18\x03 \x01(\x0b\x32\x31.bilibili.dynamic.common.ShowMoreLaunchedActivity\"Z\n\x14LaunchedActivityItem\x12\x13\n\x0b\x61\x63tivity_id\x18\x01 \x01(\x03\x12\x15\n\ractivity_name\x18\x02 \x01(\t\x12\x16\n\x0e\x61\x63tivity_state\x18\x03 \x01(\x05\"\"\n\x06LbsLoc\x12\x0b\n\x03lat\x18\x01 \x01(\x01\x12\x0b\n\x03lng\x18\x02 \x01(\x01\":\n\rLineParagraph\x12)\n\x03pic\x18\x01 \x01(\x0b\x32\x1c.bilibili.dynamic.common.Pic\"\xa5\x01\n\x08LinkNode\x12\x11\n\tshow_text\x18\x01 \x01(\t\x12\x0c\n\x04link\x18\x02 \x01(\t\x12\x0c\n\x04icon\x18\x03 \x01(\t\x12\x13\n\x0bicon_suffix\x18\x04 \x01(\t\x12\x11\n\tlink_type\x18\x05 \x01(\x05\x12\x0e\n\x06\x62iz_id\x18\x06 \x01(\t\x12\x32\n\x08video_ts\x18\x07 \x01(\x0b\x32 .bilibili.dynamic.common.VideoTs\"\xed\x01\n\x0cMetaDataCtrl\x12\x10\n\x08platform\x18\x01 \x01(\t\x12\r\n\x05\x62uild\x18\x02 \x01(\t\x12\x10\n\x08mobi_app\x18\x03 \x01(\t\x12\r\n\x05\x62uvid\x18\x04 \x01(\t\x12\x0e\n\x06\x64\x65vice\x18\x05 \x01(\t\x12\x12\n\nfrom_spmid\x18\x06 \x01(\t\x12\x0c\n\x04\x66rom\x18\x07 \x01(\t\x12\x10\n\x08trace_id\x18\x08 \x01(\t\x12\x15\n\rteenager_mode\x18\t \x01(\x05\x12\x12\n\ncold_start\x18\n \x01(\x05\x12\x0f\n\x07version\x18\x0b \x01(\t\x12\x0f\n\x07network\x18\x0c \x01(\x05\x12\n\n\x02ip\x18\r \x01(\t\"s\n\x12OnlyFansDndSetting\x12\r\n\x05title\x18\x01 \x01(\t\x12\x11\n\tpop_title\x18\x02 \x01(\t\x12\x10\n\x08pop_desc\x18\x03 \x01(\t\x12\x13\n\x0bpop_picture\x18\x04 \x01(\t\x12\x14\n\x0cpop_btn_text\x18\x05 \x01(\t\"\xbb\x01\n\x0eOnlyFansOption\x12\x39\n\x04type\x18\x01 \x01(\x0e\x32+.bilibili.dynamic.common.OnlyFansOptionType\x12\x10\n\x08\x64isabled\x18\x02 \x01(\x05\x12\r\n\x05title\x18\x03 \x01(\t\x12\x10\n\x08subtitle\x18\x04 \x01(\t\x12\x0c\n\x04icon\x18\x05 \x01(\t\x12\x16\n\x0eonly_fans_name\x18\x06 \x01(\t\x12\x15\n\rdesc_subtitle\x18\x07 \x01(\t\"\xe2\x01\n\x12OnlyFansPermission\x12\x12\n\npermission\x18\x01 \x01(\x05\x12\r\n\x05title\x18\x02 \x01(\t\x12\x10\n\x08subtitle\x18\x03 \x01(\t\x12\x0c\n\x04icon\x18\x04 \x01(\t\x12\r\n\x05toast\x18\x05 \x01(\t\x12\x38\n\x07options\x18\x06 \x03(\x0b\x32\'.bilibili.dynamic.common.OnlyFansOption\x12@\n\x0b\x64nd_setting\x18\x07 \x01(\x0b\x32+.bilibili.dynamic.common.OnlyFansDndSetting\"\xb1\x02\n\x04Opus\x12\x0f\n\x07opus_id\x18\x01 \x01(\x03\x12\x13\n\x0bopus_source\x18\x02 \x01(\x05\x12\r\n\x05title\x18\x03 \x01(\t\x12\x12\n\ncover_avid\x18\x04 \x01(\x03\x12\x12\n\nh5_content\x18\x05 \x01(\t\x12\x35\n\x07\x63ontent\x18\x06 \x01(\x0b\x32$.bilibili.dynamic.common.OpusContent\x12.\n\x04tags\x18\x07 \x03(\x0b\x32 .bilibili.dynamic.common.OpusTag\x12\x32\n\x08pub_info\x18\x08 \x01(\x0b\x32 .bilibili.dynamic.common.PubInfo\x12\x31\n\x07\x61rticle\x18\t \x01(\x0b\x32 .bilibili.dynamic.common.Article\"E\n\x0bOpusContent\x12\x36\n\nparagraphs\x18\x01 \x03(\x0b\x32\".bilibili.dynamic.common.Paragraph\"\xf9\x01\n\x0bOpusSummary\x12\x13\n\x0bopus_source\x18\x01 \x01(\x05\x12\r\n\x05title\x18\x02 \x01(\t\x12+\n\x05\x63over\x18\x03 \x03(\x0b\x32\x1c.bilibili.dynamic.common.Pic\x12\x35\n\x07summary\x18\x04 \x01(\x0b\x32$.bilibili.dynamic.common.OpusContent\x12.\n\x04tags\x18\x05 \x03(\x0b\x32 .bilibili.dynamic.common.OpusTag\x12\x32\n\x08pub_info\x18\x06 \x01(\x0b\x32 .bilibili.dynamic.common.PubInfo\"9\n\x07OpusTag\x12.\n\x03tag\x18\x01 \x01(\x0b\x32!.bilibili.dynamic.common.LinkNode\"\xc9\x05\n\tParagraph\x12\x43\n\tpara_type\x18\x01 \x01(\x0e\x32\x30.bilibili.dynamic.common.Paragraph.ParagraphType\x12\x42\n\x06\x66ormat\x18\x02 \x01(\x0b\x32\x32.bilibili.dynamic.common.Paragraph.ParagraphFormat\x12\x34\n\x04text\x18\x03 \x01(\x0b\x32&.bilibili.dynamic.common.TextParagraph\x12\x32\n\x03pic\x18\x04 \x01(\x0b\x32%.bilibili.dynamic.common.PicParagraph\x12\x34\n\x04line\x18\x05 \x01(\x0b\x32&.bilibili.dynamic.common.LineParagraph\x12\x39\n\tlink_card\x18\x06 \x01(\x0b\x32&.bilibili.dynamic.common.CardParagraph\x12\x34\n\x04\x63ode\x18\x07 \x01(\x0b\x32&.bilibili.dynamic.common.CodeParagraph\x1a\x39\n\nListFormat\x12\r\n\x05level\x18\x01 \x01(\x05\x12\r\n\x05order\x18\x02 \x01(\x05\x12\r\n\x05theme\x18\x03 \x01(\t\x1a\x64\n\x0fParagraphFormat\x12\r\n\x05\x61lign\x18\x01 \x01(\x05\x12\x42\n\x0blist_format\x18\x02 \x01(\x0b\x32-.bilibili.dynamic.common.Paragraph.ListFormat\"\x80\x01\n\rParagraphType\x12\x0b\n\x07\x44\x45\x46\x41ULT\x10\x00\x12\x08\n\x04TEXT\x10\x01\x12\x0c\n\x08PICTURES\x10\x02\x12\x08\n\x04LINE\x10\x03\x12\r\n\tREFERENCE\x10\x04\x12\x0f\n\x0bSORTED_LIST\x10\x05\x12\x11\n\rUNSORTED_LIST\x10\x06\x12\r\n\tLINK_CARD\x10\x07\"P\n\x03Pic\x12\x0b\n\x03url\x18\x01 \x01(\t\x12\r\n\x05width\x18\x02 \x01(\x01\x12\x0e\n\x06height\x18\x03 \x01(\x01\x12\x0c\n\x04size\x18\x04 \x01(\x01\x12\x0f\n\x07\x63omment\x18\x05 \x01(\t\"\xbf\x01\n\x0cPicParagraph\x12*\n\x04pics\x18\x01 \x03(\x0b\x32\x1c.bilibili.dynamic.common.Pic\x12\x46\n\x05style\x18\x02 \x01(\x0e\x32\x37.bilibili.dynamic.common.PicParagraph.PicParagraphStyle\";\n\x11PicParagraphStyle\x12\x0b\n\x07\x44\x45\x46\x41ULT\x10\x00\x12\r\n\tNINE_CELL\x10\x01\x12\n\n\x06SCROLL\x10\x02\"&\n\nPlusRedDot\x12\x18\n\x10plus_has_red_dot\x18\x01 \x01(\x03\"\x80\x01\n\x07Program\x12\r\n\x05title\x18\x01 \x01(\t\x12\x0c\n\x04\x64\x65sc\x18\x02 \x01(\t\x12\r\n\x05\x63over\x18\x03 \x01(\t\x12\x12\n\ntarget_url\x18\x04 \x01(\t\x12\x0c\n\x04icon\x18\x05 \x01(\t\x12\x14\n\x0cprogram_text\x18\x06 \x01(\t\x12\x11\n\tjump_text\x18\x07 \x01(\t\"T\n\x07PubInfo\x12\x0b\n\x03uid\x18\x01 \x01(\x03\x12\x10\n\x08pub_time\x18\x02 \x01(\x03\x12\x12\n\nlast_mtime\x18\x03 \x01(\x03\x12\x16\n\x0etimer_pub_time\x18\x04 \x01(\x03\"\xa7\x01\n\x0ePublishSetting\x12\x1c\n\x14min_words_to_article\x18\x01 \x01(\x05\x12\x1c\n\x14max_words_to_article\x18\x02 \x01(\x05\x12\x13\n\x0bupload_size\x18\x03 \x01(\x05\x12\x14\n\x0cmax_at_count\x18\x04 \x01(\x05\x12\x17\n\x0fmax_draft_count\x18\x05 \x01(\x05\x12\x15\n\rtitle_max_len\x18\x06 \x01(\x03\";\n\x10PublishYellowBar\x12\x0c\n\x04text\x18\x01 \x01(\t\x12\x0b\n\x03url\x18\x02 \x01(\t\x12\x0c\n\x04icon\x18\x03 \x01(\t\"q\n\x0fRepostInitCheck\x12\x38\n\nrepost_src\x18\x01 \x01(\x0b\x32$.bilibili.dynamic.common.DynIdentity\x12\x10\n\x08share_id\x18\x02 \x01(\t\x12\x12\n\nshare_mode\x18\x03 \x01(\x05\"\x81\x01\n\x0cShareChannel\x12\x14\n\x0cshare_origin\x18\x01 \x01(\t\x12\x0b\n\x03oid\x18\x02 \x01(\t\x12\x0b\n\x03sid\x18\x03 \x01(\t\x12\x41\n\x0eshare_channels\x18\x04 \x03(\x0b\x32).bilibili.dynamic.common.ShareChannelItem\"\x80\x01\n\x10ShareChannelItem\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0f\n\x07picture\x18\x02 \x01(\t\x12\x15\n\rshare_channel\x18\x03 \x01(\t\x12\x36\n\x07reserve\x18\x04 \x01(\x0b\x32%.bilibili.dynamic.common.ShareReserve\"o\n\x0eShareDynWindow\x12\x12\n\nmain_title\x18\x01 \x01(\t\x12\x11\n\tsub_title\x18\x02 \x01(\t\x12\x36\n\x08\x64yn_item\x18\x03 \x01(\x0b\x32$.bilibili.app.dynamic.v2.DynamicItem\"\x8c\x02\n\x0cShareReserve\x12\r\n\x05title\x18\x01 \x01(\t\x12\x0c\n\x04\x64\x65sc\x18\x02 \x01(\t\x12\x14\n\x0cqr_code_icon\x18\x03 \x01(\t\x12\x14\n\x0cqr_code_text\x18\x04 \x01(\t\x12\x13\n\x0bqr_code_url\x18\x05 \x01(\t\x12\x0c\n\x04name\x18\x06 \x01(\t\x12\x0c\n\x04\x66\x61\x63\x65\x18\x07 \x01(\t\x12;\n\x06poster\x18\x08 \x01(\x0b\x32+.bilibili.dynamic.common.ShareReservePoster\x12\x45\n\x0freserve_lottery\x18\t \x01(\x0b\x32,.bilibili.dynamic.common.ShareReserveLottery\"1\n\x13ShareReserveLottery\x12\x0c\n\x04icon\x18\x01 \x01(\t\x12\x0c\n\x04text\x18\x02 \x01(\t\"@\n\x12ShareReservePoster\x12\x0b\n\x03url\x18\x01 \x01(\t\x12\r\n\x05width\x18\x02 \x01(\x01\x12\x0e\n\x06height\x18\x03 \x01(\x01\"2\n\x0bShareResult\x12\x14\n\x0cshare_enable\x18\x01 \x01(\x03\x12\r\n\x05toast\x18\x02 \x01(\t\"A\n\x18ShowMoreLaunchedActivity\x12\x13\n\x0b\x62utton_text\x18\x01 \x01(\t\x12\x10\n\x08jump_url\x18\x02 \x01(\t\"\x81\x01\n\x06Sketch\x12\r\n\x05title\x18\x01 \x01(\t\x12\x11\n\tdesc_text\x18\x02 \x01(\t\x12\x0c\n\x04text\x18\x03 \x01(\t\x12\x0e\n\x06\x62iz_id\x18\x04 \x01(\x03\x12\x10\n\x08\x62iz_type\x18\x05 \x01(\x03\x12\x11\n\tcover_url\x18\x06 \x01(\t\x12\x12\n\ntarget_url\x18\x07 \x01(\t\"\xef\x02\n\x08TextNode\x12\x41\n\tnode_type\x18\x01 \x01(\x0e\x32..bilibili.dynamic.common.TextNode.TextNodeType\x12/\n\x04word\x18\x02 \x01(\x0b\x32!.bilibili.dynamic.common.WordNode\x12\x31\n\x05\x65mote\x18\x03 \x01(\x0b\x32\".bilibili.dynamic.common.EmoteNode\x12/\n\x04link\x18\x04 \x01(\x0b\x32!.bilibili.dynamic.common.LinkNode\x12\x35\n\x07\x66ormula\x18\x05 \x01(\x0b\x32$.bilibili.dynamic.common.FormulaNode\"T\n\x0cTextNodeType\x12\x0b\n\x07\x44\x45\x46\x41ULT\x10\x00\x12\t\n\x05WORDS\x10\x01\x12\t\n\x05\x45MOTE\x10\x02\x12\x06\n\x02\x41T\x10\x03\x12\x0c\n\x08\x42IZ_LINK\x10\x04\x12\x0b\n\x07\x46ORMULA\x10\x05\"A\n\rTextParagraph\x12\x30\n\x05nodes\x18\x01 \x03(\x0b\x32!.bilibili.dynamic.common.TextNode\"\x95\x02\n\x0cUpPermission\x12\x38\n\x05items\x18\x01 \x03(\x0b\x32).bilibili.dynamic.common.UpPermissionItem\x12\x44\n\x11launched_activity\x18\x02 \x01(\x0b\x32).bilibili.dynamic.common.LaunchedActivity\x12:\n\x0cshare_result\x18\x03 \x01(\x0b\x32$.bilibili.dynamic.common.ShareResult\x12I\n\x14only_fans_permission\x18\x04 \x01(\x0b\x32+.bilibili.dynamic.common.OnlyFansPermission\"\x99\x01\n\x10UpPermissionItem\x12\x0c\n\x04type\x18\x01 \x01(\x05\x12\x12\n\npermission\x18\x02 \x01(\x05\x12\r\n\x05title\x18\x03 \x01(\t\x12\x10\n\x08subtitle\x18\x04 \x01(\t\x12\x0c\n\x04icon\x18\x05 \x01(\t\x12\x10\n\x08jump_url\x18\x06 \x01(\t\x12\r\n\x05toast\x18\x07 \x01(\t\x12\x13\n\x0bhas_red_dot\x18\x08 \x01(\x03\"\x8c\x01\n\x0eUserCreateMeta\x12\x37\n\x08\x61pp_meta\x18\x01 \x01(\x0b\x32%.bilibili.dynamic.common.MetaDataCtrl\x12,\n\x03loc\x18\x02 \x01(\x0b\x32\x1f.bilibili.dynamic.common.LbsLoc\x12\x13\n\x0brepost_mode\x18\x03 \x01(\x05\"+\n\x0eVideoShareInfo\x12\x0b\n\x03\x63id\x18\x01 \x01(\x03\x12\x0c\n\x04part\x18\x02 \x01(\x05\"\xa2\x01\n\x07VideoTs\x12\x0b\n\x03\x63id\x18\x01 \x01(\x03\x12\x10\n\x08oid_type\x18\x02 \x01(\x03\x12\x0e\n\x06status\x18\x03 \x01(\x03\x12\r\n\x05index\x18\x04 \x01(\x03\x12\x0f\n\x07seconds\x18\x05 \x01(\x03\x12\x10\n\x08\x63idcount\x18\x06 \x01(\x03\x12\x0b\n\x03key\x18\x07 \x01(\t\x12\r\n\x05title\x18\x08 \x01(\t\x12\x0c\n\x04\x65pid\x18\t \x01(\x03\x12\x0c\n\x04\x64\x65sc\x18\n \x01(\t\"\xe8\x01\n\x08WordNode\x12\r\n\x05words\x18\x01 \x01(\t\x12\x11\n\tfont_size\x18\x02 \x01(\x01\x12\r\n\x05\x63olor\x18\x03 \x01(\t\x12\x12\n\ndark_color\x18\x04 \x01(\t\x12>\n\x05style\x18\x05 \x01(\x0b\x32/.bilibili.dynamic.common.WordNode.WordNodeStyle\x1aW\n\rWordNodeStyle\x12\x0c\n\x04\x62old\x18\x01 \x01(\x08\x12\x0e\n\x06italic\x18\x02 \x01(\x08\x12\x15\n\rstrikethrough\x18\x03 \x01(\x08\x12\x11\n\tunderline\x18\x04 \x01(\x08*\x8e\x01\n\x0b\x41tGroupType\x12\x19\n\x15\x41T_GROUP_TYPE_DEFAULT\x10\x00\x12\x18\n\x14\x41T_GROUP_TYPE_RECENT\x10\x01\x12\x18\n\x14\x41T_GROUP_TYPE_FOLLOW\x10\x02\x12\x16\n\x12\x41T_GROUP_TYPE_FANS\x10\x03\x12\x18\n\x14\x41T_GROUP_TYPE_OTHERS\x10\x04*\xa1\x04\n\x0e\x41ttachCardType\x12\x14\n\x10\x41TTACH_CARD_NONE\x10\x00\x12\x15\n\x11\x41TTACH_CARD_GOODS\x10\x01\x12\x14\n\x10\x41TTACH_CARD_VOTE\x10\x02\x12\x13\n\x0f\x41TTACH_CARD_UGC\x10\x03\x12\x18\n\x14\x41TTACH_CARD_ACTIVITY\x10\x04\x12!\n\x1d\x41TTACH_CARD_OFFICIAL_ACTIVITY\x10\x05\x12\x15\n\x11\x41TTACH_CARD_TOPIC\x10\x06\x12\x13\n\x0f\x41TTACH_CARD_OGV\x10\x07\x12\x18\n\x14\x41TTACH_CARD_AUTO_OGV\x10\x08\x12\x14\n\x10\x41TTACH_CARD_GAME\x10\t\x12\x15\n\x11\x41TTACH_CARD_MANGA\x10\n\x12\x1a\n\x16\x41TTACH_CARD_DECORATION\x10\x0b\x12\x15\n\x11\x41TTACH_CARD_MATCH\x10\x0c\x12\x14\n\x10\x41TTACH_CARD_PUGV\x10\r\x12\x17\n\x13\x41TTACH_CARD_RESERVE\x10\x0e\x12\x18\n\x14\x41TTACH_CARD_UP_TOPIC\x10\x0f\x12\x1b\n\x17\x41TTACH_CARD_UP_ACTIVITY\x10\x10\x12\x18\n\x14\x41TTACH_CARD_UP_MAOER\x10\x11\x12\x1c\n\x18\x41TTACH_CARD_MEMBER_GOODS\x10\x12\x12\x1d\n\x19\x41TTACH_CARD_MAN_TIAN_XING\x10\x13\x12\x17\n\x13\x41TTACH_CARD_LOTTERY\x10\x14*\xd3\x01\n\x0b\x43ontentType\x12\x15\n\x11\x43ONTENT_TYPE_NONE\x10\x00\x12\x08\n\x04TEXT\x10\x01\x12\x06\n\x02\x41T\x10\x02\x12\x0b\n\x07LOTTERY\x10\x03\x12\x08\n\x04VOTE\x10\x04\x12\t\n\x05TOPIC\x10\x05\x12\t\n\x05GOODS\x10\x06\x12\x06\n\x02\x42V\x10\x07\x12\x06\n\x02\x41V\x10\x08\x12\t\n\x05\x45MOJI\x10\t\x12\x08\n\x04USER\x10\n\x12\x06\n\x02\x43V\x10\x0b\x12\x06\n\x02VC\x10\x0c\x12\x07\n\x03WEB\x10\r\x12\n\n\x06TAOBAO\x10\x0e\x12\x08\n\x04MAIL\x10\x0f\x12\x0e\n\nOGV_SEASON\x10\x10\x12\n\n\x06OGV_EP\x10\x11*\xf6\x01\n\x14\x43reateInitCheckScene\x12#\n\x1f\x43REATE_INIT_CHECK_SCENE_INVALID\x10\x00\x12\"\n\x1e\x43REATE_INIT_CHECK_SCENE_NORMAL\x10\x01\x12\"\n\x1e\x43REATE_INIT_CHECK_SCENE_REPOST\x10\x02\x12!\n\x1d\x43REATE_INIT_CHECK_SCENE_SHARE\x10\x03\x12)\n%CREATE_INIT_CHECK_SCENE_RESERVE_SHARE\x10\x04\x12#\n\x1f\x43REATE_INIT_CHECK_SCENE_ARTICLE\x10\x05*\x9d\x03\n\x0b\x43reateScene\x12\x18\n\x14\x43REATE_SCENE_INVALID\x10\x00\x12\x1c\n\x18\x43REATE_SCENE_CREATE_WORD\x10\x01\x12\x1c\n\x18\x43REATE_SCENE_CREATE_DRAW\x10\x02\x12!\n\x1d\x43REATE_SCENE_CREATE_DYN_VIDEO\x10\x03\x12\x17\n\x13\x43REATE_SCENE_REPOST\x10\x04\x12\x1a\n\x16\x43REATE_SCENE_SHARE_BIZ\x10\x05\x12\x1b\n\x17\x43REATE_SCENE_SHARE_PAGE\x10\x06\x12\x1e\n\x1a\x43REATE_SCENE_SHARE_PROGRAM\x10\x07\x12\x1b\n\x17\x43REATE_SCENE_REPLY_SYNC\x10\x08\x12&\n\"CREATE_SCENE_REPLY_CREATE_ACTIVITY\x10\t\x12\x1a\n\x16\x43REATE_SCENE_CREATE_AD\x10\n\x12!\n\x1d\x43REATE_SCENE_CREATE_LIVE_RCMD\x10\x0b\x12\x1f\n\x1b\x43REATE_SCENE_CREATE_ARTICLE\x10\x0c*n\n\x12OnlyFansOptionType\x12\x19\n\x15ONLY_FANS_OPTION_NONE\x10\x00\x12\x1b\n\x17ONLY_FANS_OPTION_UPOWER\x10\x01\x12 \n\x1cONLY_FANS_OPTION_HIGH_UPOWER\x10\x02*\xac\x03\n\x0bOpusBizType\x12\x0b\n\x07\x44\x45\x46\x41ULT\x10\x00\x12\t\n\x05VIDEO\x10\x01\x12\x0b\n\x07RESERVE\x10\x02\x12\x0c\n\x08\x42IZ_VOTE\x10\x03\x12\x08\n\x04LIVE\x10\x04\x12\x0f\n\x0b\x42IZ_LOTTERY\x10\x05\x12\t\n\x05MATCH\x10\x06\x12\r\n\tBIZ_GOODS\x10\x07\x12\n\n\x06OGV_SS\x10\x08\x12\x0e\n\nBIZ_OGV_EP\x10\t\x12\t\n\x05MANGA\x10\n\x12\n\n\x06\x43HEESE\x10\x0b\x12\x0c\n\x08VIDEO_TS\x10\x0c\x12\n\n\x06\x42IZ_AT\x10\r\x12\x0c\n\x08HASH_TAG\x10\x0e\x12\n\n\x06\x42IZ_CV\x10\x0f\x12\x07\n\x03URL\x10\x10\x12\x0c\n\x08\x42IZ_MAIL\x10\x11\x12\x07\n\x03LBS\x10\x12\x12\x0c\n\x08\x41\x43TIVITY\x10\x13\x12%\n!BIZ_ATTACH_CARD_OFFICIAL_ACTIVITY\x10\x14\x12\x08\n\x04GAME\x10\x15\x12\x0e\n\nDECORATION\x10\x16\x12\x0c\n\x08UP_TOPIC\x10\x17\x12\x0f\n\x0bUP_ACTIVITY\x10\x18\x12\x0c\n\x08UP_MAOER\x10\x19\x12\x10\n\x0cMEMBER_GOODS\x10\x1a\x12\x15\n\x11OPENMALL_UP_ITEMS\x10\x1b\x12\t\n\x05MUSIC\x10\x1d*m\n\nOpusSource\x12\x12\n\x0e\x44\x45\x46\x41ULT_SOURCE\x10\x00\x12\t\n\x05\x41LBUM\x10\x01\x12\x0b\n\x07\x41RTICLE\x10\x02\x12\x08\n\x04NOTE\x10\x03\x12\x0f\n\x0bOGV_COMMENT\x10\x04\x12\x0e\n\nARTICLE_H5\x10\x05\x12\x08\n\x04WORD\x10\x06*F\n\rReserveSource\x12\x16\n\x12RESERVE_SOURCE_NEW\x10\x00\x12\x1d\n\x19RESERVE_SOURCE_ASSOCIATED\x10\x01*\xee\x03\n\x10UpPermissionType\x12\x1b\n\x17UP_PERMISSION_TYPE_NONE\x10\x00\x12\x1e\n\x1aUP_PERMISSION_TYPE_LOTTERY\x10\x01\x12%\n!UP_PERMISSION_TYPE_CLIP_PUBLISHED\x10\x02\x12&\n\"UP_PERMISSION_TYPE_UGC_ATTACH_CARD\x10\x03\x12(\n$UP_PERMISSION_TYPE_GOODS_ATTACH_CARD\x10\x04\x12%\n!UP_PERMISSION_TYPE_CHOOSE_COMMENT\x10\x05\x12&\n\"UP_PERMISSION_TYPE_CONTROL_COMMENT\x10\x06\x12$\n UP_PERMISSION_TYPE_CONTROL_DANMU\x10\x07\x12$\n UP_PERMISSION_TYPE_VIDEO_RESERVE\x10\x08\x12#\n\x1fUP_PERMISSION_TYPE_LIVE_RESERVE\x10\t\x12\x1f\n\x1bUP_PERMISSION_TYPE_BIZ_LINK\x10\n\x12!\n\x1dUP_PERMISSION_TYPE_COMMERCIAL\x10\x0b\x12 \n\x1cUP_PERMISSION_TYPE_BIG_COVER\x10\x0c\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bilibili.dynamic.common.dynamic_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_GETUIDBYNAMERSP_UIDSENTRY']._loaded_options = None
  _globals['_GETUIDBYNAMERSP_UIDSENTRY']._serialized_options = b'8\001'
  _globals['_ATGROUPTYPE']._serialized_start=12585
  _globals['_ATGROUPTYPE']._serialized_end=12727
  _globals['_ATTACHCARDTYPE']._serialized_start=12730
  _globals['_ATTACHCARDTYPE']._serialized_end=13275
  _globals['_CONTENTTYPE']._serialized_start=13278
  _globals['_CONTENTTYPE']._serialized_end=13489
  _globals['_CREATEINITCHECKSCENE']._serialized_start=13492
  _globals['_CREATEINITCHECKSCENE']._serialized_end=13738
  _globals['_CREATESCENE']._serialized_start=13741
  _globals['_CREATESCENE']._serialized_end=14154
  _globals['_ONLYFANSOPTIONTYPE']._serialized_start=14156
  _globals['_ONLYFANSOPTIONTYPE']._serialized_end=14266
  _globals['_OPUSBIZTYPE']._serialized_start=14269
  _globals['_OPUSBIZTYPE']._serialized_end=14697
  _globals['_OPUSSOURCE']._serialized_start=14699
  _globals['_OPUSSOURCE']._serialized_end=14808
  _globals['_RESERVESOURCE']._serialized_start=14810
  _globals['_RESERVESOURCE']._serialized_end=14880
  _globals['_UPPERMISSIONTYPE']._serialized_start=14883
  _globals['_UPPERMISSIONTYPE']._serialized_end=15377
  _globals['_ARTICLE']._serialized_start=106
  _globals['_ARTICLE']._serialized_end=257
  _globals['_ATGROUP']._serialized_start=260
  _globals['_ATGROUP']._serialized_end=395
  _globals['_ATITEM']._serialized_start=397
  _globals['_ATITEM']._serialized_end=490
  _globals['_ATLISTREQ']._serialized_start=492
  _globals['_ATLISTREQ']._serialized_end=516
  _globals['_ATLISTRSP']._serialized_start=518
  _globals['_ATLISTRSP']._serialized_end=579
  _globals['_ATSEARCHREQ']._serialized_start=581
  _globals['_ATSEARCHREQ']._serialized_end=624
  _globals['_BOTTOMBUSINESS']._serialized_start=626
  _globals['_BOTTOMBUSINESS']._serialized_end=669
  _globals['_CARDPARAGRAPH']._serialized_start=671
  _globals['_CARDPARAGRAPH']._serialized_end=757
  _globals['_CODEPARAGRAPH']._serialized_start=759
  _globals['_CODEPARAGRAPH']._serialized_end=805
  _globals['_COLORS']._serialized_start=807
  _globals['_COLORS']._serialized_end=855
  _globals['_CREATEACTIVITY']._serialized_start=857
  _globals['_CREATEACTIVITY']._serialized_end=959
  _globals['_CREATEATTACHCARD']._serialized_start=962
  _globals['_CREATEATTACHCARD']._serialized_end=1174
  _globals['_CREATECHECKRESP']._serialized_start=1177
  _globals['_CREATECHECKRESP']._serialized_end=1492
  _globals['_CREATECOMMERCIALCARD']._serialized_start=1494
  _globals['_CREATECOMMERCIALCARD']._serialized_end=1578
  _globals['_CREATECOMMONATTACHCARD']._serialized_start=1581
  _globals['_CREATECOMMONATTACHCARD']._serialized_end=1725
  _globals['_CREATECONTENT']._serialized_start=1727
  _globals['_CREATECONTENT']._serialized_end=1819
  _globals['_CREATECONTENTITEM']._serialized_start=1822
  _globals['_CREATECONTENTITEM']._serialized_end=1981
  _globals['_CREATEDYNVIDEO']._serialized_start=1984
  _globals['_CREATEDYNVIDEO']._serialized_end=2754
  _globals['_CREATEDYNVIDEORESULT']._serialized_start=2757
  _globals['_CREATEDYNVIDEORESULT']._serialized_end=2949
  _globals['_CREATEGOODSCARD']._serialized_start=2951
  _globals['_CREATEGOODSCARD']._serialized_end=2985
  _globals['_CREATEOPTION']._serialized_start=2988
  _globals['_CREATEOPTION']._serialized_end=3375
  _globals['_CREATEPIC']._serialized_start=3378
  _globals['_CREATEPIC']._serialized_end=3520
  _globals['_CREATEPICTAG']._serialized_start=3523
  _globals['_CREATEPICTAG']._serialized_end=3757
  _globals['_CREATERESP']._serialized_start=3760
  _globals['_CREATERESP']._serialized_end=4032
  _globals['_CREATETAG']._serialized_start=4035
  _globals['_CREATETAG']._serialized_end=4211
  _globals['_CREATETOPIC']._serialized_start=4213
  _globals['_CREATETOPIC']._serialized_end=4320
  _globals['_DYNIDENTITY']._serialized_start=4322
  _globals['_DYNIDENTITY']._serialized_end=4404
  _globals['_DYNREVSID']._serialized_start=4406
  _globals['_DYNREVSID']._serialized_end=4448
  _globals['_DYNVIDEOEDITOR']._serialized_start=4451
  _globals['_DYNVIDEOEDITOR']._serialized_end=5228
  _globals['_DYNVIDEOHOTACT']._serialized_start=5230
  _globals['_DYNVIDEOHOTACT']._serialized_end=5346
  _globals['_DYNVIDEOMULTIP']._serialized_start=5348
  _globals['_DYNVIDEOMULTIP']._serialized_end=5467
  _globals['_DYNVIDEOPUSHINTRO']._serialized_start=5469
  _globals['_DYNVIDEOPUSHINTRO']._serialized_end=5516
  _globals['_DYNVIDEOSUBMITACTBANNER']._serialized_start=5518
  _globals['_DYNVIDEOSUBMITACTBANNER']._serialized_end=5639
  _globals['_DYNVIDEOTOPIC']._serialized_start=5641
  _globals['_DYNVIDEOTOPIC']._serialized_end=5700
  _globals['_DYNVIDEOVOTE']._serialized_start=5702
  _globals['_DYNVIDEOVOTE']._serialized_end=5776
  _globals['_DYNVIDEOWATERMARK']._serialized_start=5778
  _globals['_DYNVIDEOWATERMARK']._serialized_end=5844
  _globals['_EMOTENODE']._serialized_start=5846
  _globals['_EMOTENODE']._serialized_end=5875
  _globals['_EXTLBS']._serialized_start=5878
  _globals['_EXTLBS']._serialized_end=6057
  _globals['_FORMULANODE']._serialized_start=6059
  _globals['_FORMULANODE']._serialized_end=6178
  _globals['_GETUIDBYNAMEREQ']._serialized_start=6180
  _globals['_GETUIDBYNAMEREQ']._serialized_end=6212
  _globals['_GETUIDBYNAMERSP']._serialized_start=6215
  _globals['_GETUIDBYNAMERSP']._serialized_end=6343
  _globals['_GETUIDBYNAMERSP_UIDSENTRY']._serialized_start=6300
  _globals['_GETUIDBYNAMERSP_UIDSENTRY']._serialized_end=6343
  _globals['_GOODSCONTENT']._serialized_start=6345
  _globals['_GOODSCONTENT']._serialized_end=6414
  _globals['_IMGINLINECFG']._serialized_start=6416
  _globals['_IMGINLINECFG']._serialized_end=6509
  _globals['_LAUNCHEDACTIVITY']._serialized_start=6512
  _globals['_LAUNCHEDACTIVITY']._serialized_end=6689
  _globals['_LAUNCHEDACTIVITYITEM']._serialized_start=6691
  _globals['_LAUNCHEDACTIVITYITEM']._serialized_end=6781
  _globals['_LBSLOC']._serialized_start=6783
  _globals['_LBSLOC']._serialized_end=6817
  _globals['_LINEPARAGRAPH']._serialized_start=6819
  _globals['_LINEPARAGRAPH']._serialized_end=6877
  _globals['_LINKNODE']._serialized_start=6880
  _globals['_LINKNODE']._serialized_end=7045
  _globals['_METADATACTRL']._serialized_start=7048
  _globals['_METADATACTRL']._serialized_end=7285
  _globals['_ONLYFANSDNDSETTING']._serialized_start=7287
  _globals['_ONLYFANSDNDSETTING']._serialized_end=7402
  _globals['_ONLYFANSOPTION']._serialized_start=7405
  _globals['_ONLYFANSOPTION']._serialized_end=7592
  _globals['_ONLYFANSPERMISSION']._serialized_start=7595
  _globals['_ONLYFANSPERMISSION']._serialized_end=7821
  _globals['_OPUS']._serialized_start=7824
  _globals['_OPUS']._serialized_end=8129
  _globals['_OPUSCONTENT']._serialized_start=8131
  _globals['_OPUSCONTENT']._serialized_end=8200
  _globals['_OPUSSUMMARY']._serialized_start=8203
  _globals['_OPUSSUMMARY']._serialized_end=8452
  _globals['_OPUSTAG']._serialized_start=8454
  _globals['_OPUSTAG']._serialized_end=8511
  _globals['_PARAGRAPH']._serialized_start=8514
  _globals['_PARAGRAPH']._serialized_end=9227
  _globals['_PARAGRAPH_LISTFORMAT']._serialized_start=8937
  _globals['_PARAGRAPH_LISTFORMAT']._serialized_end=8994
  _globals['_PARAGRAPH_PARAGRAPHFORMAT']._serialized_start=8996
  _globals['_PARAGRAPH_PARAGRAPHFORMAT']._serialized_end=9096
  _globals['_PARAGRAPH_PARAGRAPHTYPE']._serialized_start=9099
  _globals['_PARAGRAPH_PARAGRAPHTYPE']._serialized_end=9227
  _globals['_PIC']._serialized_start=9229
  _globals['_PIC']._serialized_end=9309
  _globals['_PICPARAGRAPH']._serialized_start=9312
  _globals['_PICPARAGRAPH']._serialized_end=9503
  _globals['_PICPARAGRAPH_PICPARAGRAPHSTYLE']._serialized_start=9444
  _globals['_PICPARAGRAPH_PICPARAGRAPHSTYLE']._serialized_end=9503
  _globals['_PLUSREDDOT']._serialized_start=9505
  _globals['_PLUSREDDOT']._serialized_end=9543
  _globals['_PROGRAM']._serialized_start=9546
  _globals['_PROGRAM']._serialized_end=9674
  _globals['_PUBINFO']._serialized_start=9676
  _globals['_PUBINFO']._serialized_end=9760
  _globals['_PUBLISHSETTING']._serialized_start=9763
  _globals['_PUBLISHSETTING']._serialized_end=9930
  _globals['_PUBLISHYELLOWBAR']._serialized_start=9932
  _globals['_PUBLISHYELLOWBAR']._serialized_end=9991
  _globals['_REPOSTINITCHECK']._serialized_start=9993
  _globals['_REPOSTINITCHECK']._serialized_end=10106
  _globals['_SHARECHANNEL']._serialized_start=10109
  _globals['_SHARECHANNEL']._serialized_end=10238
  _globals['_SHARECHANNELITEM']._serialized_start=10241
  _globals['_SHARECHANNELITEM']._serialized_end=10369
  _globals['_SHAREDYNWINDOW']._serialized_start=10371
  _globals['_SHAREDYNWINDOW']._serialized_end=10482
  _globals['_SHARERESERVE']._serialized_start=10485
  _globals['_SHARERESERVE']._serialized_end=10753
  _globals['_SHARERESERVELOTTERY']._serialized_start=10755
  _globals['_SHARERESERVELOTTERY']._serialized_end=10804
  _globals['_SHARERESERVEPOSTER']._serialized_start=10806
  _globals['_SHARERESERVEPOSTER']._serialized_end=10870
  _globals['_SHARERESULT']._serialized_start=10872
  _globals['_SHARERESULT']._serialized_end=10922
  _globals['_SHOWMORELAUNCHEDACTIVITY']._serialized_start=10924
  _globals['_SHOWMORELAUNCHEDACTIVITY']._serialized_end=10989
  _globals['_SKETCH']._serialized_start=10992
  _globals['_SKETCH']._serialized_end=11121
  _globals['_TEXTNODE']._serialized_start=11124
  _globals['_TEXTNODE']._serialized_end=11491
  _globals['_TEXTNODE_TEXTNODETYPE']._serialized_start=11407
  _globals['_TEXTNODE_TEXTNODETYPE']._serialized_end=11491
  _globals['_TEXTPARAGRAPH']._serialized_start=11493
  _globals['_TEXTPARAGRAPH']._serialized_end=11558
  _globals['_UPPERMISSION']._serialized_start=11561
  _globals['_UPPERMISSION']._serialized_end=11838
  _globals['_UPPERMISSIONITEM']._serialized_start=11841
  _globals['_UPPERMISSIONITEM']._serialized_end=11994
  _globals['_USERCREATEMETA']._serialized_start=11997
  _globals['_USERCREATEMETA']._serialized_end=12137
  _globals['_VIDEOSHAREINFO']._serialized_start=12139
  _globals['_VIDEOSHAREINFO']._serialized_end=12182
  _globals['_VIDEOTS']._serialized_start=12185
  _globals['_VIDEOTS']._serialized_end=12347
  _globals['_WORDNODE']._serialized_start=12350
  _globals['_WORDNODE']._serialized_end=12582
  _globals['_WORDNODE_WORDNODESTYLE']._serialized_start=12495
  _globals['_WORDNODE_WORDNODESTYLE']._serialized_end=12582
# @@protoc_insertion_point(module_scope)
