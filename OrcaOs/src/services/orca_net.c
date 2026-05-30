#include "services/orca_net.h"

static orca_service_boot_status orca_net_start(void) {
    return ORCA_SERVICE_READY;
}

const orca_service_descriptor ORCA_NET_SERVICE = {
    ORCA_SERVICE_NET,
    {"ORCA-Net", "Policy-aware networking and secure transport"},
    "bootstrap-network",
    ORCA_DRIVER_CAPABILITY_NETWORK,
    0,
    orca_net_start,
};