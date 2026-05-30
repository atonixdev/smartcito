#ifndef ORCA_DRIVERS_H
#define ORCA_DRIVERS_H

#include <stddef.h>
#include <stdint.h>

typedef uint32_t orca_driver_capability_mask;

typedef enum {
    ORCA_BOOT_PHASE_EARLY = 0,
    ORCA_BOOT_PHASE_MEMORY = 1,
    ORCA_BOOT_PHASE_INTERRUPTS = 2,
    ORCA_BOOT_PHASE_SERVICES = 3,
    ORCA_BOOT_PHASE_COMPLETE = 4,
} orca_boot_phase;

typedef enum {
    ORCA_DRIVER_CAPABILITY_NETWORK = 1u << 0,
    ORCA_DRIVER_CAPABILITY_STORAGE = 1u << 1,
    ORCA_DRIVER_CAPABILITY_SENSORS = 1u << 2,
    ORCA_DRIVER_CAPABILITY_CRYPTO = 1u << 3,
    ORCA_DRIVER_CAPABILITY_DISPLAY = 1u << 4,
} orca_driver_capability;

typedef struct {
    const char* name;
    const char* summary;
    orca_driver_capability capability;
    orca_boot_phase ready_phase;
    int ready;
} orca_driver_descriptor;

const orca_driver_descriptor* orca_get_registered_drivers(size_t* driver_count);
orca_driver_capability_mask orca_get_driver_capabilities(void);
const char* orca_driver_capability_token(orca_driver_capability capability);
const char* orca_boot_phase_token(orca_boot_phase phase);
void orca_driver_transition_phase(orca_boot_phase phase);

#endif