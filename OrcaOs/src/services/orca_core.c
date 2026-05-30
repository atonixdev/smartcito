#include "services/orca_core.h"

static orca_service_boot_status orca_core_start(void) {
    return ORCA_SERVICE_READY;
}

const orca_service_descriptor ORCA_CORE_SERVICE = {
    ORCA_SERVICE_CORE,
    {"ORCA-Core", "Decision engine and mission orchestration"},
    "start-decision-engine",
    0,
    ORCA_SERVICE_BIT(ORCA_SERVICE_NET) | ORCA_SERVICE_BIT(ORCA_SERVICE_VISION),
    orca_core_start,
};