# Firmware Physics Helpers

This folder provides C++ snippets intended for autopilot integration points
(PX4 / ArduPilot style control loops).

- `uav_forces.hpp` includes lift/drag/weight and pitch stabilization helpers.

Example:

```cpp
float lift = gpuops::compute_lift(rho, V, wing_area, CL);
float pitch_cmd = gpuops::pitch_stabilization_cmd(pitch_sp, pitch, pitch_rate, Kp, Kd);
```
