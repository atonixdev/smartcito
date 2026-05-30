# Prototyping Path

Suggested starting points for contributors building proof-of-concept hardware.

## Body Camera Prototype

- Raspberry Pi or Jetson-class board
- camera sensor with hardware encode support
- u-blox GNSS module
- LTE/5G modem or Wi-Fi 6 adapter
- secure enclosure with tamper switch
- battery pack sized for target duty cycle

## Micro Camera Prototype

- compact ESP32-S3, CM4, or equivalent board depending stream requirements
- compact image sensor
- Hall-effect sensor plus magnetic base
- rechargeable micro-battery and charging controller
- lightweight casing optimized for heat dissipation

## Firmware Targets

- C for device drivers and tight hardware loops
- Python for prototyping on Linux-based devices
- signed release artifacts where feasible

## Contribution Rules

- document BOM and assembly steps
- include wiring diagrams and firmware flashing procedure
- never hardcode credentials in firmware examples
- keep all security-relevant assumptions explicit
