#include "orca_platform.h"

#include "orca_init.h"

static const orca_component_descriptor BASE_OS_COMPONENTS[] = {
    {"ORCA-BOOT", "GRUB-compatible boot path and early entry"},
    {"Kernel", "Freestanding core, memory, interrupts, scheduler"},
    {"Drivers", "Network, storage, sensor, and accelerator interfaces"},
    {"Init", "Minimal service bootstrap and health supervision"},
};

static const orca_component_descriptor WORKLOAD_COMPONENTS[] = {
    {"Control Plane", "Operator APIs, dashboards, and fleet commands"},
    {"Mission Apps", "Autonomy, telemetry, and edge workflows"},
    {"Observability", "Metrics, traces, and incident response hooks"},
};

static orca_layer_descriptor ORCA_PLATFORM_LAYERS[] = {
    {
        "Layer 1 - Base OS",
        "Kernel, boot, drivers, and init kept minimal and stable",
        BASE_OS_COMPONENTS,
        sizeof(BASE_OS_COMPONENTS) / sizeof(BASE_OS_COMPONENTS[0]),
    },
    {
        "Layer 2 - ORCA System Services",
        "Platform-native services that define ORCA behavior",
        0,
        0,
    },
    {
        "Layer 3 - Workloads and Control Plane",
        "Mission workloads and operator-facing system surfaces",
        WORKLOAD_COMPONENTS,
        sizeof(WORKLOAD_COMPONENTS) / sizeof(WORKLOAD_COMPONENTS[0]),
    },
};

const orca_layer_descriptor* orca_get_platform_layers(size_t* layer_count) {
    ORCA_PLATFORM_LAYERS[1].components = orca_get_system_service_components(
        &ORCA_PLATFORM_LAYERS[1].component_count
    );
    if (layer_count != 0) {
        *layer_count = sizeof(ORCA_PLATFORM_LAYERS) / sizeof(ORCA_PLATFORM_LAYERS[0]);
    }
    return ORCA_PLATFORM_LAYERS;
}