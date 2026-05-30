#include "services/orca_vision.h"

static orca_service_boot_status orca_vision_start(void) {
    return ORCA_SERVICE_READY;
}

const orca_service_descriptor ORCA_VISION_SERVICE = {
    ORCA_SERVICE_VISION,
    {"ORCA-Vision", "Camera, sensor, and perception ingestion"},
    "discover-sensors",
    ORCA_DRIVER_CAPABILITY_SENSORS,
    0,
    orca_vision_start,
};