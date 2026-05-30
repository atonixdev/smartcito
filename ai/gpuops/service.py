"""Minimal FastAPI service exposing the JAX intelligence engine contract."""

from __future__ import annotations

from fastapi import FastAPI

from gpuops.intelligence.camera import depth_from_disparity, extract_grad_features, optical_flow_delta, optimize_focal_length, preprocess_image, segment_by_threshold
from gpuops.intelligence.distance import ekf_predict_uav, fuse_uav_sensors, gps_fusion, kalman_predict, kalman_update, particle_filter_predict, particle_filter_update, slam_pose_step
from gpuops.intelligence.mapping import astar_score, dijkstra_relaxation, rrt_expand, rrt_star_rewire
from gpuops.intelligence.optimization import batch_gradient_descent, gradient_descent
from gpuops.intelligence.physics import aerodynamic_force_vectors, batch_compute_lift, batch_net_force, body_moment_vector, compute_drag, compute_lift, compute_thrust, compute_thrust_vector, compute_torque, compute_weight, lift_coefficient_with_stall, net_force, optimize_control_signals, rigid_body_step, rollout_trajectory, simulate_uav_rollout, simulate_uav_step
from gpuops.intelligence.robotics import altitude_hold_pitch_command, batch_pitch_stabilization, diff_drive_kinematics, mpc_optimize_controls, pid_step, pitch_stabilization_command, roll_stabilization_command, rollout_dynamics, waypoint_guidance_heading, yaw_stabilization_command
from gpuops.intelligence.solvers import batch_pairwise_distance, interception_vector, predict_constant_velocity, required_intercept_speed, shortest_path_scores
from gpuops.intelligence.utils import cv2_frame_to_jax, jax_to_torch_dlpack, px4_setpoint_from_control, ros2_command_from_control, torch_to_jax_dlpack

app = FastAPI(title="Orca GPUOPS")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "gpuops"}


@app.get("/gpuops/contract")
async def gpuops_contract() -> dict[str, object]:
    return {
        "physics": [
            "compute_lift",
            "batch_compute_lift",
            "compute_drag",
            "compute_thrust",
            "compute_torque",
            "rigid_body_step",
            "rollout_trajectory",
            "optimize_control_signals",
            "compute_weight",
            "compute_thrust_vector",
            "lift_coefficient_with_stall",
            "aerodynamic_force_vectors",
            "body_moment_vector",
            "net_force",
            "batch_net_force",
            "simulate_uav_step",
            "simulate_uav_rollout",
        ],
        "robotics": [
            "diff_drive_kinematics",
            "pid_step",
            "rollout_dynamics",
            "mpc_optimize_controls",
            "pitch_stabilization_command",
            "roll_stabilization_command",
            "yaw_stabilization_command",
            "altitude_hold_pitch_command",
            "waypoint_guidance_heading",
            "batch_pitch_stabilization",
        ],
        "distance": [
            "kalman_predict",
            "kalman_update",
            "particle_filter_predict",
            "particle_filter_update",
            "gps_fusion",
            "slam_pose_step",
            "ekf_predict_uav",
            "fuse_uav_sensors",
        ],
        "mapping": ["astar_score", "dijkstra_relaxation", "rrt_expand", "rrt_star_rewire"],
        "solvers": [
            "shortest_path_scores",
            "batch_pairwise_distance",
            "predict_constant_velocity",
            "interception_vector",
            "required_intercept_speed",
        ],
        "optimization": ["gradient_descent", "batch_gradient_descent"],
        "camera": [
            "preprocess_image",
            "extract_grad_features",
            "optical_flow_delta",
            "segment_by_threshold",
            "depth_from_disparity",
            "optimize_focal_length",
        ],
        "utils": [
            "cv2_frame_to_jax",
            "torch_to_jax_dlpack",
            "jax_to_torch_dlpack",
            "ros2_command_from_control",
            "px4_setpoint_from_control",
        ],
    }