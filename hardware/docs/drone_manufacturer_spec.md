# Orca Drone Manufacturer Specification And RFP Packet

This document is the manufacturer-facing hardware specification and RFP packet structure for a Orca-compatible drone platform.

The delivery model is explicit: the manufacturer builds the airframe and electronics, while the Orca team owns the companion-computer software, MAVLink integration, camera behavior, ROS2 autonomy software, and the Orca cloud services.

## Cover Page

- Document: Orca Drone Platform RFP Packet
- Program: Orca drone airframe and electronics procurement
- Delivery model: manufacturer builds body and electronics; Orca owns software and cloud
- Response requested: prototype and pilot-batch proposal

## Executive Summary

Orca is procuring a drone platform that supports PX4 or ArduPilot,
MAVLink, a Orca-controlled companion computer, RGB or thermal or zoom
camera integration, and secure cloud uplink over 4G, 5G, or WiFi.

The manufacturer is expected to deliver the physical platform and electronics.
Orca retains control of the companion-computer software stack, including
ROS2 autonomy nodes, the Orca Drone SDK, camera streaming behavior, and
all cloud-side services.

## 1. Reference Architecture

Required architecture:

- PX4 or ArduPilot flight stack on the flight controller
- Companion computer connected to the flight controller over UART, USB, or Ethernet
- RGB, thermal, or zoom camera connected to the companion computer
- 4G, 5G, or WiFi connectivity from the companion computer to the Orca cloud
- MAVLink telemetry and mission upload available from the companion computer
- RTSP, WebRTC, or Orca-approved custom video uplink from the companion computer

High-level path:

1. Camera connects to companion computer.
2. Companion computer encodes video as H.264 or H.265.
3. Companion computer streams video to Orca Camera Service.
4. Camera Service runs AI and threat detection.
5. Results flow to the dashboard through the Orca cloud.

## 1A. ROS2 Autonomy Node Contract

The companion computer must support Orca-owned ROS2 nodes for:

- SLAM
- obstacle avoidance
- visual odometry

These nodes must be installable and operable by the Orca team. Required
runtime access includes:

- camera frames
- IMU data
- GPS data
- optional depth or lidar feeds when present

These nodes publish into the Orca edge runtime and ultimately feed:

- Drone Gateway telemetry enrichment
- Mission Control path confidence and reroute context
- Mapping and Geospatial overlays
- Dashboard operator confidence and audit trails

## 2. Flight Stack Requirements

- Autopilot must use PX4 or ArduPilot.
- MAVLink support is mandatory.
- The system must allow:
  - telemetry access from the companion computer
  - mission upload from the companion computer
  - command/control integration without closed vendor gateways
- Flight controller telemetry must expose at least:
  - GPS
  - IMU
  - barometer
  - magnetometer
  - battery status
  - flight mode
  - link quality or equivalent telemetry health data when available

## 3. Companion Computer Requirements

The companion computer is the Orca-owned software surface.

Minimum requirements:

- CPU/GPU suitable for:
  - ROS2 autonomy nodes
  - video encoding
  - optional edge AI inference
- RAM and storage sized for:
  - local logs
  - temporary video buffering
  - Orca SDK and ROS2 packages
- Physical interfaces:
  - Ethernet
  - USB
  - UART
  - modem interface for 4G/5G
  - WiFi

The Orca team must be able to:

- SSH into the companion computer
- install its own software
- run ROS2 nodes
- run a video streaming service
- access MAVLink directly from the companion computer

No locked-down vendor image is acceptable unless full Orca software installation rights remain intact.

## 4. Camera Requirements

Supported camera classes:

- RGB
- thermal
- zoom

Camera interface options:

- CSI
- USB
- HDMI
- MIPI

The camera must be fully accessible from the companion computer, including:

- frame capture
- encoder access
- stream configuration
- bitrate, FPS, and resolution tuning

Preferred video behavior:

- H.264 or H.265 encoding
- RTSP or WebRTC uplink
- configurable resolution and FPS
- support for operator preview and AI frame metadata publishing

## 5. Power and Form Factor

The manufacturer proposal must specify:

- battery size
- target flight time
- payload capacity
- thermal envelope for sustained companion-computer load
- mounting space for future sensors or radios

The form factor must allow maintenance access to:

- companion computer
- camera harnesses
- modem and network modules
- flight controller and telemetry wiring

## 6. Connectivity and Interfaces

The drone must support cloud connection through:

- 4G
- 5G
- WiFi

Required integration interfaces:

- MAVLink from flight controller to companion computer
- video uplink from companion computer to Orca Camera Service
- secure IP connectivity from companion computer to Orca cloud

## 7. Software Ownership Split

Manufacturer owns:

- airframe
- propulsion
- wiring harnesses
- power integration
- electronics packaging

Orca team owns:

- companion-computer software
- ROS2 autonomy nodes
- camera behavior software
- video streamer configuration
- Orca Drone SDK
- cloud services including Drone Gateway, Camera Service, Mission Control, and Dashboard

## 8. Engagement Workflow

Recommended process:

1. Share this architecture and specification document with manufacturers.
2. Ask whether they can build the airframe and electronics to this spec.
3. Keep software and cloud ownership with the Orca team.
4. Validate the delivered platform against PX4/ArduPilot, MAVLink, SSH access, camera accessibility, and Orca cloud integration.

## 9. Orca Acceptance Criteria

The platform is acceptable only if the Orca team can:

- SSH into the companion computer
- install its own SDK and ROS2 nodes
- access MAVLink from the companion computer
- encode and uplink camera streams from the companion computer
- register the drone and camera into Orca cloud services without vendor dependency

## 10. BOM Response Table

The vendor proposal must include at minimum these BOM fields:

- airframe model
- flight controller
- companion computer SKU
- CPU/GPU class
- RAM capacity
- storage capacity
- camera type
- camera interface
- camera resolution
- camera FPS
- modem type
- WiFi module
- battery capacity
- expected flight time
- payload capacity

## 11. Acceptance Test Checklist

The delivered platform will be checked against this acceptance list:

- PX4 or ArduPilot installed and bootable
- MAVLink reachable from companion computer user space
- Orca team can SSH into the companion computer
- Orca team can install its own SDK and ROS2 nodes
- camera is accessible for frame capture and H.264 or H.265 encoding
- RTSP or WebRTC uplink works from companion computer to Orca Camera Service
- telemetry, mission upload, and cloud registration work without vendor lock-in
- thermal and power envelope supports sustained autonomy and encode workloads

## 12. Vendor Response Questionnaire

The manufacturer response should answer:

1. Can you build the airframe and electronics to this specification while preserving Orca software control?
2. Which companion computer SKUs do you recommend for ROS2 plus H.265 encode workloads?
3. What payload and flight-time tradeoffs apply to RGB, thermal, and zoom camera options?
4. What prototype, pilot-batch, and production lead times apply?
5. What MOQ applies for prototype and pilot orders?