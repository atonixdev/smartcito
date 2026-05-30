#ifndef ORCA_INIT_H
#define ORCA_INIT_H

#include <stddef.h>
#include <stdint.h>

#include "orca_drivers.h"
#include "orca_platform.h"

#define ORCA_MAX_SYSTEM_SERVICES 8
#define ORCA_MAX_BOOT_PASSES 4

typedef enum {
    ORCA_SERVICE_NET = 0,
    ORCA_SERVICE_VISION = 1,
    ORCA_SERVICE_CORE = 2,
    ORCA_SERVICE_SECURITY = 3,
    ORCA_SERVICE_UPDATE = 4,
} orca_service_id;

typedef enum {
    ORCA_SERVICE_READY = 0,
    ORCA_SERVICE_DEFERRED = 1,
    ORCA_SERVICE_BLOCKED = 2,
} orca_service_boot_status;

typedef uint32_t orca_service_dependency_mask;

#define ORCA_SERVICE_BIT(id) (1u << (id))

typedef struct {
    orca_service_id id;
    orca_component_descriptor component;
    const char* boot_stage;
    orca_driver_capability_mask required_capabilities;
    orca_service_dependency_mask dependency_mask;
    orca_service_boot_status (*start)(void);
} orca_service_descriptor;

typedef struct {
    const orca_service_descriptor* service;
    orca_service_boot_status status;
    orca_driver_capability_mask missing_capabilities;
    orca_service_dependency_mask waiting_on_services;
    orca_boot_phase resolved_phase;
    size_t attempts;
} orca_service_boot_record;

typedef struct {
    orca_boot_phase phase;
    size_t services_ready;
    size_t services_deferred;
} orca_boot_phase_record;

typedef struct {
    const char* default_target;
    size_t max_boot_passes;
    uint8_t retry_deferred_services;
    orca_service_dependency_mask enabled_service_mask;
    orca_service_id preferred_order[ORCA_MAX_SYSTEM_SERVICES];
    size_t preferred_order_count;
} orca_init_boot_policy;

const orca_component_descriptor* orca_get_system_service_components(size_t* component_count);
const orca_service_descriptor* const* orca_get_system_services(size_t* service_count);
const orca_init_boot_policy* orca_get_init_boot_policy(void);
size_t orca_boot_system_services(
    orca_service_boot_record* records,
    size_t capacity,
    orca_boot_phase_record* phase_records,
    size_t phase_capacity,
    size_t* phase_count
);
const char* orca_service_token(orca_service_id id);

#endif