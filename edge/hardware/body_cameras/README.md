# Body Cameras

Reference design for Orca body-worn cameras.

## Capabilities

- integrated GPS / GNSS module for continuous location updates
- secure wireless backhaul via LTE, 5G, or Wi-Fi 6
- encrypted local storage using AES-256
- tamper-resistant enclosure with open-case and power-loss events
- direct API registration into the Orca backbone

## Reference Build

- SBC or embedded compute board with hardware video encode support
- camera sensor with low-light support and hardware timestamping
- GNSS module from u-blox or Broadcom families
- LTE/5G modem or Wi-Fi 6 radio depending on deployment zone
- secure element or TPM for device identity and key storage
- removable or sealed battery pack depending operational policy

## Telemetry

A body camera should emit:
- device heartbeat
- stream status
- GPS position
- tamper events
- battery and storage state
- mount / unmount state when attached to magnetic docking hardware

## Integration Path

- stream video into [`../../camera_module/`](../../camera_module/)
- publish location into [`../../gps_module/`](../../gps_module/)
- register and rotate credentials via [`../api_connectors/`](../api_connectors/)
- enforce hardware security controls from [`../security/`](../security/)

## Prototype Path

Start with an off-the-shelf kit:
- Raspberry Pi or Jetson Nano-class board
- CSI or USB camera
- u-blox GNSS module
- LTE HAT or Wi-Fi 6 adapter

Document firmware and housing iterations in this folder as the design matures.
