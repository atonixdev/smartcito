#include "services/orca_update.h"

static orca_service_boot_status orca_update_start(void) {
    return ORCA_SERVICE_DEFERRED;
}

const orca_service_descriptor ORCA_UPDATE_SERVICE = {
    ORCA_SERVICE_UPDATE,
    {"ORCA-Update", "OTA rollout, rollback, and image verification"},
    "verify-ota-target",
    ORCA_DRIVER_CAPABILITY_NETWORK | ORCA_DRIVER_CAPABILITY_STORAGE | ORCA_DRIVER_CAPABILITY_CRYPTO,
    ORCA_SERVICE_BIT(ORCA_SERVICE_NET) | ORCA_SERVICE_BIT(ORCA_SERVICE_SECURITY),
    orca_update_start,
};