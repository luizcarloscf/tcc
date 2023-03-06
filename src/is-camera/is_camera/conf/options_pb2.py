# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: is_camera/conf/options.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='is_camera/conf/options.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x1cis_camera/conf/options.proto\"<\n\x06\x43\x61mera\x12\n\n\x02id\x18\x01 \x01(\r\x12\x0e\n\x06\x64\x65vice\x18\x02 \x01(\t\x12\x16\n\x0einitial_config\x18\x03 \x01(\t\"Y\n\x14\x43\x61meraGatewayOptions\x12\x14\n\x0crabbitmq_uri\x18\x01 \x01(\t\x12\x12\n\nzipkin_uri\x18\x02 \x01(\t\x12\x17\n\x06\x63\x61mera\x18\x03 \x01(\x0b\x32\x07.Camerab\x06proto3'
)




_CAMERA = _descriptor.Descriptor(
  name='Camera',
  full_name='Camera',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='Camera.id', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='device', full_name='Camera.device', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='initial_config', full_name='Camera.initial_config', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=32,
  serialized_end=92,
)


_CAMERAGATEWAYOPTIONS = _descriptor.Descriptor(
  name='CameraGatewayOptions',
  full_name='CameraGatewayOptions',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='rabbitmq_uri', full_name='CameraGatewayOptions.rabbitmq_uri', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='zipkin_uri', full_name='CameraGatewayOptions.zipkin_uri', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='camera', full_name='CameraGatewayOptions.camera', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=94,
  serialized_end=183,
)

_CAMERAGATEWAYOPTIONS.fields_by_name['camera'].message_type = _CAMERA
DESCRIPTOR.message_types_by_name['Camera'] = _CAMERA
DESCRIPTOR.message_types_by_name['CameraGatewayOptions'] = _CAMERAGATEWAYOPTIONS
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Camera = _reflection.GeneratedProtocolMessageType('Camera', (_message.Message,), {
  'DESCRIPTOR' : _CAMERA,
  '__module__' : 'is_camera.conf.options_pb2'
  # @@protoc_insertion_point(class_scope:Camera)
  })
_sym_db.RegisterMessage(Camera)

CameraGatewayOptions = _reflection.GeneratedProtocolMessageType('CameraGatewayOptions', (_message.Message,), {
  'DESCRIPTOR' : _CAMERAGATEWAYOPTIONS,
  '__module__' : 'is_camera.conf.options_pb2'
  # @@protoc_insertion_point(class_scope:CameraGatewayOptions)
  })
_sym_db.RegisterMessage(CameraGatewayOptions)


# @@protoc_insertion_point(module_scope)
