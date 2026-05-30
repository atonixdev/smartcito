#include "services/orca_security.h"

static orca_service_boot_status orca_security_start(void) {
    return ORCA_SERVICE_READY;
}

const orca_service_descriptor ORCA_SECURITY_SERVICE = {
    ORCA_SERVICE_SECURITY,
    {"ORCA-Security", "Identity, encryption, firewall, and audit"},
    "enforce-platform-policy",
    ORCA_DRIVER_CAPABILITY_CRYPTO | ORCA_DRIVER_CAPABILITY_NETWORK,
    ORCA_SERVICE_BIT(ORCA_SERVICE_NET),
    orca_security_start,
};