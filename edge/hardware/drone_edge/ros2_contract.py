from __future__ import annotations


def build_ros2_node_contract() -> dict[str, object]:
    return {
        "runtime": {
            "middleware": "ROS2",
            "distribution": "Humble-or-newer",
            "deployment_surface": "companion computer",
            "bridge_goal": "publish autonomy outputs into the Orca edge runtime for Drone Gateway, Mission Control, Mapping, and Camera Service.",
        },
        "nodes": [
            {
                "name": "orca_slam_node",
                "purpose": "Local SLAM and map-frame localization for contested GPS or urban canyon conditions.",
                "subscribes": ["/camera/image_raw", "/imu/data", "/gps/fix"],
                "publishes": ["/orca/slam/pose", "/orca/slam/quality", "/orca/slam/local_map"],
                "orca_mapping": {
                    "edge_output": "pose confidence and local map summary",
                    "cloud_use": "map overlay correction, route confidence, operator audit trail",
                },
            },
            {
                "name": "orca_obstacle_avoidance_node",
                "purpose": "Consumes local perception feeds and emits safe-flight constraints and reroute advisories.",
                "subscribes": ["/camera/depth", "/lidar/points", "/orca/slam/pose", "/mavros/local_position/pose"],
                "publishes": ["/orca/avoidance/vector", "/orca/avoidance/hazard", "/orca/avoidance/recommended_path"],
                "orca_mapping": {
                    "edge_output": "hazard vectors and reroute proposals",
                    "cloud_use": "mission review, geofence exception logging, dashboard threat context",
                },
            },
            {
                "name": "orca_visual_odometry_node",
                "purpose": "Produces frame-to-frame motion estimates and dead-reckoning support for navigation continuity.",
                "subscribes": ["/camera/image_raw", "/imu/data"],
                "publishes": ["/orca/vo/pose", "/orca/vo/twist", "/orca/vo/confidence"],
                "orca_mapping": {
                    "edge_output": "pose delta and confidence",
                    "cloud_use": "telemetry enrichment, flight replay, operator confidence scoring",
                },
            },
        ],
        "cloud_publish_contract": {
            "telemetry_fields": [
                "pose_confidence",
                "slam_status",
                "visual_odometry_status",
                "avoidance_state",
                "recommended_path_available",
            ],
            "transport": "Orca Drone SDK through Drone Gateway and Mapping/Threat services",
            "operator_surfaces": ["Mission Control", "Mapping and Geospatial", "Threat Detection", "Dashboard"],
        },
        "vendor_requirements": [
            "Manufacturer must provide enough CPU/GPU headroom for ROS2 SLAM, obstacle avoidance, and visual odometry.",
            "Companion computer image must allow Orca ROS2 package installation and service management.",
            "Camera, IMU, GPS, and optional depth/lidar data must be reachable from ROS2 user space.",
        ],
    }