# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: aquaticus_vehicle.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from . import node_report_pb2 as node__report__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='aquaticus_vehicle.proto',
  package='mivp_agent',
  syntax='proto2',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x17\x61quaticus_vehicle.proto\x12\nmivp_agent\x1a\x11node_report.proto\"a\n\x10\x41quaticusVehicle\x12\x0e\n\x06tagged\x18\x01 \x02(\x08\x12\x10\n\x08has_flag\x18\x02 \x02(\x08\x12+\n\x0bnode_report\x18\x03 \x02(\x0b\x32\x16.mivp_agent.NodeReport'
  ,
  dependencies=[node__report__pb2.DESCRIPTOR,])




_AQUATICUSVEHICLE = _descriptor.Descriptor(
  name='AquaticusVehicle',
  full_name='mivp_agent.AquaticusVehicle',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='tagged', full_name='mivp_agent.AquaticusVehicle.tagged', index=0,
      number=1, type=8, cpp_type=7, label=2,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='has_flag', full_name='mivp_agent.AquaticusVehicle.has_flag', index=1,
      number=2, type=8, cpp_type=7, label=2,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='node_report', full_name='mivp_agent.AquaticusVehicle.node_report', index=2,
      number=3, type=11, cpp_type=10, label=2,
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
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=58,
  serialized_end=155,
)

_AQUATICUSVEHICLE.fields_by_name['node_report'].message_type = node__report__pb2._NODEREPORT
DESCRIPTOR.message_types_by_name['AquaticusVehicle'] = _AQUATICUSVEHICLE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

AquaticusVehicle = _reflection.GeneratedProtocolMessageType('AquaticusVehicle', (_message.Message,), {
  'DESCRIPTOR' : _AQUATICUSVEHICLE,
  '__module__' : 'aquaticus_vehicle_pb2'
  # @@protoc_insertion_point(class_scope:mivp_agent.AquaticusVehicle)
  })
_sym_db.RegisterMessage(AquaticusVehicle)


# @@protoc_insertion_point(module_scope)