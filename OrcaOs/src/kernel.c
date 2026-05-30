#include <stdint.h>
#include <stddef.h>

#include "orca_drivers.h"
#include "orca_init.h"
#include "orca_platform.h"

static volatile uint16_t* const VGA_BUFFER = (uint16_t*)0xB8000;
static const size_t VGA_WIDTH = 80;
static const size_t VGA_HEIGHT = 25;

static inline uint16_t vga_entry(unsigned char c, uint8_t color) {
    return (uint16_t)c | (uint16_t)color << 8;
}

static void clear_screen(uint8_t color) {
    for (size_t y = 0; y < VGA_HEIGHT; ++y) {
        for (size_t x = 0; x < VGA_WIDTH; ++x) {
            VGA_BUFFER[y * VGA_WIDTH + x] = vga_entry(' ', color);
        }
    }
}

static void write_string_at(const char* s, size_t row, size_t col, uint8_t color) {
    size_t i = 0;
    while (s[i] != '\0' && col + i < VGA_WIDTH) {
        VGA_BUFFER[row * VGA_WIDTH + col + i] = vga_entry((unsigned char)s[i], color);
        ++i;
    }
}

static void append_token(char* buffer, size_t buffer_size, const char* token) {
    size_t length = 0;
    size_t i = 0;

    while (length < buffer_size && buffer[length] != '\0') {
        ++length;
    }
    if (length >= buffer_size) {
        return;
    }

    if (length > 0 && length + 1 < buffer_size) {
        buffer[length++] = '+';
        buffer[length] = '\0';
    }

    while (token[i] != '\0' && length + 1 < buffer_size) {
        buffer[length++] = token[i++];
    }
    buffer[length] = '\0';
}

static void mask_to_capability_tokens(orca_driver_capability_mask mask, char* buffer, size_t buffer_size) {
    const orca_driver_capability capabilities[] = {
        ORCA_DRIVER_CAPABILITY_NETWORK,
        ORCA_DRIVER_CAPABILITY_STORAGE,
        ORCA_DRIVER_CAPABILITY_SENSORS,
        ORCA_DRIVER_CAPABILITY_CRYPTO,
        ORCA_DRIVER_CAPABILITY_DISPLAY,
    };
    size_t i = 0;

    if (buffer_size == 0) {
        return;
    }

    buffer[0] = '\0';
    if (mask == 0) {
        append_token(buffer, buffer_size, "none");
        return;
    }

    for (i = 0; i < sizeof(capabilities) / sizeof(capabilities[0]); ++i) {
        if ((mask & capabilities[i]) != 0) {
            append_token(buffer, buffer_size, orca_driver_capability_token(capabilities[i]));
        }
    }
}

static void mask_to_dependency_tokens(
    orca_service_dependency_mask mask,
    char* buffer,
    size_t buffer_size
) {
    const orca_service_id services[] = {
        ORCA_SERVICE_NET,
        ORCA_SERVICE_VISION,
        ORCA_SERVICE_CORE,
        ORCA_SERVICE_SECURITY,
        ORCA_SERVICE_UPDATE,
    };
    size_t i = 0;

    if (buffer_size == 0) {
        return;
    }

    buffer[0] = '\0';
    if (mask == 0) {
        append_token(buffer, buffer_size, "none");
        return;
    }

    for (i = 0; i < sizeof(services) / sizeof(services[0]); ++i) {
        if ((mask & ORCA_SERVICE_BIT(services[i])) != 0) {
            append_token(buffer, buffer_size, orca_service_token(services[i]));
        }
    }
}

static void write_layer_row(const orca_layer_descriptor* layer, size_t row, uint8_t color) {
    write_string_at(layer->name, row, 2, color);
    if (layer->component_count > 0) {
        write_string_at(layer->components[0].name, row, 34, color);
    }
}

static const char* service_status_text(orca_service_boot_status status) {
    switch (status) {
        case ORCA_SERVICE_READY:
            return "ready";
        case ORCA_SERVICE_DEFERRED:
            return "deferred";
        case ORCA_SERVICE_BLOCKED:
            return "blocked";
        default:
            return "unknown";
    }
}

static void write_driver_row(const orca_driver_descriptor* driver, size_t row) {
    write_string_at(driver->name, row, 4, 0x1E);
    write_string_at(orca_driver_capability_token(driver->capability), row, 14, 0x1F);
    write_string_at(orca_boot_phase_token(driver->ready_phase), row, 18, 0x1F);
    write_string_at(driver->ready != 0 ? "ready" : "wait", row, 22, 0x1A);
    write_string_at(driver->summary, row, 30, 0x1F);
}

static void write_service_row(const orca_service_boot_record* record, size_t row) {
    char capability_tokens[16];
    char dependency_tokens[16];

    mask_to_capability_tokens(record->service->required_capabilities, capability_tokens, sizeof(capability_tokens));
    mask_to_dependency_tokens(record->service->dependency_mask, dependency_tokens, sizeof(dependency_tokens));

    write_string_at(record->service->component.name, row, 2, 0x1E);
    write_string_at(record->service->boot_stage, row, 16, 0x1F);
    write_string_at(capability_tokens, row, 36, 0x1F);
    write_string_at(dependency_tokens, row, 48, 0x1F);
    write_string_at(orca_boot_phase_token(record->resolved_phase), row, 58, 0x1F);
    write_string_at(service_status_text(record->status), row, 66, 0x1A);
}

static void write_service_note_row(const orca_service_boot_record* record, size_t row) {
    char capability_tokens[16];
    char dependency_tokens[16];

    if (record->status == ORCA_SERVICE_READY) {
        write_string_at("ok", row, 4, 0x1A);
        return;
    }

    mask_to_capability_tokens(record->missing_capabilities, capability_tokens, sizeof(capability_tokens));
    mask_to_dependency_tokens(record->waiting_on_services, dependency_tokens, sizeof(dependency_tokens));

    write_string_at("wait", row, 4, 0x4E);
    write_string_at("drv:", row, 10, 0x1F);
    write_string_at(capability_tokens, row, 15, 0x1F);
    write_string_at("svc:", row, 28, 0x1F);
    write_string_at(dependency_tokens, row, 33, 0x1F);
    write_string_at("try:", row, 48, 0x1F);
    if (record->attempts > 9) {
        write_string_at("9+", row, 53, 0x1F);
    } else {
        char attempt[2];
        attempt[0] = (char)('0' + record->attempts);
        attempt[1] = '\0';
        write_string_at(attempt, row, 53, 0x1F);
    }
}

static void write_phase_row(const orca_boot_phase_record* record, size_t row) {
    char ready[2];
    char deferred[2];

    ready[0] = (char)('0' + (record->services_ready > 9 ? 9 : record->services_ready));
    ready[1] = '\0';
    deferred[0] = (char)('0' + (record->services_deferred > 9 ? 9 : record->services_deferred));
    deferred[1] = '\0';

    write_string_at(orca_boot_phase_token(record->phase), row, 4, 0x1E);
    write_string_at("ready", row, 16, 0x1F);
    write_string_at(ready, row, 22, 0x1A);
    write_string_at("deferred", row, 28, 0x1F);
    write_string_at(deferred, row, 37, 0x4E);
}

void kernel_main(uint32_t multiboot_magic, uint32_t multiboot_info_ptr) {
    (void)multiboot_info_ptr;
    size_t driver_count = 0;
    size_t layer_count = 0;
    size_t booted_services = 0;
    size_t phase_count = 0;
    const orca_driver_descriptor* drivers = orca_get_registered_drivers(&driver_count);
    const orca_layer_descriptor* layers = orca_get_platform_layers(&layer_count);
    orca_service_boot_record service_records[ORCA_MAX_SYSTEM_SERVICES];
    orca_boot_phase_record phase_records[ORCA_BOOT_PHASE_COMPLETE];

    clear_screen(0x1F);
    write_string_at("ORCA OS Boot Checkpoint", 1, 2, 0x1F);

    if (multiboot_magic == 0x2BADB002) {
        write_string_at("Multiboot magic validated.", 3, 2, 0x1A);
    } else {
        write_string_at("Multiboot magic invalid.", 3, 2, 0x4F);
    }

    write_string_at("3-layer ORCA OS scaffold loaded:", 5, 2, 0x1E);

    if (layer_count > 0) {
        write_layer_row(&layers[0], 6, 0x1E);
    }
    if (layer_count > 1) {
        write_layer_row(&layers[1], 7, 0x1E);
    }
    if (layer_count > 2) {
        write_layer_row(&layers[2], 8, 0x1E);
    }

    write_string_at("Layer 1 driver registry:", 10, 2, 0x1E);
    for (size_t i = 0; i < driver_count && 11 + i < VGA_HEIGHT; ++i) {
        write_driver_row(&drivers[i], 11 + i);
    }

    booted_services = orca_boot_system_services(
        service_records,
        ORCA_MAX_SYSTEM_SERVICES,
        phase_records,
        ORCA_BOOT_PHASE_COMPLETE,
        &phase_count
    );

    write_string_at("Boot phases:", 16, 2, 0x1E);
    for (size_t i = 0; i < phase_count && 17 + i < VGA_HEIGHT; ++i) {
        write_phase_row(&phase_records[i], 17 + i);
    }

    write_string_at("Layer 2 service table:", 16, 44, 0x1E);
    write_string_at("svc           stage       drv         dep       ph   status", 17, 20, 0x1F);
    for (size_t i = 0; i < booted_services && 18 + i < VGA_HEIGHT; ++i) {
        write_service_row(&service_records[i], 18 + i);
    }

    if (booted_services > 0 && 18 + booted_services < VGA_HEIGHT) {
        write_service_note_row(&service_records[booted_services - 1], 18 + booted_services);
    }

    write_string_at("Next: interrupts, memory, scheduler, user-mode runtime.", 24, 2, 0x1E);

    for (;;) {
        __asm__ __volatile__("hlt");
    }
}
