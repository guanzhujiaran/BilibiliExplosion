# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: datacenter/hakase/protobuf/android_device_info.proto
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
    'datacenter/hakase/protobuf/android_device_info.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n4datacenter/hakase/protobuf/android_device_info.proto\x12\x1a\x64\x61tacenter.hakase.protobuf\"\xb8\x13\n\x11\x41ndroidDeviceInfo\x12\x0e\n\x06sdkver\x18\x01 \x01(\t\x12\x0e\n\x06\x61pp_id\x18\x02 \x01(\t\x12\x13\n\x0b\x61pp_version\x18\x03 \x01(\t\x12\x18\n\x10\x61pp_version_code\x18\x04 \x01(\t\x12\x0b\n\x03mid\x18\x05 \x01(\t\x12\x0c\n\x04\x63hid\x18\x06 \x01(\t\x12\x0b\n\x03\x66ts\x18\x07 \x01(\x03\x12\x13\n\x0b\x62uvid_local\x18\x08 \x01(\t\x12\r\n\x05\x66irst\x18\t \x01(\x05\x12\x0c\n\x04proc\x18\n \x01(\t\x12\x0b\n\x03net\x18\x0b \x01(\t\x12\x0c\n\x04\x62\x61nd\x18\x0c \x01(\t\x12\r\n\x05osver\x18\r \x01(\t\x12\t\n\x01t\x18\x0e \x01(\x03\x12\x11\n\tcpu_count\x18\x0f \x01(\x05\x12\r\n\x05model\x18\x10 \x01(\t\x12\r\n\x05\x62rand\x18\x11 \x01(\t\x12\x0e\n\x06screen\x18\x12 \x01(\t\x12\x11\n\tcpu_model\x18\x13 \x01(\t\x12\r\n\x05\x62tmac\x18\x14 \x01(\t\x12\x0c\n\x04\x62oot\x18\x15 \x01(\x03\x12\x0b\n\x03\x65mu\x18\x16 \x01(\t\x12\x0b\n\x03oid\x18\x17 \x01(\t\x12\x0f\n\x07network\x18\x18 \x01(\t\x12\x0b\n\x03mem\x18\x19 \x01(\x03\x12\x0e\n\x06sensor\x18\x1a \x01(\t\x12\x10\n\x08\x63pu_freq\x18\x1b \x01(\x03\x12\x12\n\ncpu_vendor\x18\x1c \x01(\t\x12\x0b\n\x03sim\x18\x1d \x01(\t\x12\x12\n\nbrightness\x18\x1e \x01(\x05\x12G\n\x05props\x18\x1f \x03(\x0b\x32\x38.datacenter.hakase.protobuf.AndroidDeviceInfo.PropsEntry\x12\x43\n\x03sys\x18  \x03(\x0b\x32\x36.datacenter.hakase.protobuf.AndroidDeviceInfo.SysEntry\x12\x0f\n\x07wifimac\x18! \x01(\t\x12\x0c\n\x04\x61\x64id\x18\" \x01(\t\x12\n\n\x02os\x18# \x01(\t\x12\x0c\n\x04imei\x18$ \x01(\t\x12\x0c\n\x04\x63\x65ll\x18% \x01(\t\x12\x0c\n\x04imsi\x18& \x01(\t\x12\r\n\x05iccid\x18\' \x01(\t\x12\x0e\n\x06\x63\x61mcnt\x18( \x01(\x05\x12\r\n\x05\x63\x61mpx\x18) \x01(\t\x12\x13\n\x0btotal_space\x18* \x01(\x03\x12\x0f\n\x07\x61xposed\x18+ \x01(\t\x12\x0c\n\x04maps\x18, \x01(\t\x12\r\n\x05\x66iles\x18- \x01(\t\x12\x0f\n\x07virtual\x18. \x01(\t\x12\x13\n\x0bvirtualproc\x18/ \x01(\t\x12\r\n\x05gadid\x18\x30 \x01(\t\x12\x0e\n\x06glimit\x18\x31 \x01(\t\x12\x0c\n\x04\x61pps\x18\x32 \x01(\t\x12\x0c\n\x04guid\x18\x33 \x01(\t\x12\x0b\n\x03uid\x18\x34 \x01(\t\x12\x0c\n\x04root\x18\x35 \x01(\x05\x12\x0f\n\x07\x63\x61mzoom\x18\x36 \x01(\t\x12\x10\n\x08\x63\x61mlight\x18\x37 \x01(\t\x12\x0c\n\x04oaid\x18\x38 \x01(\t\x12\x0c\n\x04udid\x18\x39 \x01(\t\x12\x0c\n\x04vaid\x18: \x01(\t\x12\x0c\n\x04\x61\x61id\x18; \x01(\t\x12\x14\n\x0c\x61ndroidapp20\x18< \x01(\t\x12\x15\n\randroidappcnt\x18= \x01(\x05\x12\x17\n\x0f\x61ndroidsysapp20\x18> \x01(\t\x12\x0f\n\x07\x62\x61ttery\x18? \x01(\x05\x12\x15\n\rbattery_state\x18@ \x01(\t\x12\r\n\x05\x62ssid\x18\x41 \x01(\t\x12\x10\n\x08\x62uild_id\x18\x43 \x01(\t\x12\x13\n\x0b\x63ountry_iso\x18\x44 \x01(\t\x12\x13\n\x0b\x66ree_memory\x18\x46 \x01(\x03\x12\x10\n\x08\x66storage\x18G \x01(\t\x12\x16\n\x0ekernel_version\x18J \x01(\t\x12\x11\n\tlanguages\x18K \x01(\t\x12\x0b\n\x03mac\x18L \x01(\t\x12\x0c\n\x04ssid\x18O \x01(\t\x12\x14\n\x0csystemvolume\x18P \x01(\x05\x12\x13\n\x0bwifimaclist\x18Q \x01(\t\x12\x0e\n\x06memory\x18R \x01(\x03\x12\x13\n\x0bstr_battery\x18S \x01(\t\x12\x0f\n\x07is_root\x18T \x01(\x08\x12\x16\n\x0estr_brightness\x18U \x01(\t\x12\x12\n\nstr_app_id\x18V \x01(\t\x12\n\n\x02ip\x18W \x01(\t\x12\x12\n\nuser_agent\x18X \x01(\t\x12\x17\n\x0flight_intensity\x18Y \x01(\t\x12\x14\n\x0c\x64\x65vice_angle\x18Z \x03(\x02\x12\x12\n\ngps_sensor\x18[ \x01(\x03\x12\x14\n\x0cspeed_sensor\x18\\ \x01(\x03\x12\x1b\n\x13linear_speed_sensor\x18] \x01(\x03\x12\x18\n\x10gyroscope_sensor\x18^ \x01(\x03\x12\x11\n\tbiometric\x18_ \x01(\x03\x12\x12\n\nbiometrics\x18` \x03(\t\x12\x14\n\x0clast_dump_ts\x18\x61 \x01(\x03\x12\x10\n\x08location\x18\x62 \x01(\t\x12\x0f\n\x07\x63ountry\x18\x63 \x01(\t\x12\x0c\n\x04\x63ity\x18\x64 \x01(\t\x12\x1b\n\x13\x64\x61ta_activity_state\x18\x65 \x01(\x05\x12\x1a\n\x12\x64\x61ta_connect_state\x18\x66 \x01(\x05\x12\x19\n\x11\x64\x61ta_network_type\x18g \x01(\x05\x12\x1a\n\x12voice_network_type\x18h \x01(\x05\x12\x1b\n\x13voice_service_state\x18i \x01(\x05\x12\x15\n\rusb_connected\x18j \x01(\x05\x12\x13\n\x0b\x61\x64\x62_enabled\x18k \x01(\x05\x12\x12\n\nui_version\x18l \x01(\t\x12\x1d\n\x15\x61\x63\x63\x65ssibility_service\x18m \x03(\t\x12<\n\x0csensors_info\x18n \x03(\x0b\x32&.datacenter.hakase.protobuf.SensorInfo\x12\r\n\x05\x64rmid\x18o \x01(\t\x12\x17\n\x0f\x62\x61ttery_present\x18p \x01(\x08\x12\x1a\n\x12\x62\x61ttery_technology\x18q \x01(\t\x12\x1b\n\x13\x62\x61ttery_temperature\x18r \x01(\x05\x12\x17\n\x0f\x62\x61ttery_voltage\x18s \x01(\x05\x12\x17\n\x0f\x62\x61ttery_plugged\x18t \x01(\x05\x12\x16\n\x0e\x62\x61ttery_health\x18u \x01(\x05\x12\x14\n\x0c\x63pu_abi_list\x18v \x03(\t\x12\x14\n\x0c\x63pu_abi_libc\x18w \x01(\t\x12\x16\n\x0e\x63pu_abi_libc64\x18x \x01(\t\x12\x15\n\rcpu_processor\x18y \x01(\t\x12\x16\n\x0e\x63pu_model_name\x18z \x01(\t\x12\x14\n\x0c\x63pu_hardware\x18{ \x01(\t\x12\x14\n\x0c\x63pu_features\x18| \x01(\t\x12\x10\n\x08\x61\x64\x62_info\x18} \x01(\t\x1a,\n\nPropsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\x1a*\n\x08SysEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"\x92\x01\n\nSensorInfo\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0e\n\x06vendor\x18\x02 \x01(\t\x12\x0f\n\x07version\x18\x03 \x01(\x05\x12\x0c\n\x04type\x18\x04 \x01(\x05\x12\x11\n\tmax_range\x18\x05 \x01(\x02\x12\x12\n\nresolution\x18\x06 \x01(\x02\x12\r\n\x05power\x18\x07 \x01(\x02\x12\x11\n\tmin_delay\x18\x08 \x01(\x05\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'datacenter.hakase.protobuf.android_device_info_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_ANDROIDDEVICEINFO_PROPSENTRY']._loaded_options = None
  _globals['_ANDROIDDEVICEINFO_PROPSENTRY']._serialized_options = b'8\001'
  _globals['_ANDROIDDEVICEINFO_SYSENTRY']._loaded_options = None
  _globals['_ANDROIDDEVICEINFO_SYSENTRY']._serialized_options = b'8\001'
  _globals['_ANDROIDDEVICEINFO']._serialized_start=85
  _globals['_ANDROIDDEVICEINFO']._serialized_end=2573
  _globals['_ANDROIDDEVICEINFO_PROPSENTRY']._serialized_start=2485
  _globals['_ANDROIDDEVICEINFO_PROPSENTRY']._serialized_end=2529
  _globals['_ANDROIDDEVICEINFO_SYSENTRY']._serialized_start=2531
  _globals['_ANDROIDDEVICEINFO_SYSENTRY']._serialized_end=2573
  _globals['_SENSORINFO']._serialized_start=2576
  _globals['_SENSORINFO']._serialized_end=2722
# @@protoc_insertion_point(module_scope)
