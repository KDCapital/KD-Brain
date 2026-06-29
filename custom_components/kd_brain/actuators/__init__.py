"""Actuator layer: executes safety-approved actions on real devices.

Actuators drive existing Home Assistant control entities (e.g. a battery power
setpoint ``number``) via their own integrations, rather than KD Brain writing
raw Modbus/MQTT. This reuses the device integration's validated write path and
keeps KD Brain a safe orchestration layer.
"""
