#pragma once

// Lightweight firmware-side physics helpers for PX4/ArduPilot modules.

namespace gpuops {

inline float compute_lift(float rho, float V, float S, float CL) {
    return 0.5f * rho * V * V * S * CL;
}

inline float compute_drag(float rho, float V, float S, float CD) {
    return 0.5f * rho * V * V * S * CD;
}

inline float compute_weight(float mass, float gravity = 9.81f) {
    return mass * gravity;
}

inline float pitch_stabilization_cmd(float pitch_setpoint, float pitch_angle, float pitch_rate, float Kp, float Kd) {
    float pitch_error = pitch_setpoint - pitch_angle;
    return Kp * pitch_error - Kd * pitch_rate;
}

}  // namespace gpuops
