# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: options.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\roptions.proto\"d\n\x0eObjectSettings\x12\x1a\n\x12input_service_name\x18\x01 \x01(\t\x12\x11\n\traspberry\x18\x02 \x01(\x08\x12\x12\n\nmodel_path\x18\x03 \x01(\t\x12\x0f\n\x07\x63\x61meras\x18\x04 \x03(\x03\"x\n\x15ObjectDetectorOptions\x12\x14\n\x0cservice_name\x18\x01 \x01(\t\x12\x14\n\x0crabbitmq_uri\x18\x02 \x01(\t\x12\x12\n\nzipkin_uri\x18\x03 \x01(\t\x12\x1f\n\x06\x63onfig\x18\x04 \x01(\x0b\x32\x0f.ObjectSettingsb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'options_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _OBJECTSETTINGS._serialized_start=17
  _OBJECTSETTINGS._serialized_end=117
  _OBJECTDETECTOROPTIONS._serialized_start=119
  _OBJECTDETECTOROPTIONS._serialized_end=239
# @@protoc_insertion_point(module_scope)
