#include "orca_init.h"

#include "orca_handoff.h"
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
static orca_init_boot_policy ORCA_INIT_BOOT_POLICY = {
    "orca-core.target",
    ORCA_MAX_BOOT_PASSES,
    1u,
    0u,
    { ORCA_SERVICE_NET, ORCA_SERVICE_VISION, ORCA_SERVICE_CORE, ORCA_SERVICE_SECURITY, ORCA_SERVICE_UPDATE, 0u, 0u, 0u },
    sizeof(SYSTEM_SERVICES) / sizeof(SYSTEM_SERVICES[0])
};
static int orca_init_boot_policy_initialized = 0;

static size_t string_length(const char* value) {
    size_t length = 0;

    while (value[length] != '\0') {
        ++length;
    }

    return length;
}

static int string_equals(const char* left, const char* right) {
    size_t i = 0;

    while (left[i] != '\0' && right[i] != '\0') {
        if (left[i] != right[i]) {
            return 0;
        }
        ++i;
    }

    return left[i] == right[i];
}


static int config_value_equals(const orca_config_value_view* value, const char* expected) {
    size_t expected_length = string_length(expected);
    size_t i = 0;

    if (value->found == 0u || value->size != expected_length) {
        return 0;
    }

    for (i = 0; i < expected_length; ++i) {
        if ((char)value->value[i] != expected[i]) {
            return 0;
        }
    }

    return 1;
}

static size_t parse_unsigned_decimal_value(const orca_config_value_view* value, size_t fallback) {
    size_t parsed = 0;
    size_t i = 0;

    if (value->found == 0u || value->size == 0u) {
        return fallback;
    }

    for (i = 0; i < value->size; ++i) {
        if (value->value[i] < '0' || value->value[i] > '9') {
            return fallback;
        }
        parsed = (parsed * 10u) + (size_t)(value->value[i] - '0');
    }

    return parsed == 0u ? fallback : parsed;
}

static void copy_config_value_string(const orca_config_value_view* value, char* buffer, size_t buffer_size, const char** out_string, const char* fallback) {
    size_t i = 0;

    if (value->found == 0u || value->size == 0u || buffer_size == 0u) {
        *out_string = fallback;
        return;
    }

    if (value->size >= buffer_size) {
        *out_string = fallback;
        return;
    }

    for (i = 0; i < value->size; ++i) {
        buffer[i] = (char)value->value[i];
    }
    buffer[value->size] = '\0';
    *out_string = buffer;
}

static orca_service_dependency_mask parse_service_mask_value(const orca_config_value_view* value, orca_service_dependency_mask fallback) {
    orca_service_dependency_mask mask = 0u;
    size_t offset = 0;

    if (value->found == 0u || value->size == 0u) {
        return fallback;
    }

    while (offset < value->size) {
        size_t token_start = offset;
        size_t token_end = offset;

        while (token_start < value->size && (value->value[token_start] == ' ' || value->value[token_start] == ',')) {
            ++token_start;
        }
        token_end = token_start;
        while (token_end < value->size && value->value[token_end] != ',') {
            ++token_end;
        }

        if (token_end > token_start) {
            size_t trimmed_end = token_end;
            while (trimmed_end > token_start && value->value[trimmed_end - 1u] == ' ') {
                --trimmed_end;
            }

            if (trimmed_end - token_start == 3u &&
                value->value[token_start] == 'n' && value->value[token_start + 1u] == 'e' && value->value[token_start + 2u] == 't') {
                mask |= ORCA_SERVICE_BIT(ORCA_SERVICE_NET);
            } else if (trimmed_end - token_start == 6u &&
                value->value[token_start] == 'v' && value->value[token_start + 1u] == 'i' && value->value[token_start + 2u] == 's' &&
                value->value[token_start + 3u] == 'i' && value->value[token_start + 4u] == 'o' && value->value[token_start + 5u] == 'n') {
                mask |= ORCA_SERVICE_BIT(ORCA_SERVICE_VISION);
            } else if (trimmed_end - token_start == 4u &&
                value->value[token_start] == 'c' && value->value[token_start + 1u] == 'o' && value->value[token_start + 2u] == 'r' && value->value[token_start + 3u] == 'e') {
                mask |= ORCA_SERVICE_BIT(ORCA_SERVICE_CORE);
            } else if (trimmed_end - token_start == 8u &&
                value->value[token_start] == 's' && value->value[token_start + 1u] == 'e' && value->value[token_start + 2u] == 'c' &&
                value->value[token_start + 3u] == 'u' && value->value[token_start + 4u] == 'r' && value->value[token_start + 5u] == 'i' &&
                value->value[token_start + 6u] == 't' && value->value[token_start + 7u] == 'y') {
                mask |= ORCA_SERVICE_BIT(ORCA_SERVICE_SECURITY);
            } else if (trimmed_end - token_start == 6u &&
                value->value[token_start] == 'u' && value->value[token_start + 1u] == 'p' && value->value[token_start + 2u] == 'd' &&
                value->value[token_start + 3u] == 'a' && value->value[token_start + 4u] == 't' && value->value[token_start + 5u] == 'e') {
                mask |= ORCA_SERVICE_BIT(ORCA_SERVICE_UPDATE);
            }
        }

        offset = token_end + 1u;
    }

    return mask == 0u ? fallback : mask;
}

static void set_default_enabled_services(void) {
    ORCA_INIT_BOOT_POLICY.enabled_service_mask =
        ORCA_SERVICE_BIT(ORCA_SERVICE_NET) |
        ORCA_SERVICE_BIT(ORCA_SERVICE_VISION) |
        ORCA_SERVICE_BIT(ORCA_SERVICE_CORE) |
        ORCA_SERVICE_BIT(ORCA_SERVICE_SECURITY) |
        ORCA_SERVICE_BIT(ORCA_SERVICE_UPDATE);
}

static void set_default_service_order(void) {
    ORCA_INIT_BOOT_POLICY.preferred_order[0] = ORCA_SERVICE_NET;
    ORCA_INIT_BOOT_POLICY.preferred_order[1] = ORCA_SERVICE_VISION;
    ORCA_INIT_BOOT_POLICY.preferred_order[2] = ORCA_SERVICE_CORE;
    ORCA_INIT_BOOT_POLICY.preferred_order[3] = ORCA_SERVICE_SECURITY;
    ORCA_INIT_BOOT_POLICY.preferred_order[4] = ORCA_SERVICE_UPDATE;
    ORCA_INIT_BOOT_POLICY.preferred_order_count = sizeof(SYSTEM_SERVICES) / sizeof(SYSTEM_SERVICES[0]);
}

static void set_service_order_for_target(const char* target) {
    set_default_service_order();
    set_default_enabled_services();

    if (string_equals(target, "orca-security.target")) {
        ORCA_INIT_BOOT_POLICY.enabled_service_mask =
            ORCA_SERVICE_BIT(ORCA_SERVICE_NET) |
            ORCA_SERVICE_BIT(ORCA_SERVICE_SECURITY) |
            ORCA_SERVICE_BIT(ORCA_SERVICE_CORE);
        ORCA_INIT_BOOT_POLICY.preferred_order[0] = ORCA_SERVICE_NET;
        ORCA_INIT_BOOT_POLICY.preferred_order[1] = ORCA_SERVICE_SECURITY;
        ORCA_INIT_BOOT_POLICY.preferred_order[2] = ORCA_SERVICE_VISION;
        ORCA_INIT_BOOT_POLICY.preferred_order[3] = ORCA_SERVICE_CORE;
        ORCA_INIT_BOOT_POLICY.preferred_order[4] = ORCA_SERVICE_UPDATE;
    } else if (string_equals(target, "orca-update.target")) {
        ORCA_INIT_BOOT_POLICY.enabled_service_mask =
            ORCA_SERVICE_BIT(ORCA_SERVICE_NET) |
            ORCA_SERVICE_BIT(ORCA_SERVICE_SECURITY) |
            ORCA_SERVICE_BIT(ORCA_SERVICE_UPDATE);
        ORCA_INIT_BOOT_POLICY.preferred_order[0] = ORCA_SERVICE_NET;
        ORCA_INIT_BOOT_POLICY.preferred_order[1] = ORCA_SERVICE_SECURITY;
        ORCA_INIT_BOOT_POLICY.preferred_order[2] = ORCA_SERVICE_UPDATE;
        ORCA_INIT_BOOT_POLICY.preferred_order[3] = ORCA_SERVICE_VISION;
        ORCA_INIT_BOOT_POLICY.preferred_order[4] = ORCA_SERVICE_CORE;
    } else if (string_equals(target, "orca-vision.target")) {
        ORCA_INIT_BOOT_POLICY.enabled_service_mask =
            ORCA_SERVICE_BIT(ORCA_SERVICE_NET) |
            ORCA_SERVICE_BIT(ORCA_SERVICE_VISION) |
            ORCA_SERVICE_BIT(ORCA_SERVICE_CORE);
        ORCA_INIT_BOOT_POLICY.preferred_order[0] = ORCA_SERVICE_VISION;
        ORCA_INIT_BOOT_POLICY.preferred_order[1] = ORCA_SERVICE_NET;
        ORCA_INIT_BOOT_POLICY.preferred_order[2] = ORCA_SERVICE_CORE;
        ORCA_INIT_BOOT_POLICY.preferred_order[3] = ORCA_SERVICE_SECURITY;
        ORCA_INIT_BOOT_POLICY.preferred_order[4] = ORCA_SERVICE_UPDATE;
    } else if (string_equals(target, "orca-net.target")) {
        ORCA_INIT_BOOT_POLICY.enabled_service_mask =
            ORCA_SERVICE_BIT(ORCA_SERVICE_NET) |
            ORCA_SERVICE_BIT(ORCA_SERVICE_SECURITY);
        ORCA_INIT_BOOT_POLICY.preferred_order[0] = ORCA_SERVICE_NET;
        ORCA_INIT_BOOT_POLICY.preferred_order[1] = ORCA_SERVICE_SECURITY;
        ORCA_INIT_BOOT_POLICY.preferred_order[2] = ORCA_SERVICE_UPDATE;
        ORCA_INIT_BOOT_POLICY.preferred_order[3] = ORCA_SERVICE_VISION;
        ORCA_INIT_BOOT_POLICY.preferred_order[4] = ORCA_SERVICE_CORE;
    }
}

static void initialize_boot_policy(void) {
    orca_config_value_view value;
    static char target_buffer[32];

    if (orca_init_boot_policy_initialized != 0) {
        return;
    }

    ORCA_INIT_BOOT_POLICY.default_target = "orca-core.target";
    ORCA_INIT_BOOT_POLICY.max_boot_passes = ORCA_MAX_BOOT_PASSES;
    ORCA_INIT_BOOT_POLICY.retry_deferred_services = 1u;
    set_service_order_for_target(ORCA_INIT_BOOT_POLICY.default_target);

    if (orca_handoff_lookup_config_value(ORCA_HANDOFF_FILE_SYSTEM_INIT_PROFILE, "default_target", &value) != 0) {
        copy_config_value_string(&value, target_buffer, sizeof(target_buffer), &ORCA_INIT_BOOT_POLICY.default_target, "orca-core.target");
        set_service_order_for_target(ORCA_INIT_BOOT_POLICY.default_target);
    }

    if (orca_handoff_lookup_config_value(ORCA_HANDOFF_FILE_SYSTEM_INIT_PROFILE, "retry_deferred_services", &value) != 0) {
        if (config_value_equals(&value, "true")) {
            ORCA_INIT_BOOT_POLICY.retry_deferred_services = 1u;
        } else {
            ORCA_INIT_BOOT_POLICY.retry_deferred_services = 0u;
        }
    }

    if (orca_handoff_lookup_config_value(ORCA_HANDOFF_FILE_SYSTEM_INIT_PROFILE, "service_graph_retries", &value) != 0) {
        ORCA_INIT_BOOT_POLICY.max_boot_passes = parse_unsigned_decimal_value(&value, ORCA_MAX_BOOT_PASSES);
    }

    if (ORCA_INIT_BOOT_POLICY.retry_deferred_services == 0u) {
        ORCA_INIT_BOOT_POLICY.max_boot_passes = 1u;
    }

    if (orca_handoff_lookup_config_value(ORCA_HANDOFF_FILE_SYSTEM_INIT_PROFILE, "enabled_services", &value) != 0) {
        ORCA_INIT_BOOT_POLICY.enabled_service_mask = parse_service_mask_value(&value, ORCA_INIT_BOOT_POLICY.enabled_service_mask);
    }

    orca_init_boot_policy_initialized = 1;
}

static const orca_service_descriptor* lookup_service_descriptor(orca_service_id id) {
    size_t i = 0;

    for (i = 0; i < sizeof(SYSTEM_SERVICES) / sizeof(SYSTEM_SERVICES[0]); ++i) {
        if (SYSTEM_SERVICES[i]->id == id) {
            return SYSTEM_SERVICES[i];
        }
    }

    return 0;
}

static size_t build_service_order(const orca_init_boot_policy* policy, const orca_service_descriptor** ordered_services, size_t capacity) {
    size_t count = 0;
    size_t i = 0;
    size_t j = 0;

    for (i = 0; i < policy->preferred_order_count && count < capacity; ++i) {
        const orca_service_descriptor* descriptor = lookup_service_descriptor(policy->preferred_order[i]);
        int already_present = 0;

        if (descriptor == 0 || (policy->enabled_service_mask & ORCA_SERVICE_BIT(policy->preferred_order[i])) == 0u) {
            continue;
        }

        for (j = 0; j < count; ++j) {
            if (ordered_services[j] == descriptor) {
                already_present = 1;
                break;
            }
        }

        if (already_present == 0) {
            ordered_services[count++] = descriptor;
        }
    }

    for (i = 0; i < sizeof(SYSTEM_SERVICES) / sizeof(SYSTEM_SERVICES[0]) && count < capacity; ++i) {
        int already_present = 0;

        for (j = 0; j < count; ++j) {
            if (ordered_services[j] == SYSTEM_SERVICES[i]) {
                already_present = 1;
                break;
            }
        }

        if (already_present == 0 && (policy->enabled_service_mask & ORCA_SERVICE_BIT(SYSTEM_SERVICES[i]->id)) != 0u) {
            ordered_services[count++] = SYSTEM_SERVICES[i];
        }
    }

    return count;
}

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

const orca_init_boot_policy* orca_get_init_boot_policy(void) {
    initialize_boot_policy();
    return &ORCA_INIT_BOOT_POLICY;
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
    const orca_init_boot_policy* policy = orca_get_init_boot_policy();
    const orca_service_descriptor* ordered_services[sizeof(SYSTEM_SERVICES) / sizeof(SYSTEM_SERVICES[0])];
    size_t ordered_count = 0;
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

    ordered_count = build_service_order(policy, ordered_services, count);

    for (i = 0; i < ordered_count; ++i) {
        records[i].service = ordered_services[i];
        records[i].status = ORCA_SERVICE_DEFERRED;
        records[i].missing_capabilities = ordered_services[i]->required_capabilities;
        records[i].waiting_on_services = ordered_services[i]->dependency_mask;
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

        for (pass = 0; pass < policy->max_boot_passes; ++pass) {
            int pass_progressed = 0;

            for (i = 0; i < ordered_count; ++i) {
                if (records[i].status == ORCA_SERVICE_READY) {
                    continue;
                }

                ++records[i].attempts;
                records[i].missing_capabilities =
                    records[i].service->required_capabilities & ~capabilities;
                records[i].waiting_on_services =
                    records[i].service->dependency_mask & ~started_services;
                records[i].resolved_phase = phases[phase_index];

                if (records[i].missing_capabilities != 0 || records[i].waiting_on_services != 0) {
                    records[i].status = ORCA_SERVICE_DEFERRED;
                    continue;
                }

                records[i].status = records[i].service->start();
                if (records[i].status == ORCA_SERVICE_READY) {
                    started_services |= ORCA_SERVICE_BIT(records[i].service->id);
                    pass_progressed = 1;
                    progressed = 1;
                }
            }

            if (pass_progressed == 0) {
                break;
            }
        }

        for (i = 0; i < ordered_count; ++i) {
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

        if (deferred_count == 0 || progressed == 0 || policy->retry_deferred_services == 0u) {
            continue;
        }
    }

    if (phase_count != 0) {
        *phase_count = local_phase_count;
    }

    return ordered_count;
}