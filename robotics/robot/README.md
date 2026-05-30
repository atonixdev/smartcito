# Orca Robot Stack

This package implements a modular robot intelligence stack for Orca.
It is organized around physics, sensors, perception, navigation, AI, cloud,
and ROS2 integration.

## Layout

- `robot/physics/` - traction, stability, energy, and motion dynamics
- `robot/sensors/` - sensor normalization and fusion contracts
- `robot/perception/` - obstacle, target, and terrain perception helpers
- `robot/navigation/` - planning, control, and localization
- `robot/ai/` - hybrid physics + AI helpers
- `robot/cloud/` - MQTT, gRPC, mission control, and streaming contracts
- `robot/ros2_ws/` - ROS2 workspace notes and integration hooks

## Install

```bash
pip install -r robot/requirements.txt
```

## Validate

```bash
PYTHONPATH=. python3 -m pytest tests/robot -q
```
