#include "orca_init.h"

#include "services/orca_core.h"
#include "services/orca_net.h"
#include "services/orca_security.h"
#include "services/orca_update.h"
#include "services/orca_vision.h"

static const orca_service_descriptor* const SYSTEM_SERVICES[] = {
    &ORCA_NET_SERVICE,
    &ORCA_VISION_SERVICE,
    &ORCA_CORE_SERVICE,
    &ORCA_SECURITY_SERVICE,
    &ORCA_UPDATE_SERVICE,
};

static orca_component_descriptor system_service_components[
    sizeof(SYSTEM_SERVICES) / sizeof(SYSTEM_SERVICES[0])
];
static int system_service_components_initialized = 0;

static void initialize_system_service_components(void) {
    size_t i = 0;

    if (system_service_components_initialized != 0) {
        return;
    }

    for (i = 0; i < sizeof(SYSTEM_SERVICES) / sizeof(SYSTEM_SERVICES[0]); ++i) {
        system_service_components[i] = SYSTEM_SERVICES[i]->component;
    }

    system_service_components_initialized = 1;
}

const orca_component_descriptor* orca_get_system_service_components(size_t* component_count) {
    initialize_system_service_components();
    if (component_count != 0) {
        *component_count = sizeof(system_service_components) / sizeof(system_service_components[0]);
    }
    return system_service_components;
}

const orca_service_descriptor* const* orca_get_system_services(size_t* service_count) {
    if (service_count != 0) {
        *service_count = sizeof(SYSTEM_SERVICES) / sizeof(SYSTEM_SERVICES[0]);
    }
    return SYSTEM_SERVICES;
}

const char* orca_service_token(orca_service_id id) {
    switch (id) {
        case ORCA_SERVICE_NET:
            return "net";
        case ORCA_SERVICE_VISION:
            return "vis";
        case ORCA_SERVICE_CORE:
            return "core";
        case ORCA_SERVICE_SECURITY:
            return "sec";
        case ORCA_SERVICE_UPDATE:
            return "upd";
        default:
            return "unk";
    }
}

size_t orca_boot_system_services(
    orca_service_boot_record* records,
    size_t capacity,
    orca_boot_phase_record* phase_records,
    size_t phase_capacity,
    size_t* phase_count
) {
    size_t available = sizeof(SYSTEM_SERVICES) / sizeof(SYSTEM_SERVICES[0]);
    size_t count = capacity < available ? capacity : available;
    orca_boot_phase phases[] = {
        ORCA_BOOT_PHASE_EARLY,
        ORCA_BOOT_PHASE_MEMORY,
        ORCA_BOOT_PHASE_INTERRUPTS,
        ORCA_BOOT_PHASE_SERVICES,
    };
    orca_service_dependency_mask started_services = 0;
    size_t i = 0;
    size_t phase_index = 0;
    size_t local_phase_count = 0;

    for (i = 0; i < count; ++i) {
        records[i].service = SYSTEM_SERVICES[i];
        records[i].status = ORCA_SERVICE_DEFERRED;
        records[i].missing_capabilities = SYSTEM_SERVICES[i]->required_capabilities;
        records[i].waiting_on_services = SYSTEM_SERVICES[i]->dependency_mask;
        records[i].resolved_phase = ORCA_BOOT_PHASE_EARLY;
        records[i].attempts = 0;
    }

    for (phase_index = 0; phase_index < sizeof(phases) / sizeof(phases[0]); ++phase_index) {
        orca_driver_capability_mask capabilities = 0;
        size_t pass = 0;
        size_t ready_count = 0;
        size_t deferred_count = 0;
        int progressed = 0;

        orca_driver_transition_phase(phases[phase_index]);
        capabilities = orca_get_driver_capabilities();

        for (pass = 0; pass < ORCA_MAX_BOOT_PASSES; ++pass) {
            int pass_progressed = 0;

            for (i = 0; i < count; ++i) {
                if (records[i].status == ORCA_SERVICE_READY) {
                    continue;
                }

                ++records[i].attempts;
                records[i].missing_capabilities =
                    SYSTEM_SERVICES[i]->required_capabilities & ~capabilities;
                records[i].waiting_on_services =
                    SYSTEM_SERVICES[i]->dependency_mask & ~started_services;
                records[i].resolved_phase = phases[phase_index];

                if (records[i].missing_capabilities != 0 || records[i].waiting_on_services != 0) {
                    records[i].status = ORCA_SERVICE_DEFERRED;
                    continue;
                }

                records[i].status = SYSTEM_SERVICES[i]->start();
                if (records[i].status == ORCA_SERVICE_READY) {
                    started_services |= ORCA_SERVICE_BIT(SYSTEM_SERVICES[i]->id);
                    pass_progressed = 1;
                    progressed = 1;
                }
            }

            if (pass_progressed == 0) {
                break;
            }
        }

        for (i = 0; i < count; ++i) {
            if (records[i].status == ORCA_SERVICE_READY) {
                ++ready_count;
            } else {
                ++deferred_count;
            }
        }

        if (phase_records != 0 && local_phase_count < phase_capacity) {
            phase_records[local_phase_count].phase = phases[phase_index];
            phase_records[local_phase_count].services_ready = ready_count;
            phase_records[local_phase_count].services_deferred = deferred_count;
            ++local_phase_count;
        }

        if (deferred_count == 0 || progressed == 0) {
            continue;
        }
    }

    if (phase_count != 0) {
        *phase_count = local_phase_count;
    }

    return count;
}