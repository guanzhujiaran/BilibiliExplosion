# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: google/protobuf/unittest_proto3_lite.proto
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
    'google/protobuf/unittest_proto3_lite.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import unittest_import_pb2 as google_dot_protobuf_dot_unittest__import__pb2
try:
  google_dot_protobuf_dot_unittest__import__public__pb2 = google_dot_protobuf_dot_unittest__import__pb2.google_dot_protobuf_dot_unittest__import__public__pb2
except AttributeError:
  google_dot_protobuf_dot_unittest__import__public__pb2 = google_dot_protobuf_dot_unittest__import__pb2.google.protobuf.unittest_import_public_pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n*google/protobuf/unittest_proto3_lite.proto\x12\x14proto3_lite_unittest\x1a%google/protobuf/unittest_import.proto\"\xeb\x10\n\x0cTestAllTypes\x12\x16\n\x0eoptional_int32\x18\x01 \x01(\x05\x12\x16\n\x0eoptional_int64\x18\x02 \x01(\x03\x12\x17\n\x0foptional_uint32\x18\x03 \x01(\r\x12\x17\n\x0foptional_uint64\x18\x04 \x01(\x04\x12\x17\n\x0foptional_sint32\x18\x05 \x01(\x11\x12\x17\n\x0foptional_sint64\x18\x06 \x01(\x12\x12\x18\n\x10optional_fixed32\x18\x07 \x01(\x07\x12\x18\n\x10optional_fixed64\x18\x08 \x01(\x06\x12\x19\n\x11optional_sfixed32\x18\t \x01(\x0f\x12\x19\n\x11optional_sfixed64\x18\n \x01(\x10\x12\x16\n\x0eoptional_float\x18\x0b \x01(\x02\x12\x17\n\x0foptional_double\x18\x0c \x01(\x01\x12\x15\n\roptional_bool\x18\r \x01(\x08\x12\x17\n\x0foptional_string\x18\x0e \x01(\t\x12\x16\n\x0eoptional_bytes\x18\x0f \x01(\x0c\x12Q\n\x17optional_nested_message\x18\x12 \x01(\x0b\x32\x30.proto3_lite_unittest.TestAllTypes.NestedMessage\x12\x46\n\x18optional_foreign_message\x18\x13 \x01(\x0b\x32$.proto3_lite_unittest.ForeignMessage\x12H\n\x17optional_import_message\x18\x14 \x01(\x0b\x32\'.protobuf_unittest_import.ImportMessage\x12K\n\x14optional_nested_enum\x18\x15 \x01(\x0e\x32-.proto3_lite_unittest.TestAllTypes.NestedEnum\x12@\n\x15optional_foreign_enum\x18\x16 \x01(\x0e\x32!.proto3_lite_unittest.ForeignEnum\x12!\n\x15optional_string_piece\x18\x18 \x01(\tB\x02\x08\x02\x12\x19\n\roptional_cord\x18\x19 \x01(\tB\x02\x08\x01\x12U\n\x1eoptional_public_import_message\x18\x1a \x01(\x0b\x32-.protobuf_unittest_import.PublicImportMessage\x12S\n\x15optional_lazy_message\x18\x1b \x01(\x0b\x32\x30.proto3_lite_unittest.TestAllTypes.NestedMessageB\x02(\x01\x12\x16\n\x0erepeated_int32\x18\x1f \x03(\x05\x12\x16\n\x0erepeated_int64\x18  \x03(\x03\x12\x17\n\x0frepeated_uint32\x18! \x03(\r\x12\x17\n\x0frepeated_uint64\x18\" \x03(\x04\x12\x17\n\x0frepeated_sint32\x18# \x03(\x11\x12\x17\n\x0frepeated_sint64\x18$ \x03(\x12\x12\x18\n\x10repeated_fixed32\x18% \x03(\x07\x12\x18\n\x10repeated_fixed64\x18& \x03(\x06\x12\x19\n\x11repeated_sfixed32\x18\' \x03(\x0f\x12\x19\n\x11repeated_sfixed64\x18( \x03(\x10\x12\x16\n\x0erepeated_float\x18) \x03(\x02\x12\x17\n\x0frepeated_double\x18* \x03(\x01\x12\x15\n\rrepeated_bool\x18+ \x03(\x08\x12\x17\n\x0frepeated_string\x18, \x03(\t\x12\x16\n\x0erepeated_bytes\x18- \x03(\x0c\x12Q\n\x17repeated_nested_message\x18\x30 \x03(\x0b\x32\x30.proto3_lite_unittest.TestAllTypes.NestedMessage\x12\x46\n\x18repeated_foreign_message\x18\x31 \x03(\x0b\x32$.proto3_lite_unittest.ForeignMessage\x12H\n\x17repeated_import_message\x18\x32 \x03(\x0b\x32\'.protobuf_unittest_import.ImportMessage\x12K\n\x14repeated_nested_enum\x18\x33 \x03(\x0e\x32-.proto3_lite_unittest.TestAllTypes.NestedEnum\x12@\n\x15repeated_foreign_enum\x18\x34 \x03(\x0e\x32!.proto3_lite_unittest.ForeignEnum\x12!\n\x15repeated_string_piece\x18\x36 \x03(\tB\x02\x08\x02\x12\x19\n\rrepeated_cord\x18\x37 \x03(\tB\x02\x08\x01\x12S\n\x15repeated_lazy_message\x18\x39 \x03(\x0b\x32\x30.proto3_lite_unittest.TestAllTypes.NestedMessageB\x02(\x01\x12\x16\n\x0coneof_uint32\x18o \x01(\rH\x00\x12P\n\x14oneof_nested_message\x18p \x01(\x0b\x32\x30.proto3_lite_unittest.TestAllTypes.NestedMessageH\x00\x12\x16\n\x0coneof_string\x18q \x01(\tH\x00\x12\x15\n\x0boneof_bytes\x18r \x01(\x0cH\x00\x1a\x1b\n\rNestedMessage\x12\n\n\x02\x62\x62\x18\x01 \x01(\x05\"C\n\nNestedEnum\x12\x08\n\x04ZERO\x10\x00\x12\x07\n\x03\x46OO\x10\x01\x12\x07\n\x03\x42\x41R\x10\x02\x12\x07\n\x03\x42\x41Z\x10\x03\x12\x10\n\x03NEG\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01\x42\r\n\x0boneof_field\"\xad\x03\n\x0fTestPackedTypes\x12\x18\n\x0cpacked_int32\x18Z \x03(\x05\x42\x02\x10\x01\x12\x18\n\x0cpacked_int64\x18[ \x03(\x03\x42\x02\x10\x01\x12\x19\n\rpacked_uint32\x18\\ \x03(\rB\x02\x10\x01\x12\x19\n\rpacked_uint64\x18] \x03(\x04\x42\x02\x10\x01\x12\x19\n\rpacked_sint32\x18^ \x03(\x11\x42\x02\x10\x01\x12\x19\n\rpacked_sint64\x18_ \x03(\x12\x42\x02\x10\x01\x12\x1a\n\x0epacked_fixed32\x18` \x03(\x07\x42\x02\x10\x01\x12\x1a\n\x0epacked_fixed64\x18\x61 \x03(\x06\x42\x02\x10\x01\x12\x1b\n\x0fpacked_sfixed32\x18\x62 \x03(\x0f\x42\x02\x10\x01\x12\x1b\n\x0fpacked_sfixed64\x18\x63 \x03(\x10\x42\x02\x10\x01\x12\x18\n\x0cpacked_float\x18\x64 \x03(\x02\x42\x02\x10\x01\x12\x19\n\rpacked_double\x18\x65 \x03(\x01\x42\x02\x10\x01\x12\x17\n\x0bpacked_bool\x18\x66 \x03(\x08\x42\x02\x10\x01\x12:\n\x0bpacked_enum\x18g \x03(\x0e\x32!.proto3_lite_unittest.ForeignEnumB\x02\x10\x01\"\xde\x03\n\x11TestUnpackedTypes\x12\x1a\n\x0erepeated_int32\x18\x01 \x03(\x05\x42\x02\x10\x00\x12\x1a\n\x0erepeated_int64\x18\x02 \x03(\x03\x42\x02\x10\x00\x12\x1b\n\x0frepeated_uint32\x18\x03 \x03(\rB\x02\x10\x00\x12\x1b\n\x0frepeated_uint64\x18\x04 \x03(\x04\x42\x02\x10\x00\x12\x1b\n\x0frepeated_sint32\x18\x05 \x03(\x11\x42\x02\x10\x00\x12\x1b\n\x0frepeated_sint64\x18\x06 \x03(\x12\x42\x02\x10\x00\x12\x1c\n\x10repeated_fixed32\x18\x07 \x03(\x07\x42\x02\x10\x00\x12\x1c\n\x10repeated_fixed64\x18\x08 \x03(\x06\x42\x02\x10\x00\x12\x1d\n\x11repeated_sfixed32\x18\t \x03(\x0f\x42\x02\x10\x00\x12\x1d\n\x11repeated_sfixed64\x18\n \x03(\x10\x42\x02\x10\x00\x12\x1a\n\x0erepeated_float\x18\x0b \x03(\x02\x42\x02\x10\x00\x12\x1b\n\x0frepeated_double\x18\x0c \x03(\x01\x42\x02\x10\x00\x12\x19\n\rrepeated_bool\x18\r \x03(\x08\x42\x02\x10\x00\x12O\n\x14repeated_nested_enum\x18\x0e \x03(\x0e\x32-.proto3_lite_unittest.TestAllTypes.NestedEnumB\x02\x10\x00\"\x82\x01\n\x12NestedTestAllTypes\x12\x37\n\x05\x63hild\x18\x01 \x01(\x0b\x32(.proto3_lite_unittest.NestedTestAllTypes\x12\x33\n\x07payload\x18\x02 \x01(\x0b\x32\".proto3_lite_unittest.TestAllTypes\"\x1b\n\x0e\x46oreignMessage\x12\t\n\x01\x63\x18\x01 \x01(\x05\"\x12\n\x10TestEmptyMessage*R\n\x0b\x46oreignEnum\x12\x10\n\x0c\x46OREIGN_ZERO\x10\x00\x12\x0f\n\x0b\x46OREIGN_FOO\x10\x04\x12\x0f\n\x0b\x46OREIGN_BAR\x10\x05\x12\x0f\n\x0b\x46OREIGN_BAZ\x10\x06\x42\x02H\x03\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'google.protobuf.unittest_proto3_lite_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'H\003'
  _globals['_TESTALLTYPES'].fields_by_name['optional_string_piece']._loaded_options = None
  _globals['_TESTALLTYPES'].fields_by_name['optional_string_piece']._serialized_options = b'\010\002'
  _globals['_TESTALLTYPES'].fields_by_name['optional_cord']._loaded_options = None
  _globals['_TESTALLTYPES'].fields_by_name['optional_cord']._serialized_options = b'\010\001'
  _globals['_TESTALLTYPES'].fields_by_name['optional_lazy_message']._loaded_options = None
  _globals['_TESTALLTYPES'].fields_by_name['optional_lazy_message']._serialized_options = b'(\001'
  _globals['_TESTALLTYPES'].fields_by_name['repeated_string_piece']._loaded_options = None
  _globals['_TESTALLTYPES'].fields_by_name['repeated_string_piece']._serialized_options = b'\010\002'
  _globals['_TESTALLTYPES'].fields_by_name['repeated_cord']._loaded_options = None
  _globals['_TESTALLTYPES'].fields_by_name['repeated_cord']._serialized_options = b'\010\001'
  _globals['_TESTALLTYPES'].fields_by_name['repeated_lazy_message']._loaded_options = None
  _globals['_TESTALLTYPES'].fields_by_name['repeated_lazy_message']._serialized_options = b'(\001'
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_int32']._loaded_options = None
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_int32']._serialized_options = b'\020\001'
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_int64']._loaded_options = None
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_int64']._serialized_options = b'\020\001'
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_uint32']._loaded_options = None
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_uint32']._serialized_options = b'\020\001'
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_uint64']._loaded_options = None
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_uint64']._serialized_options = b'\020\001'
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_sint32']._loaded_options = None
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_sint32']._serialized_options = b'\020\001'
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_sint64']._loaded_options = None
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_sint64']._serialized_options = b'\020\001'
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_fixed32']._loaded_options = None
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_fixed32']._serialized_options = b'\020\001'
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_fixed64']._loaded_options = None
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_fixed64']._serialized_options = b'\020\001'
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_sfixed32']._loaded_options = None
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_sfixed32']._serialized_options = b'\020\001'
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_sfixed64']._loaded_options = None
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_sfixed64']._serialized_options = b'\020\001'
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_float']._loaded_options = None
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_float']._serialized_options = b'\020\001'
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_double']._loaded_options = None
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_double']._serialized_options = b'\020\001'
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_bool']._loaded_options = None
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_bool']._serialized_options = b'\020\001'
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_enum']._loaded_options = None
  _globals['_TESTPACKEDTYPES'].fields_by_name['packed_enum']._serialized_options = b'\020\001'
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_int32']._loaded_options = None
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_int32']._serialized_options = b'\020\000'
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_int64']._loaded_options = None
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_int64']._serialized_options = b'\020\000'
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_uint32']._loaded_options = None
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_uint32']._serialized_options = b'\020\000'
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_uint64']._loaded_options = None
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_uint64']._serialized_options = b'\020\000'
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_sint32']._loaded_options = None
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_sint32']._serialized_options = b'\020\000'
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_sint64']._loaded_options = None
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_sint64']._serialized_options = b'\020\000'
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_fixed32']._loaded_options = None
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_fixed32']._serialized_options = b'\020\000'
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_fixed64']._loaded_options = None
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_fixed64']._serialized_options = b'\020\000'
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_sfixed32']._loaded_options = None
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_sfixed32']._serialized_options = b'\020\000'
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_sfixed64']._loaded_options = None
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_sfixed64']._serialized_options = b'\020\000'
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_float']._loaded_options = None
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_float']._serialized_options = b'\020\000'
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_double']._loaded_options = None
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_double']._serialized_options = b'\020\000'
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_bool']._loaded_options = None
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_bool']._serialized_options = b'\020\000'
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_nested_enum']._loaded_options = None
  _globals['_TESTUNPACKEDTYPES'].fields_by_name['repeated_nested_enum']._serialized_options = b'\020\000'
  _globals['_FOREIGNENUM']._serialized_start=3360
  _globals['_FOREIGNENUM']._serialized_end=3442
  _globals['_TESTALLTYPES']._serialized_start=108
  _globals['_TESTALLTYPES']._serialized_end=2263
  _globals['_TESTALLTYPES_NESTEDMESSAGE']._serialized_start=2152
  _globals['_TESTALLTYPES_NESTEDMESSAGE']._serialized_end=2179
  _globals['_TESTALLTYPES_NESTEDENUM']._serialized_start=2181
  _globals['_TESTALLTYPES_NESTEDENUM']._serialized_end=2248
  _globals['_TESTPACKEDTYPES']._serialized_start=2266
  _globals['_TESTPACKEDTYPES']._serialized_end=2695
  _globals['_TESTUNPACKEDTYPES']._serialized_start=2698
  _globals['_TESTUNPACKEDTYPES']._serialized_end=3176
  _globals['_NESTEDTESTALLTYPES']._serialized_start=3179
  _globals['_NESTEDTESTALLTYPES']._serialized_end=3309
  _globals['_FOREIGNMESSAGE']._serialized_start=3311
  _globals['_FOREIGNMESSAGE']._serialized_end=3338
  _globals['_TESTEMPTYMESSAGE']._serialized_start=3340
  _globals['_TESTEMPTYMESSAGE']._serialized_end=3358
# @@protoc_insertion_point(module_scope)
