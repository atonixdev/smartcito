#include "orca_drivers.h"

#include "orca_interrupts.h"
#include "orca_memory.h"

static orca_driver_descriptor ORCA_DRIVERS[] = {
    {"net0", "Edge uplink and secure transport", ORCA_DRIVER_CAPABILITY_NETWORK, ORCA_BOOT_PHASE_EARLY, 1},
    {"store0", "Boot storage and OTA target", ORCA_DRIVER_CAPABILITY_STORAGE, ORCA_BOOT_PHASE_INTERRUPTS, 0},
    {"sensor0", "Camera and sensor intake bus", ORCA_DRIVER_CAPABILITY_SENSORS, ORCA_BOOT_PHASE_EARLY, 1},
    {"crypto0", "Platform crypto and identity engine", ORCA_DRIVER_CAPABILITY_CRYPTO, ORCA_BOOT_PHASE_EARLY, 1},
    {"display0", "VGA and operator console output", ORCA_DRIVER_CAPABILITY_DISPLAY, ORCA_BOOT_PHASE_EARLY, 1},
};

const orca_driver_descriptor* orca_get_registered_drivers(size_t* driver_count) {
    if (driver_count != 0) {
        *driver_count = sizeof(ORCA_DRIVERS) / sizeof(ORCA_DRIVERS[0]);
    }
    return ORCA_DRIVERS;
}

orca_driver_capability_mask orca_get_driver_capabilities(void) {
    orca_driver_capability_mask capabilities = 0;
    size_t i = 0;

    for (i = 0; i < sizeof(ORCA_DRIVERS) / sizeof(ORCA_DRIVERS[0]); ++i) {
        if (ORCA_DRIVERS[i].ready != 0) {
            capabilities |= ORCA_DRIVERS[i].capability;
        }
    }

    return capabilities;
}

const char* orca_driver_capability_token(orca_driver_capability capability) {
    switch (capability) {
        case ORCA_DRIVER_CAPABILITY_NETWORK:
            return "net";
        case ORCA_DRIVER_CAPABILITY_STORAGE:
            return "sto";
        case ORCA_DRIVER_CAPABILITY_SENSORS:
            return "sns";
        case ORCA_DRIVER_CAPABILITY_CRYPTO:
            return "cry";
        case ORCA_DRIVER_CAPABILITY_DISPLAY:
            return "dsp";
        default:
            return "unk";
    }
}

const char* orca_boot_phase_token(orca_boot_phase phase) {
    switch (phase) {
        case ORCA_BOOT_PHASE_EARLY:
            return "early";
        case ORCA_BOOT_PHASE_MEMORY:
            return "memory";
        case ORCA_BOOT_PHASE_INTERRUPTS:
            return "irq";
        case ORCA_BOOT_PHASE_SERVICES:
            return "services";
        case ORCA_BOOT_PHASE_COMPLETE:
            return "done";
        default:
            return "unknown";
    }
}

void orca_driver_transition_phase(orca_boot_phase phase) {
    size_t i = 0;

    if (phase == ORCA_BOOT_PHASE_MEMORY) {
        (void)orca_memory_initialize();
    }
    if (phase == ORCA_BOOT_PHASE_INTERRUPTS) {
        (void)orca_interrupts_initialize();
    }

    for (i = 0; i < sizeof(ORCA_DRIVERS) / sizeof(ORCA_DRIVERS[0]); ++i) {
        if (ORCA_DRIVERS[i].capability == ORCA_DRIVER_CAPABILITY_STORAGE) {
            ORCA_DRIVERS[i].ready =
                phase >= ORCA_DRIVERS[i].ready_phase &&
                orca_memory_ready() != 0 &&
                orca_interrupts_ready() != 0;
            continue;
        }

        ORCA_DRIVERS[i].ready = phase >= ORCA_DRIVERS[i].ready_phase;
    }
}