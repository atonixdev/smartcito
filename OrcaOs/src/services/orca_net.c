#include "services/orca_net.h"

#include "orca_handoff.h"

static orca_net_runtime_policy ORCA_NET_RUNTIME_POLICY = {
    "unconfigured",
    "/run/orca/sockets/orca-net.sock",
    0u,
    0u,
    0u,
    0u,
};

static size_t string_length(const char* value) {
    size_t length = 0;

    while (value[length] != '\0') {
        ++length;
    }

    return length;
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

static void copy_config_string(const orca_config_value_view* value, char* buffer, size_t buffer_size, const char** out_value, const char* fallback) {
    size_t i = 0;

    if (value->found == 0u || value->size == 0u || value->size >= buffer_size) {
        *out_value = fallback;
        return;
    }

    for (i = 0; i < value->size; ++i) {
        buffer[i] = (char)value->value[i];
    }
    buffer[value->size] = '\0';
    *out_value = buffer;
}

static void load_orca_net_runtime_policy(void) {
    static char mode_buffer[24];
    static char socket_buffer[64];
    orca_config_value_view value;

    ORCA_NET_RUNTIME_POLICY.mode = "unconfigured";
    ORCA_NET_RUNTIME_POLICY.control_socket = "/run/orca/sockets/orca-net.sock";
    ORCA_NET_RUNTIME_POLICY.mesh_enabled = 0u;
    ORCA_NET_RUNTIME_POLICY.satellite_enabled = 0u;
    ORCA_NET_RUNTIME_POLICY.vpn_enabled = 0u;
    ORCA_NET_RUNTIME_POLICY.config_loaded = 0u;

    if (orca_handoff_lookup_config_value(ORCA_HANDOFF_FILE_NET_CONFIG, "mode", &value) != 0) {
        copy_config_string(&value, mode_buffer, sizeof(mode_buffer), &ORCA_NET_RUNTIME_POLICY.mode, "unconfigured");
        ORCA_NET_RUNTIME_POLICY.config_loaded = 1u;
    }
    if (orca_handoff_lookup_config_value(ORCA_HANDOFF_FILE_NET_CONFIG, "control_socket", &value) != 0) {
        copy_config_string(&value, socket_buffer, sizeof(socket_buffer), &ORCA_NET_RUNTIME_POLICY.control_socket, "/run/orca/sockets/orca-net.sock");
    }
    if (orca_handoff_lookup_config_value(ORCA_HANDOFF_FILE_NET_CONFIG, "mesh_enabled", &value) != 0) {
        ORCA_NET_RUNTIME_POLICY.mesh_enabled = config_value_equals(&value, "true") ? 1u : 0u;
    }
    if (orca_handoff_lookup_config_value(ORCA_HANDOFF_FILE_NET_CONFIG, "satellite_enabled", &value) != 0) {
        ORCA_NET_RUNTIME_POLICY.satellite_enabled = config_value_equals(&value, "true") ? 1u : 0u;
    }
    if (orca_handoff_lookup_config_value(ORCA_HANDOFF_FILE_NET_CONFIG, "vpn_enabled", &value) != 0) {
        ORCA_NET_RUNTIME_POLICY.vpn_enabled = config_value_equals(&value, "true") ? 1u : 0u;
    }
}

static orca_service_boot_status orca_net_start(void) {
    load_orca_net_runtime_policy();

    if (ORCA_NET_RUNTIME_POLICY.config_loaded == 0u) {
        return ORCA_SERVICE_BLOCKED;
    }

    if (ORCA_NET_RUNTIME_POLICY.mesh_enabled == 0u &&
        ORCA_NET_RUNTIME_POLICY.satellite_enabled == 0u &&
        ORCA_NET_RUNTIME_POLICY.vpn_enabled == 0u) {
        return ORCA_SERVICE_BLOCKED;
    }

    return ORCA_SERVICE_READY;
}

const orca_net_runtime_policy* orca_net_get_runtime_policy(void) {
    return &ORCA_NET_RUNTIME_POLICY;
}

const orca_service_descriptor ORCA_NET_SERVICE = {
    ORCA_SERVICE_NET,
    {"ORCA-Net", "Policy-aware networking and secure transport"},
    "bootstrap-network",
    ORCA_DRIVER_CAPABILITY_NETWORK,
    0,
    orca_net_start,
};